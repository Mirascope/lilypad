import { describe, it, expect, beforeEach, vi } from 'vitest';
import { wrapOpenAI } from './wrap-openai';
import { SpanKind, SpanStatusCode } from '@opentelemetry/api';

// Mock modules
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

// Import mocked modules
import { trace, context } from '@opentelemetry/api';
import { logger } from './utils/logger';
import { isAsyncIterable } from './utils/stream-wrapper';

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

    // Mock API functions
    vi.mocked(trace.getTracer).mockReturnValue(mockTracer);
    vi.mocked(trace.setSpan).mockImplementation((ctx, span) => ({ ...ctx, span }));
    vi.mocked(context.active).mockReturnValue({});
    vi.mocked(context.with).mockImplementation((ctx, fn) => fn());

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

      expect(logger.debug).toHaveBeenCalledWith('[wrapOpenAI] Wrapping OpenAI instance');
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
      vi.mocked(isAsyncIterable).mockReturnValue(true);

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
      vi.mocked(isAsyncIterable).mockReturnValue(true);

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
});
