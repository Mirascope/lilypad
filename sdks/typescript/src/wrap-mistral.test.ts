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

vi.mock('./utils/error-handler', () => ({
  ensureError: vi.fn(),
}));

// Import after mocking
import { wrapMistral } from './wrap-mistral';
import { trace, context, SpanKind, SpanStatusCode } from '@opentelemetry/api';
import { logger } from './utils/logger';
import { ensureError } from './utils/error-handler';

// Get mocked functions
const mockedTrace = vi.mocked(trace);
const mockedContext = vi.mocked(context);
const mockedLogger = vi.mocked(logger);
const mockedEnsureError = vi.mocked(ensureError);

describe('wrapMistral', () => {
  let mockSpan: any;
  let mockTracer: any;
  let mockChat: any;
  let mockChatStream: any;
  let MistralClass: any;

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
    mockedEnsureError.mockImplementation((error) => {
      if (error instanceof Error) return error;
      return new Error(String(error));
    });

    // Mock original methods
    mockChat = vi.fn();
    mockChatStream = vi.fn();

    // Create base Mistral class with new SDK structure
    MistralClass = class {
      chat = {
        complete: mockChat,
        stream: mockChatStream,
      };
    };
  });

  describe('class wrapping', () => {
    it('should create a wrapped class that extends the original', () => {
      const WrappedMistral = wrapMistral(MistralClass);
      const instance = new WrappedMistral();

      expect(instance).toBeInstanceOf(MistralClass);
      expect(instance.chat).toBeDefined();
      expect(instance.chat.complete).toBeDefined();
      expect(instance.chat.complete).not.toBe(mockChat);
      expect(instance.chat.stream).toBeDefined();
      expect(instance.chat.stream).not.toBe(mockChatStream);
    });

    it('should log debug message when wrapping', () => {
      wrapMistral(MistralClass);

      expect(mockedLogger.debug).toHaveBeenCalledWith('[wrapMistral] Wrapping Mistral instance');
    });

    it('should handle missing methods gracefully', () => {
      const EmptyClass = class {};
      const WrappedClass = wrapMistral(EmptyClass);
      const instance = new WrappedClass();

      expect(instance).toBeInstanceOf(EmptyClass);
    });
  });

  describe('chat wrapping', () => {
    it('should create a span with correct attributes', async () => {
      const WrappedMistral = wrapMistral(MistralClass);
      const instance = new WrappedMistral();

      const params = {
        model: 'mistral-medium',
        messages: [{ role: 'user', content: 'Hello Mistral!' }],
        temperature: 0.7,
        maxTokens: 100,
        top_p: 0.9,
        safe_prompt: true,
        random_seed: 42,
      };

      mockChat.mockResolvedValue({
        choices: [],
        usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 },
      });

      await instance.chat.complete(params);

      expect(mockTracer.startSpan).toHaveBeenCalledWith('chat mistral-medium', {
        kind: SpanKind.CLIENT,
        attributes: {
          'gen_ai.system': 'mistral',
          'server.address': 'api.mistral.ai',
          'gen_ai.request.model': 'mistral-medium',
          'gen_ai.request.temperature': 0.7,
          'gen_ai.request.max_tokens': 100,
          'gen_ai.request.top_p': 0.9,
          'gen_ai.operation.name': 'chat',
          'lilypad.type': 'llm',
          'gen_ai.request.safe_prompt': true,
          'gen_ai.request.random_seed': 42,
        },
      });
    });

    it('should record message events', async () => {
      const WrappedMistral = wrapMistral(MistralClass);
      const instance = new WrappedMistral();

      const params = {
        model: 'mistral-medium',
        messages: [
          { role: 'system', content: 'You are helpful' },
          { role: 'user', content: 'Hello' },
          { role: 'assistant', content: 'Hi there!' },
          { role: 'user', content: 'How are you?' },
        ],
      };

      mockChat.mockResolvedValue({ choices: [] });

      await instance.chat.complete(params);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.system.message', {
        'gen_ai.system': 'mistral',
        content: 'You are helpful',
      });
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.user.message', {
        'gen_ai.system': 'mistral',
        content: 'Hello',
      });
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.assistant.message', {
        'gen_ai.system': 'mistral',
        content: 'Hi there!',
      });
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.user.message', {
        'gen_ai.system': 'mistral',
        content: 'How are you?',
      });
    });

    it('should record response data', async () => {
      const WrappedMistral = wrapMistral(MistralClass);
      const instance = new WrappedMistral();

      const response = {
        id: 'cmpl-123',
        object: 'chat.completion',
        created: 1234567890,
        model: 'mistral-medium',
        choices: [
          {
            index: 0,
            message: {
              role: 'assistant',
              content: 'Hello! I am doing well, thank you.',
            },
            finish_reason: 'stop',
          },
        ],
        usage: {
          prompt_tokens: 10,
          completion_tokens: 20,
          total_tokens: 30,
        },
      };

      mockChat.mockResolvedValue(response);

      await instance.chat.complete({ model: 'mistral-medium', messages: [] });

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'mistral',
        index: 0,
        finish_reason: 'stop',
        message: JSON.stringify({
          role: 'assistant',
          content: 'Hello! I am doing well, thank you.',
        }),
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.finish_reasons', [
        'stop',
      ]);

      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.usage.input_tokens': 10,
        'gen_ai.usage.output_tokens': 20,
        'gen_ai.usage.total_tokens': 30,
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.model', 'mistral-medium');
      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.id', 'cmpl-123');
    });

    it('should handle errors', async () => {
      const WrappedMistral = wrapMistral(MistralClass);
      const instance = new WrappedMistral();

      const error = new Error('Mistral API Error');
      mockChat.mockRejectedValue(error);

      await expect(
        instance.chat.complete({
          model: 'mistral-medium',
          messages: [],
        }),
      ).rejects.toThrow('Mistral API Error');

      expect(mockSpan.recordException).toHaveBeenCalledWith(error);
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'Mistral API Error',
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should handle missing model parameter', async () => {
      const WrappedMistral = wrapMistral(MistralClass);
      const instance = new WrappedMistral();

      mockChat.mockResolvedValue({ choices: [] });

      await instance.chat.complete({ messages: [] });

      expect(mockTracer.startSpan).toHaveBeenCalledWith('chat unknown', expect.any(Object));
    });
  });

  describe('chatStream wrapping', () => {
    it('should handle streaming responses', async () => {
      const WrappedMistral = wrapMistral(MistralClass);
      const instance = new WrappedMistral();

      // Create a mock async iterable
      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield {
            id: 'cmpl-123',
            object: 'chat.completion.chunk',
            created: 1234567890,
            model: 'mistral-medium',
            choices: [
              {
                index: 0,
                delta: { role: 'assistant', content: 'Hello' },
                finish_reason: null,
              },
            ],
          };
          yield {
            choices: [
              {
                index: 0,
                delta: { content: ' from' },
                finish_reason: null,
              },
            ],
          };
          yield {
            choices: [
              {
                index: 0,
                delta: { content: ' Mistral!' },
                finish_reason: 'stop',
              },
            ],
          };
        },
      };

      mockChatStream.mockReturnValue(mockStream);

      const stream = instance.chat.stream({
        model: 'mistral-medium',
        messages: [],
        stream: true,
      });

      // Consume the stream
      const chunks = [];
      for await (const chunk of stream) {
        chunks.push(chunk);
      }

      expect(chunks).toHaveLength(3);
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'mistral',
        index: 0,
        finish_reason: 'stop',
        message: JSON.stringify({
          role: 'assistant',
          content: 'Hello from Mistral!',
        }),
      });
      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.finish_reasons', [
        'stop',
      ]);
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should handle streaming errors', async () => {
      const WrappedMistral = wrapMistral(MistralClass);
      const instance = new WrappedMistral();

      const error = new Error('Stream error');
      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield {
            choices: [
              {
                delta: { content: 'Hello' },
                finish_reason: null,
              },
            ],
          };
          throw error;
        },
      };

      mockChatStream.mockReturnValue(mockStream);

      const stream = instance.chat.stream({
        model: 'mistral-medium',
        messages: [],
        stream: true,
      });

      const chunks = [];
      await expect(async () => {
        for await (const chunk of stream) {
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

    it('should handle empty deltas in stream', async () => {
      const WrappedMistral = wrapMistral(MistralClass);
      const instance = new WrappedMistral();

      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield { choices: [{ delta: {}, finish_reason: null }] };
          yield { choices: [{ delta: { content: 'Text' }, finish_reason: 'stop' }] };
        },
      };

      mockChatStream.mockReturnValue(mockStream);

      const stream = instance.chat.stream({
        model: 'mistral-medium',
        messages: [],
      });

      const chunks = [];
      for await (const chunk of stream) {
        chunks.push(chunk);
      }

      expect(chunks).toHaveLength(2);
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'mistral',
        index: 0,
        finish_reason: 'stop',
        message: JSON.stringify({ role: 'assistant', content: 'Text' }),
      });
    });
  });

  describe('isChatResponse type guard', () => {
    it('should handle non-response objects', async () => {
      const WrappedMistral = wrapMistral(MistralClass);
      const instance = new WrappedMistral();

      mockChat.mockResolvedValue(null);

      await instance.chat.complete({ model: 'mistral-medium', messages: [] });

      expect(mockSpan.addEvent).not.toHaveBeenCalledWith('gen_ai.choice', expect.any(Object));
    });

    it('should handle response without choices', async () => {
      const WrappedMistral = wrapMistral(MistralClass);
      const instance = new WrappedMistral();

      mockChat.mockResolvedValue({ choices: null });

      await instance.chat.complete({ model: 'mistral-medium', messages: [] });

      expect(mockSpan.addEvent).not.toHaveBeenCalledWith('gen_ai.choice', expect.any(Object));
    });
  });

  describe('instance wrapping', () => {
    it('should wrap an existing Mistral instance', () => {
      const instance = new MistralClass();
      const originalComplete = instance.chat.complete;
      const originalStream = instance.chat.stream;

      const wrappedInstance = wrapMistral(instance);

      expect(wrappedInstance).toBe(instance); // Modified in-place
      expect(instance.chat.complete).not.toBe(originalComplete);
      expect(instance.chat.stream).not.toBe(originalStream);
      expect(instance.chat.complete).toBeDefined();
      expect(instance.chat.stream).toBeDefined();
    });

    it('should handle instance without chat object', () => {
      const instance = {};
      const wrappedInstance = wrapMistral(instance);

      expect(wrappedInstance).toBe(instance);
      // Should not throw
    });

    it('should handle instance with chat object but no methods', () => {
      const instance = { chat: {} };
      const wrappedInstance = wrapMistral(instance);

      expect(wrappedInstance).toBe(instance);
      expect(wrappedInstance.chat).toBeDefined();
      // Should not throw
    });

    it('should handle empty instance', () => {
      const instance = {};
      const wrappedInstance = wrapMistral(instance);

      expect(wrappedInstance).toBe(instance);
      // Should not throw
    });
  });

  describe('recordResponse helper', () => {
    it('should handle empty response', async () => {
      const WrappedMistral = wrapMistral(MistralClass);
      const instance = new WrappedMistral();

      mockChat.mockResolvedValue({});

      await instance.chat.complete({ model: 'mistral-medium', messages: [] });

      // Should not throw, but also shouldn't record anything
      expect(mockSpan.addEvent).not.toHaveBeenCalledWith('gen_ai.choice', expect.any(Object));
    });

    it('should handle choices with missing message', async () => {
      const WrappedMistral = wrapMistral(MistralClass);
      const instance = new WrappedMistral();

      const response = {
        choices: [
          { finish_reason: 'stop' }, // No message property
        ],
      };

      mockChat.mockResolvedValue(response);

      await instance.chat.complete({ model: 'mistral-medium', messages: [] });

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'mistral',
        index: 0,
        finish_reason: 'stop',
        message: JSON.stringify({ role: 'assistant', content: '' }),
      });
    });

    it('should filter out falsy finish reasons', async () => {
      const WrappedMistral = wrapMistral(MistralClass);
      const instance = new WrappedMistral();

      const response = {
        choices: [
          { message: { content: 'a' }, finish_reason: 'stop' },
          { message: { content: 'b' }, finish_reason: null },
          { message: { content: 'c' }, finish_reason: '' },
          { message: { content: 'd' }, finish_reason: 'length' },
        ],
      };

      mockChat.mockResolvedValue(response);

      await instance.chat.complete({ model: 'mistral-medium', messages: [] });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.finish_reasons', [
        'stop',
        'length',
      ]);
    });

    it('should record server.address attribute', async () => {
      const WrappedMistral = wrapMistral(MistralClass);
      const instance = new WrappedMistral();

      const response = {
        choices: [{ message: { content: 'test' } }],
      };

      mockChat.mockResolvedValue(response);

      await instance.chat.complete({ model: 'mistral-medium', messages: [] });

      // server.address is set in the span attributes when the span is created
      expect(mockTracer.startSpan).toHaveBeenCalledWith(
        'chat mistral-medium',
        expect.objectContaining({
          attributes: expect.objectContaining({
            'server.address': 'api.mistral.ai',
          }),
        }),
      );
    });
  });

  describe('wrapStream helper', () => {
    it('should handle malformed streaming chunks', async () => {
      const WrappedMistral = wrapMistral(MistralClass);
      const instance = new WrappedMistral();

      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield null;
          yield undefined;
          yield {};
          yield { choices: null };
          yield { choices: [] };
          yield { choices: [null] };
          yield { choices: [{ delta: { content: 'Valid' }, finish_reason: 'stop' }] };
        },
      };

      mockChatStream.mockReturnValue(mockStream);

      const stream = instance.chat.stream({ model: 'mistral-medium', messages: [] });

      const chunks = [];
      for await (const chunk of stream) {
        chunks.push(chunk);
      }

      expect(chunks).toHaveLength(7);
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'mistral',
        index: 0,
        finish_reason: 'stop',
        message: JSON.stringify({ role: 'assistant', content: 'Valid' }),
      });
    });

    it('should extract role from first chunk', async () => {
      const WrappedMistral = wrapMistral(MistralClass);
      const instance = new WrappedMistral();

      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield {
            choices: [
              {
                delta: { role: 'assistant', content: 'First' },
                finish_reason: null,
              },
            ],
          };
          yield {
            choices: [
              {
                delta: { content: ' Second' }, // No role in subsequent chunks
                finish_reason: 'stop',
              },
            ],
          };
        },
      };

      mockChatStream.mockReturnValue(mockStream);

      const stream = instance.chat.stream({ model: 'mistral-medium', messages: [] });

      for await (const _chunk of stream) {
        // Consume stream
      }

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'mistral',
        index: 0,
        finish_reason: 'stop',
        message: JSON.stringify({ role: 'assistant', content: 'First Second' }),
      });
    });
  });

  describe('error handling with ensureError', () => {
    it('should handle non-Error exceptions', async () => {
      const WrappedMistral = wrapMistral(MistralClass);
      const instance = new WrappedMistral();

      const nonErrorValue = { message: 'object error', code: 'ERR_001' };
      mockChat.mockRejectedValue(nonErrorValue);

      await expect(
        instance.chat.complete({
          model: 'mistral-medium',
          messages: [],
        }),
      ).rejects.toThrow();

      expect(mockedEnsureError).toHaveBeenCalledWith(nonErrorValue);
      expect(mockSpan.recordException).toHaveBeenCalledWith(expect.any(Error));
    });

    it('should handle non-Error exceptions in streaming', async () => {
      const WrappedMistral = wrapMistral(MistralClass);
      const instance = new WrappedMistral();

      const nonErrorValue = 'string error';
      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield { choices: [{ delta: { content: 'test' } }] };
          throw nonErrorValue;
        },
      };

      mockChatStream.mockReturnValue(mockStream);

      const stream = instance.chat.stream({ model: 'mistral-medium', messages: [] });

      await expect(async () => {
        for await (const _chunk of stream) {
          // Process chunk
        }
      }).rejects.toThrow('string error');

      expect(mockedEnsureError).toHaveBeenCalledWith(nonErrorValue);
      expect(mockSpan.recordException).toHaveBeenCalledWith(expect.any(Error));
    });
  });
});
