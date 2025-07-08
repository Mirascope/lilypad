import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { trace, SpanStatusCode, SpanKind } from '@opentelemetry/api';
import { logger } from '../utils/logger';
import { isSDKShuttingDown } from '../shutdown';
import { StreamWrapper } from '../utils/stream-wrapper';

// Note: Testing module patching is complex in vitest, so we'll focus on testing
// the wrapping logic directly

// Mock modules
vi.mock('../utils/logger', () => ({
  logger: {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock('../shutdown', () => ({
  isSDKShuttingDown: vi.fn(() => false),
}));

vi.mock('../utils/stream-wrapper', () => ({
  StreamWrapper: vi.fn().mockImplementation((stream, span, options) => {
    // Return an async iterable that processes chunks through callbacks
    return {
      async *[Symbol.asyncIterator]() {
        if (options?.onChunk) {
          for await (const chunk of stream) {
            options.onChunk(chunk);
            yield chunk;
          }
        } else {
          yield* stream;
        }
        if (options?.onFinalize) {
          options.onFinalize();
        }
      },
    };
  }),
  isAsyncIterable: (obj: any) => obj && typeof obj[Symbol.asyncIterator] === 'function',
}));

describe('OpenAI Wrapper Module Logic', () => {
  let mockTracer: any;
  let mockSpan: any;

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
      startActiveSpan: vi.fn((name, options, callback) => {
        return callback(mockSpan);
      }),
    };

    // Mock trace API
    vi.spyOn(trace, 'getTracer').mockReturnValue(mockTracer);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('wrapChatCompletionsCreate logic', () => {
    it('should skip instrumentation when SDK is shutting down', async () => {
      vi.mocked(isSDKShuttingDown).mockReturnValue(true);

      const originalCreate = vi.fn().mockResolvedValue({});
      const params = { model: 'gpt-4' };

      // Import the actual implementation to test the wrap function
      const { wrapChatCompletionsCreate } = await import('./openai-wrapper');
      const wrapped = wrapChatCompletionsCreate(originalCreate);

      await wrapped.call({}, params);

      expect(originalCreate).toHaveBeenCalledWith(params, undefined);
      expect(mockTracer.startActiveSpan).not.toHaveBeenCalled();
    });

    it('should create span for non-streaming completion', async () => {
      const params = {
        model: 'gpt-4',
        messages: [{ role: 'user', content: 'Hello' }],
        temperature: 0.7,
        max_tokens: 100,
      };

      const response = {
        choices: [
          {
            message: { role: 'assistant', content: 'Hi there!' },
            finish_reason: 'stop',
          },
        ],
        usage: {
          prompt_tokens: 10,
          completion_tokens: 5,
          total_tokens: 15,
        },
        model: 'gpt-4-0613',
      };

      const originalCreate = vi.fn().mockResolvedValue(response);

      // Import and test the wrap function
      const { wrapChatCompletionsCreate } = await import('./openai-wrapper');
      const wrapped = wrapChatCompletionsCreate(originalCreate);

      const result = await wrapped.call({}, params);

      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        'openai.chat.completions gpt-4',
        expect.objectContaining({
          kind: SpanKind.CLIENT,
          attributes: expect.objectContaining({
            'gen_ai.system': 'openai',
            'gen_ai.request.model': 'gpt-4',
            'gen_ai.request.temperature': 0.7,
            'gen_ai.request.max_tokens': 100,
            'gen_ai.operation.name': 'chat',
            'lilypad.type': 'llm',
          }),
        }),
        expect.any(Function),
      );

      expect(result).toBe(response);
      expect(mockSpan.setStatus).toHaveBeenCalledWith({ code: SpanStatusCode.OK });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should handle streaming response', async () => {
      const params = { model: 'gpt-4', stream: true };

      const mockStream = {
        [Symbol.asyncIterator]: vi.fn(() => ({
          next: vi
            .fn()
            .mockResolvedValueOnce({
              value: { choices: [{ delta: { content: 'Hello' } }] },
              done: false,
            })
            .mockResolvedValueOnce({ done: true }),
        })),
      };

      const originalCreate = vi.fn().mockResolvedValue(mockStream);

      const { wrapChatCompletionsCreate } = await import('./openai-wrapper');
      const wrapped = wrapChatCompletionsCreate(originalCreate);

      const result = await wrapped.call({}, params);

      expect(vi.mocked(StreamWrapper)).toHaveBeenCalledWith(
        mockStream,
        mockSpan,
        expect.objectContaining({
          onChunk: expect.any(Function),
          onFinalize: expect.any(Function),
        }),
      );
      expect(result).toBeDefined();

      // The result should be what the StreamWrapper mock returns
      // Just verify it was called correctly
      expect(vi.mocked(StreamWrapper)).toHaveBeenCalled();
    });

    it('should handle errors', async () => {
      const params = { model: 'gpt-4' };
      const error = new Error('API Error');
      const originalCreate = vi.fn().mockRejectedValue(error);

      const { wrapChatCompletionsCreate } = await import('./openai-wrapper');
      const wrapped = wrapChatCompletionsCreate(originalCreate);

      await expect(wrapped.call({}, params)).rejects.toThrow('API Error');

      expect(mockSpan.recordException).toHaveBeenCalledWith(error);
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'API Error',
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should record messages', async () => {
      const params = {
        model: 'gpt-4',
        messages: [
          { role: 'system', content: 'You are helpful' },
          { role: 'user', content: 'Hello' },
        ],
      };

      const originalCreate = vi.fn().mockResolvedValue({});

      const { wrapChatCompletionsCreate } = await import('./openai-wrapper');
      const wrapped = wrapChatCompletionsCreate(originalCreate);

      await wrapped.call({}, params);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.content.prompt', {
        'gen_ai.prompt.role': 'system',
        'gen_ai.prompt.content': '"You are helpful"',
        'gen_ai.prompt.index': '0',
      });

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.content.prompt', {
        'gen_ai.prompt.role': 'user',
        'gen_ai.prompt.content': '"Hello"',
        'gen_ai.prompt.index': '1',
      });
    });

    it('should record completion response', async () => {
      const params = { model: 'gpt-4' };
      const response = {
        choices: [
          {
            message: { role: 'assistant', content: 'Hello!' },
            finish_reason: 'stop',
          },
        ],
        usage: {
          prompt_tokens: 10,
          completion_tokens: 5,
          total_tokens: 15,
        },
        model: 'gpt-4-0613',
      };

      const originalCreate = vi.fn().mockResolvedValue(response);

      const { wrapChatCompletionsCreate } = await import('./openai-wrapper');
      const wrapped = wrapChatCompletionsCreate(originalCreate);

      await wrapped.call({}, params);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.content.completion', {
        'gen_ai.completion.role': 'assistant',
        'gen_ai.completion.content': '"Hello!"',
        'gen_ai.completion.index': '0',
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.finish_reasons', [
        'stop',
      ]);

      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.usage.input_tokens': 10,
        'gen_ai.usage.output_tokens': 5,
        'gen_ai.usage.total_tokens': 15,
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.model', 'gpt-4-0613');
    });
  });

  describe('wrapOpenAIModule function', () => {
    it('should create wrapped module with proper structure', async () => {
      const mockOpenAI = class OpenAI {
        static VERSION = '1.0.0';
        chat = {
          completions: {
            create: vi.fn(),
          },
        };
      };

      const openaiModule = { default: mockOpenAI };

      const { wrapOpenAIModule } = await import('./openai-wrapper');
      const wrapped = wrapOpenAIModule(openaiModule);

      expect(wrapped.default).toBeDefined();
      expect(typeof wrapped.default).toBe('function');
      expect(wrapped.default.VERSION).toBe('1.0.0');
    });

    it('should handle module with OpenAI named export', async () => {
      const mockOpenAI = class OpenAI {
        chat = {
          completions: {
            create: vi.fn(),
          },
        };
      };

      const openaiModule = { OpenAI: mockOpenAI };

      const { wrapOpenAIModule } = await import('./openai-wrapper');
      const wrapped = wrapOpenAIModule(openaiModule);

      expect(wrapped.OpenAI).toBeDefined();
      expect(typeof wrapped.OpenAI).toBe('function');
    });

    it('should handle module without OpenAI class', async () => {
      const openaiModule = { someOtherExport: 'value' };

      const { wrapOpenAIModule } = await import('./openai-wrapper');
      const wrapped = wrapOpenAIModule(openaiModule);

      expect(wrapped).toEqual({ someOtherExport: 'value' });
      expect(logger.error).toHaveBeenCalledWith('Could not find OpenAI class in module');
    });
  });
});
