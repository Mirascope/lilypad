import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock modules before imports
vi.mock('@opentelemetry/api', () => ({
  trace: {
    getTracer: vi.fn(),
    setSpan: vi.fn(),
  },
  context: {
    active: vi.fn(),
    with: vi.fn(),
  },
  SpanKind: {
    CLIENT: 2,
  },
  SpanStatusCode: {
    OK: 1,
    ERROR: 2,
  },
}));

vi.mock('./utils/logger', () => ({
  logger: {
    debug: vi.fn(),
  },
}));

vi.mock('./utils/stream-wrapper', () => ({
  isAsyncIterable: vi.fn(),
}));

vi.mock('./utils/error-handler', () => ({
  ensureError: vi.fn(),
}));

// Import after mocking
import { wrapOpenAI } from './wrap-openai';
import { trace, context, SpanKind, SpanStatusCode } from '@opentelemetry/api';
import { logger } from './utils/logger';
import { isAsyncIterable } from './utils/stream-wrapper';
import { ensureError } from './utils/error-handler';

// Get mocked functions
const mockedTrace = vi.mocked(trace);
const mockedContext = vi.mocked(context);
const mockedLogger = vi.mocked(logger);
const mockedIsAsyncIterable = vi.mocked(isAsyncIterable);
const mockedEnsureError = vi.mocked(ensureError);

