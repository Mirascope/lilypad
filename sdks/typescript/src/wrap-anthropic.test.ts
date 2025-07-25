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
import { wrapAnthropic } from './wrap-anthropic';
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

describe('wrapAnthropic', () => {
  let mockSpan: any;
  let mockTracer: any;
  let mockOriginalCreate: any;
  let AnthropicClass: any;

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

    // Create base Anthropic class
    AnthropicClass = class {
      messages = {
        create: mockOriginalCreate,
      };
    };
  });

  describe('class wrapping', () => {
    it('should create a wrapped class that extends the original', () => {
      const WrappedAnthropic = wrapAnthropic(AnthropicClass);
      const instance = new WrappedAnthropic();

      expect(instance).toBeInstanceOf(AnthropicClass);
      expect(instance.messages.create).toBeDefined();
      expect(instance.messages.create).not.toBe(mockOriginalCreate);
    });

    it('should log debug message when wrapping', () => {
      wrapAnthropic(AnthropicClass);

      expect(mockedLogger.debug).toHaveBeenCalledWith('[wrapAnthropic] Wrapping Anthropic instance');
    });

    it('should handle missing messages.create gracefully', () => {
      const EmptyClass = class {};
      const WrappedClass = wrapAnthropic(EmptyClass);
      const instance = new WrappedClass();

      expect(instance).toBeInstanceOf(EmptyClass);
    });
  });

  describe('messages.create wrapping', () => {
    it('should create a span with correct attributes', async () => {
      const WrappedAnthropic = wrapAnthropic(AnthropicClass);
      const instance = new WrappedAnthropic();

      const params = {
        model: 'claude-3-opus-20240229',
        messages: [{ role: 'user', content: 'Hello' }],
        max_tokens: 1000,
        temperature: 0.7,
        top_p: 0.9,
        top_k: 20,
      };

      mockOriginalCreate.mockResolvedValue({ 
        type: 'message',
        content: []
      });

      await instance.messages.create(params);

      expect(mockTracer.startSpan).toHaveBeenCalledWith('chat claude-3-opus-20240229', {
        kind: SpanKind.CLIENT,
        attributes: {
          'gen_ai.system': 'anthropic',
          'server.address': 'api.anthropic.com',
          'gen_ai.request.model': 'claude-3-opus-20240229',
          'gen_ai.request.temperature': 0.7,
          'gen_ai.request.max_tokens': 1000,
          'gen_ai.request.top_p': 0.9,
          'gen_ai.request.top_k': 20,
          'gen_ai.operation.name': 'chat',
        },
      });
    });

    it('should record system message', async () => {
      const WrappedAnthropic = wrapAnthropic(AnthropicClass);
      const instance = new WrappedAnthropic();

      const params = {
        model: 'claude-3-opus-20240229',
        messages: [{ role: 'user', content: 'Hello' }],
        system: 'You are a helpful assistant',
        max_tokens: 1000,
      };

      mockOriginalCreate.mockResolvedValue({ 
        type: 'message',
        content: []
      });

      await instance.messages.create(params);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.system.message', {
        'gen_ai.system': 'anthropic',
        content: 'You are a helpful assistant',
      });
    });

    it('should record message events', async () => {
      const WrappedAnthropic = wrapAnthropic(AnthropicClass);
      const instance = new WrappedAnthropic();

      const params = {
        model: 'claude-3-opus-20240229',
        messages: [
          { role: 'user', content: 'Hello' },
          { role: 'assistant', content: 'Hi there!' },
          { role: 'user', content: 'How are you?' },
        ],
        max_tokens: 1000,
      };

      mockOriginalCreate.mockResolvedValue({ 
        type: 'message',
        content: []
      });

      await instance.messages.create(params);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.user.message', {
        'gen_ai.system': 'anthropic',
        content: 'Hello',
      });
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.assistant.message', {
        'gen_ai.system': 'anthropic',
        content: 'Hi there!',
      });
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.user.message', {
        'gen_ai.system': 'anthropic',
        content: 'How are you?',
      });
    });

    it('should handle complex message content', async () => {
      const WrappedAnthropic = wrapAnthropic(AnthropicClass);
      const instance = new WrappedAnthropic();

      const params = {
        model: 'claude-3-opus-20240229',
        messages: [{ 
          role: 'user', 
          content: [
            { type: 'text', text: 'What is in this image?' },
            { 
              type: 'image',
              source: { 
                type: 'base64',
                media_type: 'image/jpeg',
                data: 'base64data'
              }
            }
          ]
        }],
        max_tokens: 1000,
      };

      mockOriginalCreate.mockResolvedValue({ 
        type: 'message',
        content: []
      });

      await instance.messages.create(params);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.user.message', {
        'gen_ai.system': 'anthropic',
        content: JSON.stringify([
          { type: 'text', text: 'What is in this image?' },
          { 
            type: 'image',
            source: { 
              type: 'base64',
              media_type: 'image/jpeg',
              data: 'base64data'
            }
          }
        ]),
      });
    });

    it('should record response data', async () => {
      const WrappedAnthropic = wrapAnthropic(AnthropicClass);
      const instance = new WrappedAnthropic();

      const response = {
        id: 'msg_123',
        type: 'message',
        role: 'assistant',
        model: 'claude-3-opus-20240229',
        content: [
          { type: 'text', text: 'Hello! How can I help you today?' }
        ],
        stop_reason: 'end_turn',
        stop_sequence: null,
        usage: {
          input_tokens: 10,
          output_tokens: 20,
        },
      };

      mockOriginalCreate.mockResolvedValue(response);

      await instance.messages.create({ 
        model: 'claude-3-opus-20240229',
        messages: [],
        max_tokens: 1000
      });

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'anthropic',
        index: 0,
        finish_reason: 'end_turn',
        message: JSON.stringify({ 
          role: 'assistant', 
          content: 'Hello! How can I help you today?' 
        }),
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith(
        'gen_ai.response.finish_reasons', 
        ['end_turn']
      );

      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.usage.input_tokens': 10,
        'gen_ai.usage.output_tokens': 20,
        'gen_ai.usage.total_tokens': 30,
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.model', 'claude-3-opus-20240229');
      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.id', 'msg_123');
    });

    it('should handle errors', async () => {
      const WrappedAnthropic = wrapAnthropic(AnthropicClass);
      const instance = new WrappedAnthropic();

      const error = new Error('API Error');
      mockOriginalCreate.mockRejectedValue(error);

      await expect(instance.messages.create({ 
        model: 'claude-3-opus-20240229',
        messages: [],
        max_tokens: 1000
      })).rejects.toThrow('API Error');

      expect(mockSpan.recordException).toHaveBeenCalledWith(error);
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'API Error',
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should handle streaming responses', async () => {
      const WrappedAnthropic = wrapAnthropic(AnthropicClass);
      const instance = new WrappedAnthropic();

      // Create a mock async iterable
      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield {
            type: 'message_start',
            message: {
              id: 'msg_123',
              type: 'message',
              role: 'assistant',
              content: [],
              model: 'claude-3-opus-20240229',
              stop_reason: null,
              stop_sequence: null,
              usage: { input_tokens: 10, output_tokens: 0 },
            },
          };
          yield {
            type: 'content_block_delta',
            index: 0,
            delta: { type: 'text_delta', text: 'Hello' },
          };
          yield {
            type: 'content_block_delta',
            index: 0,
            delta: { type: 'text_delta', text: ' world!' },
          };
          yield {
            type: 'message_delta',
            delta: { stop_reason: 'end_turn' },
          };
          yield {
            type: 'message_stop',
            usage: { output_tokens: 8 },
          };
        },
      };

      mockOriginalCreate.mockResolvedValue(mockStream);
      mockedIsAsyncIterable.mockReturnValue(true);

      const result = await instance.messages.create({ 
        model: 'claude-3-opus-20240229',
        messages: [],
        max_tokens: 1000,
        stream: true 
      });

      // Consume the stream
      const chunks = [];
      for await (const chunk of result) {
        chunks.push(chunk);
      }

      expect(chunks).toHaveLength(5);
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'anthropic',
        index: 0,
        finish_reason: 'end_turn',
        message: JSON.stringify({ role: 'assistant', content: 'Hello world!' }),
      });
      expect(mockSpan.setAttribute).toHaveBeenCalledWith(
        'gen_ai.response.finish_reasons', 
        ['end_turn']
      );
      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.usage.input_tokens': 10,
        'gen_ai.usage.output_tokens': 8,
        'gen_ai.usage.total_tokens': 18,
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should handle streaming errors', async () => {
      const WrappedAnthropic = wrapAnthropic(AnthropicClass);
      const instance = new WrappedAnthropic();

      const error = new Error('Stream error');
      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield {
            type: 'content_block_delta',
            delta: { type: 'text_delta', text: 'Hello' },
          };
          throw error;
        },
      };

      mockOriginalCreate.mockResolvedValue(mockStream);
      mockedIsAsyncIterable.mockReturnValue(true);

      const result = await instance.messages.create({ 
        model: 'claude-3-opus-20240229',
        messages: [],
        max_tokens: 1000,
        stream: true 
      });

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

    it('should pass through all arguments to original method', async () => {
      const WrappedAnthropic = wrapAnthropic(AnthropicClass);
      const instance = new WrappedAnthropic();

      const params = { 
        model: 'claude-3-opus-20240229',
        messages: [],
        max_tokens: 1000
      };
      const options = { headers: { 'X-Custom': 'value' } };

      mockOriginalCreate.mockResolvedValue({ 
        type: 'message',
        content: []
      });

      await instance.messages.create(params, options);

      expect(mockOriginalCreate).toHaveBeenCalledWith(params, options);
    });
  });

  describe('isMessageResponse type guard', () => {
    it('should handle non-message responses', async () => {
      const WrappedAnthropic = wrapAnthropic(AnthropicClass);
      const instance = new WrappedAnthropic();

      // Return something that doesn't match AnthropicMessageResponse structure
      mockOriginalCreate.mockResolvedValue(null);

      await instance.messages.create({ 
        model: 'claude-3-opus-20240229',
        messages: [],
        max_tokens: 1000
      });

      // Should not try to record response
      expect(mockSpan.addEvent).not.toHaveBeenCalledWith('gen_ai.choice', expect.any(Object));
    });

    it('should handle response without content array', async () => {
      const WrappedAnthropic = wrapAnthropic(AnthropicClass);
      const instance = new WrappedAnthropic();

      mockOriginalCreate.mockResolvedValue({ 
        type: 'message',
        content: null 
      });

      await instance.messages.create({ 
        model: 'claude-3-opus-20240229',
        messages: [],
        max_tokens: 1000
      });

      expect(mockSpan.addEvent).not.toHaveBeenCalledWith('gen_ai.choice', expect.any(Object));
    });
  });

  describe('instance wrapping', () => {
    it('should wrap an existing Anthropic instance', () => {
      const instance = new AnthropicClass();
      const originalCreate = instance.messages.create;

      const wrappedInstance = wrapAnthropic(instance);

      expect(wrappedInstance).toBe(instance); // Modified in-place
      expect(instance.messages.create).not.toBe(originalCreate);
      expect(instance.messages.create).toBeDefined();
    });

    it('should handle instance without messages property', () => {
      const instance = {};
      const wrappedInstance = wrapAnthropic(instance);

      expect(wrappedInstance).toBe(instance);
      // Should not throw
    });

    it('should handle instance without create method', () => {
      const instance = { messages: {} };
      const wrappedInstance = wrapAnthropic(instance);

      expect(wrappedInstance).toBe(instance);
      // Should not throw
    });
  });

  describe('recordResponse helper', () => {
    it('should handle empty response', async () => {
      const WrappedAnthropic = wrapAnthropic(AnthropicClass);
      const instance = new WrappedAnthropic();

      mockOriginalCreate.mockResolvedValue({});

      await instance.messages.create({ 
        model: 'claude-3-opus-20240229',
        messages: [],
        max_tokens: 1000
      });

      // Should not throw, but also shouldn't record anything
      expect(mockSpan.addEvent).not.toHaveBeenCalledWith('gen_ai.choice', expect.any(Object));
    });

    it('should handle multiple text content blocks', async () => {
      const WrappedAnthropic = wrapAnthropic(AnthropicClass);
      const instance = new WrappedAnthropic();

      const response = {
        type: 'message',
        role: 'assistant',
        content: [
          { type: 'text', text: 'First part. ' },
          { type: 'text', text: 'Second part.' }
        ],
        stop_reason: 'end_turn',
      };

      mockOriginalCreate.mockResolvedValue(response);

      await instance.messages.create({ 
        model: 'claude-3-opus-20240229',
        messages: [],
        max_tokens: 1000
      });

      // Should record each content block separately
      expect(mockSpan.addEvent).toHaveBeenCalledTimes(2);
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'anthropic',
        index: 0,
        finish_reason: 'end_turn',
        message: JSON.stringify({ role: 'assistant', content: 'First part. ' }),
      });
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'anthropic',
        index: 1,
        finish_reason: 'end_turn',
        message: JSON.stringify({ role: 'assistant', content: 'Second part.' }),
      });
    });

    it('should record server.address attribute', async () => {
      const WrappedAnthropic = wrapAnthropic(AnthropicClass);
      const instance = new WrappedAnthropic();

      const response = {
        type: 'message',
        content: [{ type: 'text', text: 'test' }],
      };

      mockOriginalCreate.mockResolvedValue(response);

      await instance.messages.create({ 
        model: 'claude-3-opus-20240229',
        messages: [],
        max_tokens: 1000
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('server.address', 'api.anthropic.com');
    });
  });

  describe('wrapStream helper', () => {
    it('should handle stream with various chunk types', async () => {
      const WrappedAnthropic = wrapAnthropic(AnthropicClass);
      const instance = new WrappedAnthropic();

      const mockStream = {
        async *[Symbol.asyncIterator]() {
          // Unknown chunk type
          yield { type: 'unknown' };
          // content_block_start
          yield {
            type: 'content_block_start',
            index: 0,
            content_block: { type: 'text', text: '' },
          };
          // content_block_stop
          yield {
            type: 'content_block_stop',
            index: 0,
          };
        },
      };

      mockOriginalCreate.mockResolvedValue(mockStream);
      mockedIsAsyncIterable.mockReturnValue(true);

      const result = await instance.messages.create({ 
        model: 'claude-3-opus-20240229',
        messages: [],
        max_tokens: 1000,
        stream: true 
      });

      const chunks = [];
      for await (const chunk of result) {
        chunks.push(chunk);
      }

      expect(chunks).toHaveLength(3);
      // Should handle all chunk types gracefully
    });

    it('should handle malformed streaming chunks', async () => {
      const WrappedAnthropic = wrapAnthropic(AnthropicClass);
      const instance = new WrappedAnthropic();

      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield null;
          yield undefined;
          yield {};
          yield { type: 'content_block_delta' }; // No delta
          yield { type: 'content_block_delta', delta: {} }; // Empty delta
          yield { type: 'message_stop' }; // No usage
          yield {
            type: 'content_block_delta',
            delta: { type: 'text_delta', text: 'Valid' },
          };
        },
      };

      mockOriginalCreate.mockResolvedValue(mockStream);
      mockedIsAsyncIterable.mockReturnValue(true);

      const result = await instance.messages.create({ 
        model: 'claude-3-opus-20240229',
        messages: [],
        max_tokens: 1000,
        stream: true 
      });

      const chunks = [];
      for await (const chunk of result) {
        chunks.push(chunk);
      }

      expect(chunks).toHaveLength(7);
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'anthropic',
        index: 0,
        finish_reason: 'error',
        message: JSON.stringify({ role: 'assistant', content: 'Valid' }),
      });
    });

    it('should ensure error is Error instance', async () => {
      const WrappedAnthropic = wrapAnthropic(AnthropicClass);
      const instance = new WrappedAnthropic();

      const nonErrorValue = 'string error';
      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield {
            type: 'content_block_delta',
            delta: { type: 'text_delta', text: 'Hello' },
          };
          throw nonErrorValue;
        },
      };

      mockOriginalCreate.mockResolvedValue(mockStream);
      mockedIsAsyncIterable.mockReturnValue(true);

      const result = await instance.messages.create({ 
        model: 'claude-3-opus-20240229',
        messages: [],
        max_tokens: 1000,
        stream: true 
      });

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
  });

  describe('error handling with ensureError', () => {
    it('should handle non-Error exceptions in non-streaming mode', async () => {
      const WrappedAnthropic = wrapAnthropic(AnthropicClass);
      const instance = new WrappedAnthropic();

      const nonErrorValue = { message: 'object error', code: 'ERR_001' };
      mockOriginalCreate.mockRejectedValue(nonErrorValue);

      await expect(instance.messages.create({ 
        model: 'claude-3-opus-20240229',
        messages: [],
        max_tokens: 1000
      })).rejects.toThrow();

      expect(mockedEnsureError).toHaveBeenCalledWith(nonErrorValue);
      expect(mockSpan.recordException).toHaveBeenCalledWith(expect.any(Error));
    });
  });
});