describe('wrapOpenAI', () => {
  let mockSpan: any;
  let mockTracer: any;
  let mockOriginalCreate: any;
  let OpenAIClass: any;

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock span
    mockSpan = {
      setAttribute: vi.fn(),
      setAttributes: vi.fn(),
      addEvent: vi.fn(),
      setStatus: vi.fn(),
      recordException: vi.fn(),
      end: vi.fn(),
    };

    // Mock tracer
    mockTracer = {
      startSpan: vi.fn().mockReturnValue(mockSpan),
    };

    // Set up mock implementations
    mockedTrace.getTracer.mockReturnValue(mockTracer);
    mockedTrace.setSpan.mockImplementation((ctx, span) => ({ ...ctx, span }));
    mockedContext.active.mockReturnValue({});
    mockedContext.with.mockImplementation((ctx, fn) => fn());
    mockedIsAsyncIterable.mockImplementation((value) => {
      return value != null && typeof value === 'object' && Symbol.asyncIterator in value;
    });
    mockedEnsureError.mockImplementation((error) => {
      if (error instanceof Error) return error;
      return new Error(String(error));
    });

    // Mock original create method
    mockOriginalCreate = vi.fn();

    // Create base OpenAI class
    OpenAIClass = class {
      chat = {
        completions: {
          create: mockOriginalCreate,
        },
      };
    };
  });

  describe('class wrapping', () => {
    it('should create a wrapped class that extends the original', () => {
      const WrappedOpenAI = wrapOpenAI(OpenAIClass);
      const instance = new WrappedOpenAI();

      expect(instance).toBeInstanceOf(OpenAIClass);
      expect(instance.chat.completions.create).toBeDefined();
      expect(instance.chat.completions.create).not.toBe(mockOriginalCreate);
    });

    it('should log debug message when wrapping', () => {
      wrapOpenAI(OpenAIClass);

      expect(mockedLogger.debug).toHaveBeenCalledWith('[wrapOpenAI] Wrapping OpenAI instance');
    });

    it('should handle missing chat.completions.create gracefully', () => {
      const EmptyClass = class {};
      const WrappedClass = wrapOpenAI(EmptyClass);
      const instance = new WrappedClass();

      expect(instance).toBeInstanceOf(EmptyClass);
    });
  });

  describe('chat.completions.create wrapping', () => {
    it('should create a span with correct attributes', async () => {
      const WrappedOpenAI = wrapOpenAI(OpenAIClass);
      const instance = new WrappedOpenAI();

      const params = {
        model: 'gpt-4',
        messages: [{ role: 'user', content: 'Hello' }],
        temperature: 0.7,
        max_tokens: 100,
        top_p: 0.9,
      };

      mockOriginalCreate.mockResolvedValue({ choices: [] });

      await instance.chat.completions.create(params);

      expect(mockTracer.startSpan).toHaveBeenCalledWith('chat gpt-4', {
        kind: SpanKind.CLIENT,
        attributes: {
          'gen_ai.system': 'openai',
          'server.address': 'api.openai.com',
          'gen_ai.request.model': 'gpt-4',
          'gen_ai.request.temperature': 0.7,
          'gen_ai.request.max_tokens': 100,
          'gen_ai.request.top_p': 0.9,
          'gen_ai.operation.name': 'chat',
        },
      });
    });

    it('should record message events', async () => {
      const WrappedOpenAI = wrapOpenAI(OpenAIClass);
      const instance = new WrappedOpenAI();

      const params = {
        model: 'gpt-4',
        messages: [
          { role: 'system', content: 'You are helpful' },
          { role: 'user', content: 'Hello' },
        ],
      };

      mockOriginalCreate.mockResolvedValue({ choices: [] });

      await instance.chat.completions.create(params);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.system.message', {
        'gen_ai.system': 'openai',
        content: 'You are helpful',
      });
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.user.message', {
        'gen_ai.system': 'openai',
        content: 'Hello',
      });
    });

    it('should handle complex message content', async () => {
      const WrappedOpenAI = wrapOpenAI(OpenAIClass);
      const instance = new WrappedOpenAI();

      const params = {
        model: 'gpt-4',
        messages: [{ role: 'user', content: { type: 'text', text: 'Hello' } }],
      };

      mockOriginalCreate.mockResolvedValue({ choices: [] });

      await instance.chat.completions.create(params);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.user.message', {
        'gen_ai.system': 'openai',
        content: JSON.stringify({ type: 'text', text: 'Hello' }),
      });
    });

    it('should record response data', async () => {
      const WrappedOpenAI = wrapOpenAI(OpenAIClass);
      const instance = new WrappedOpenAI();

      const response = {
        id: 'chatcmpl-123',
        model: 'gpt-4-0613',
        choices: [
          {
            message: { role: 'assistant', content: 'Hi there!' },
            finish_reason: 'stop',
          },
        ],
        usage: {
          prompt_tokens: 10,
          completion_tokens: 20,
          total_tokens: 30,
        },
      };

      mockOriginalCreate.mockResolvedValue(response);

      await instance.chat.completions.create({ model: 'gpt-4' });

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'openai',
        index: 0,
        finish_reason: 'stop',
        message: JSON.stringify({ role: 'assistant', content: 'Hi there!' }),
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.finish_reasons', [
        'stop',
      ]);

      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.usage.input_tokens': 10,
        'gen_ai.usage.output_tokens': 20,
        'gen_ai.usage.total_tokens': 30,
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.model', 'gpt-4-0613');
      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.id', 'chatcmpl-123');
    });

    it('should handle errors', async () => {
      const WrappedOpenAI = wrapOpenAI(OpenAIClass);
      const instance = new WrappedOpenAI();

      const error = new Error('API Error');
      mockOriginalCreate.mockRejectedValue(error);

      await expect(instance.chat.completions.create({ model: 'gpt-4' })).rejects.toThrow(
        'API Error',
      );

      expect(mockSpan.recordException).toHaveBeenCalledWith(error);
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'API Error',
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should handle streaming responses', async () => {
      const WrappedOpenAI = wrapOpenAI(OpenAIClass);
      const instance = new WrappedOpenAI();

      // Create a mock async iterable
      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield {
            choices: [{ delta: { content: 'Hello' } }],
          };
          yield {
            choices: [{ delta: { content: ' world' }, finish_reason: 'stop' }],
            usage: { prompt_tokens: 5, completion_tokens: 10, total_tokens: 15 },
          };
        },
      };

      mockOriginalCreate.mockResolvedValue(mockStream);
      mockedIsAsyncIterable.mockReturnValue(true);

      const result = await instance.chat.completions.create({ model: 'gpt-4', stream: true });

      // Consume the stream
      const chunks = [];
      for await (const chunk of result) {
        chunks.push(chunk);
      }

      expect(chunks).toHaveLength(2);
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'openai',
        index: 0,
        finish_reason: 'stop',
        message: JSON.stringify({ role: 'assistant', content: 'Hello world' }),
      });
      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.finish_reasons', [
        'stop',
      ]);
      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.usage.input_tokens': 5,
        'gen_ai.usage.output_tokens': 10,
        'gen_ai.usage.total_tokens': 15,
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should handle streaming errors', async () => {
      const WrappedOpenAI = wrapOpenAI(OpenAIClass);
      const instance = new WrappedOpenAI();

      const error = new Error('Stream error');
      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield { choices: [{ delta: { content: 'Hello' } }] };
          throw error;
        },
      };

      mockOriginalCreate.mockResolvedValue(mockStream);
      mockedIsAsyncIterable.mockReturnValue(true);

      const result = await instance.chat.completions.create({ model: 'gpt-4', stream: true });

      const chunks = [];
      await expect(async () => {
        for await (const chunk of result) {
          chunks.push(chunk);
        }
      }).rejects.toThrow('Stream error');

      expect(mockSpan.recordException).toHaveBeenCalledWith(error);
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'Stream error',
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should not end span for non-streaming responses in finally block', async () => {
      const WrappedOpenAI = wrapOpenAI(OpenAIClass);
      const instance = new WrappedOpenAI();

      mockOriginalCreate.mockResolvedValue({ choices: [] });

      await instance.chat.completions.create({ model: 'gpt-4', stream: false });

      // End should be called once after success
      expect(mockSpan.end).toHaveBeenCalledTimes(1);
    });

    it('should pass through all arguments to original method', async () => {
      const WrappedOpenAI = wrapOpenAI(OpenAIClass);
      const instance = new WrappedOpenAI();

      const params = { model: 'gpt-4' };
      const options = { signal: new AbortController().signal };

      mockOriginalCreate.mockResolvedValue({ choices: [] });

      await instance.chat.completions.create(params, options);

      expect(mockOriginalCreate).toHaveBeenCalledWith(params, options);
    });
  });

  describe('isCompletionResponse type guard', () => {
    it('should handle non-completion responses', async () => {
      const WrappedOpenAI = wrapOpenAI(OpenAIClass);
      const instance = new WrappedOpenAI();

      // Return something that doesn't match ChatCompletionResponse structure
      mockOriginalCreate.mockResolvedValue(null);

      await instance.chat.completions.create({ model: 'gpt-4' });

      // Should not try to record response
      expect(mockSpan.addEvent).not.toHaveBeenCalledWith('gen_ai.choice', expect.any(Object));
    });

    it('should handle response without choices array', async () => {
      const WrappedOpenAI = wrapOpenAI(OpenAIClass);
      const instance = new WrappedOpenAI();

      mockOriginalCreate.mockResolvedValue({ choices: null });

      await instance.chat.completions.create({ model: 'gpt-4' });

      expect(mockSpan.addEvent).not.toHaveBeenCalledWith('gen_ai.choice', expect.any(Object));
    });
  });

  describe('instance wrapping', () => {
    it('should wrap an existing OpenAI instance', () => {
      const instance = new OpenAIClass();
      const originalCreate = instance.chat.completions.create;

      const wrappedInstance = wrapOpenAI(instance);

      expect(wrappedInstance).toBe(instance); // Modified in-place
      expect(instance.chat.completions.create).not.toBe(originalCreate);
      expect(instance.chat.completions.create).toBeDefined();
    });

    it('should handle instance without chat property', () => {
      const instance = {};
      const wrappedInstance = wrapOpenAI(instance);

      expect(wrappedInstance).toBe(instance);
      // Should not throw
    });

    it('should handle instance without completions property', () => {
      const instance = { chat: {} };
      const wrappedInstance = wrapOpenAI(instance);

      expect(wrappedInstance).toBe(instance);
      // Should not throw
    });

    it('should handle instance without create method', () => {
      const instance = { chat: { completions: {} } };
      const wrappedInstance = wrapOpenAI(instance);

      expect(wrappedInstance).toBe(instance);
      // Should not throw
    });
  });

  describe('recordResponse helper', () => {
    it('should handle empty response', async () => {
      const WrappedOpenAI = wrapOpenAI(OpenAIClass);
      const instance = new WrappedOpenAI();

      mockOriginalCreate.mockResolvedValue({});

      await instance.chat.completions.create({ model: 'gpt-4' });

      // Should not throw, but also shouldn't record anything
      expect(mockSpan.addEvent).not.toHaveBeenCalledWith('gen_ai.choice', expect.any(Object));
    });

    it('should handle choices with missing message', async () => {
      const WrappedOpenAI = wrapOpenAI(OpenAIClass);
      const instance = new WrappedOpenAI();

      const response = {
        choices: [
          { finish_reason: 'stop' }, // No message property
        ],
      };

      mockOriginalCreate.mockResolvedValue(response);

      await instance.chat.completions.create({ model: 'gpt-4' });

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'openai',
        index: 0,
        finish_reason: 'stop',
        message: JSON.stringify({ role: 'assistant' }), // Default role, no content
      });
    });

    it('should handle choices with null finish_reason', async () => {
      const WrappedOpenAI = wrapOpenAI(OpenAIClass);
      const instance = new WrappedOpenAI();

      const response = {
        choices: [
          {
            message: { role: 'assistant', content: 'Hello' },
            finish_reason: null,
          },
        ],
      };

      mockOriginalCreate.mockResolvedValue(response);

      await instance.chat.completions.create({ model: 'gpt-4' });

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'openai',
        index: 0,
        finish_reason: 'error', // Default when null
        message: JSON.stringify({ role: 'assistant', content: 'Hello' }),
      });

      // Should not set finish_reasons attribute when all are null
      expect(mockSpan.setAttribute).not.toHaveBeenCalledWith(
        'gen_ai.response.finish_reasons',
        expect.any(Array),
      );
    });

    it('should record server.address attribute', async () => {
      const WrappedOpenAI = wrapOpenAI(OpenAIClass);
      const instance = new WrappedOpenAI();

      const response = {
        choices: [{ message: { content: 'test' } }],
      };

      mockOriginalCreate.mockResolvedValue(response);

      await instance.chat.completions.create({ model: 'gpt-4' });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('server.address', 'api.openai.com');
    });

    it('should filter out falsy finish reasons', async () => {
      const WrappedOpenAI = wrapOpenAI(OpenAIClass);
      const instance = new WrappedOpenAI();

      const response = {
        choices: [
          { finish_reason: 'stop' },
          { finish_reason: null },
          { finish_reason: '' },
          { finish_reason: 'length' },
        ],
      };

      mockOriginalCreate.mockResolvedValue(response);

      await instance.chat.completions.create({ model: 'gpt-4' });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.finish_reasons', [
        'stop',
        'length',
      ]);
    });
  });

  describe('wrapStream helper', () => {
    it('should handle stream with usage in chunks', async () => {
      const WrappedOpenAI = wrapOpenAI(OpenAIClass);
      const instance = new WrappedOpenAI();

      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield {
            choices: [{ delta: { content: 'Hello' } }],
            usage: { prompt_tokens: 5, completion_tokens: 5, total_tokens: 10 },
          };
          yield {
            choices: [{ delta: { content: ' world' }, finish_reason: 'stop' }],
            usage: { prompt_tokens: 5, completion_tokens: 10, total_tokens: 15 },
          };
        },
      };

      mockOriginalCreate.mockResolvedValue(mockStream);
      mockedIsAsyncIterable.mockReturnValue(true);

      const result = await instance.chat.completions.create({ model: 'gpt-4', stream: true });

      const chunks = [];
      for await (const chunk of result) {
        chunks.push(chunk);
      }

      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.usage.input_tokens': 5,
        'gen_ai.usage.output_tokens': 10,
        'gen_ai.usage.total_tokens': 15,
      });
    });

    it('should handle stream with non-string content', async () => {
      const WrappedOpenAI = wrapOpenAI(OpenAIClass);
      const instance = new WrappedOpenAI();

      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield {
            choices: [{ delta: { content: 123 } }], // Non-string content
          };
        },
      };

      mockOriginalCreate.mockResolvedValue(mockStream);
      mockedIsAsyncIterable.mockReturnValue(true);

      const result = await instance.chat.completions.create({ model: 'gpt-4', stream: true });

      const chunks = [];
      for await (const chunk of result) {
        chunks.push(chunk);
      }

      // Should handle non-string content gracefully
      expect(chunks).toHaveLength(1);
    });

    it('should handle stream with malformed chunks', async () => {
      const WrappedOpenAI = wrapOpenAI(OpenAIClass);
      const instance = new WrappedOpenAI();

      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield null;
          yield undefined;
          yield {};
          yield { choices: null };
          yield { choices: [] };
          yield { choices: [null] };
          yield { choices: [{ delta: { content: 'Valid' } }] };
        },
      };

      mockOriginalCreate.mockResolvedValue(mockStream);
      mockedIsAsyncIterable.mockReturnValue(true);

      const result = await instance.chat.completions.create({ model: 'gpt-4', stream: true });

      const chunks = [];
      for await (const chunk of result) {
        chunks.push(chunk);
      }

      expect(chunks).toHaveLength(7);
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'openai',
        index: 0,
        finish_reason: 'error',
        message: JSON.stringify({ role: 'assistant', content: 'Valid' }),
      });
    });

    it('should ensure error is Error instance', async () => {
      const WrappedOpenAI = wrapOpenAI(OpenAIClass);
      const instance = new WrappedOpenAI();

      const nonErrorValue = 'string error';
      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield { choices: [{ delta: { content: 'Hello' } }] };
          throw nonErrorValue;
        },
      };

      mockOriginalCreate.mockResolvedValue(mockStream);
      mockedIsAsyncIterable.mockReturnValue(true);

      const result = await instance.chat.completions.create({ model: 'gpt-4', stream: true });

      await expect(async () => {
        for await (const _chunk of result) {
          // Process chunk
        }
      }).rejects.toThrow('string error');

      expect(mockedEnsureError).toHaveBeenCalledWith(nonErrorValue);
      expect(mockSpan.recordException).toHaveBeenCalledWith(expect.any(Error));
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'string error',
      });
    });

    it('should set usage to default object if undefined', async () => {
      const WrappedOpenAI = wrapOpenAI(OpenAIClass);
      const instance = new WrappedOpenAI();

      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield { choices: [{ delta: { content: 'test' }, finish_reason: 'stop' }] };
        },
      };

      mockOriginalCreate.mockResolvedValue(mockStream);
      mockedIsAsyncIterable.mockReturnValue(true);

      const result = await instance.chat.completions.create({ model: 'gpt-4', stream: true });

      for await (const _chunk of result) {
        // Consume stream
      }

      // Should use default usage values
      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.usage.input_tokens': 0,
        'gen_ai.usage.output_tokens': 0,
        'gen_ai.usage.total_tokens': 0,
      });
    });
  });

  describe('error handling with ensureError', () => {
    it('should handle non-Error exceptions in non-streaming mode', async () => {
      const WrappedOpenAI = wrapOpenAI(OpenAIClass);
      const instance = new WrappedOpenAI();

      const nonErrorValue = { message: 'object error', code: 'ERR_001' };
      mockOriginalCreate.mockRejectedValue(nonErrorValue);

      await expect(instance.chat.completions.create({ model: 'gpt-4' })).rejects.toThrow();

      expect(mockedEnsureError).toHaveBeenCalledWith(nonErrorValue);
      expect(mockSpan.recordException).toHaveBeenCalledWith(expect.any(Error));
    });
  });
});
