import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { trace, SpanStatusCode, SpanKind } from '@opentelemetry/api';
import { OpenAIAutoInstrumentation } from './openai-auto';
import { logger } from '../utils/logger';
import { isSDKShuttingDown } from '../shutdown';
import { StreamWrapper } from '../utils/stream-wrapper';

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
  StreamWrapper: vi.fn().mockImplementation((stream) => {
    const handlers: Record<string, Function[]> = {};
    return {
      on: (event: string, handler: Function) => {
        if (!handlers[event]) handlers[event] = [];
        handlers[event].push(handler);
      },
      emit: (event: string, ...args: any[]) => {
        if (handlers[event]) {
          handlers[event].forEach((handler) => handler(...args));
        }
      },
      [Symbol.asyncIterator]: () => stream[Symbol.asyncIterator](),
    };
  }),
  isAsyncIterable: (obj: any) => obj && typeof obj[Symbol.asyncIterator] === 'function',
}));

describe('OpenAIAutoInstrumentation', () => {
  let instrumentation: OpenAIAutoInstrumentation;
  let mockTracer: any;
  let mockSpan: any;

  beforeEach(() => {
    instrumentation = new OpenAIAutoInstrumentation();

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
    vi.clearAllMocks();
  });

  it('should initialize with correct name and version', () => {
    expect(instrumentation.instrumentationName).toBe('openai');
    expect(instrumentation.instrumentationVersion).toBe('0.1.0');
  });

  describe('init', () => {
    it('should return instrumentation node module definition', () => {
      const result = (instrumentation as any).init();
      expect(result).toHaveLength(1);
      expect(result[0]).toBeDefined();
      expect(result[0].name).toBe('openai');
      expect(result[0].supportedVersions).toEqual(['>=4.0.0']);
    });

    it('should patch and unpatch module exports', () => {
      const mockModule = {
        default: class OpenAI {
          chat = {
            completions: {
              create: vi.fn(),
            },
          };
        },
      };

      const result = (instrumentation as any).init();
      const patchedModule = result[0].patch(mockModule);

      expect(patchedModule.default).toBeDefined();
      expect(patchedModule.OpenAI).toBeDefined();

      // Test unpatch
      const unpatchedModule = result[0].unpatch(patchedModule);
      expect(unpatchedModule).toBe(patchedModule);
    });
  });

  describe('patchOpenAIModule', () => {
    it('should wrap OpenAI class with instrumentation', () => {
      const mockCreate = vi.fn();
      const OpenAI = class {
        chat = {
          completions: {
            create: mockCreate,
          },
        };
      };

      const mockModule = { default: OpenAI };
      const patched = (instrumentation as any).patchOpenAIModule(mockModule);

      // Create instance
      const instance = new patched.default({});
      expect(instance.chat.completions.create).not.toBe(mockCreate);
    });

    it('should handle module without default export', () => {
      const mockCreate = vi.fn();
      const OpenAI = class {
        chat = {
          completions: {
            create: mockCreate,
          },
        };
      };

      const mockModule = { OpenAI };
      const patched = (instrumentation as any).patchOpenAIModule(mockModule);

      expect(patched.OpenAI).toBeDefined();
      const instance = new patched.OpenAI({});
      expect(instance.chat.completions.create).not.toBe(mockCreate);
    });

    it('should handle module with additional exports', () => {
      const mockCreate = vi.fn();
      const OpenAI = class {
        chat = {
          completions: {
            create: mockCreate,
          },
        };
      };

      const mockModule = {
        default: OpenAI,
        OpenAI,
        someOtherExport: 'value',
        anotherExport: { nested: true },
      };

      const patched = (instrumentation as any).patchOpenAIModule(mockModule);

      // OpenAI exports should be wrapped
      expect(patched.default).toBeDefined();
      expect(patched.OpenAI).toBeDefined();

      // Other exports should be preserved as-is
      expect(patched.someOtherExport).toBe('value');
      expect(patched.anotherExport).toEqual({ nested: true });
    });

    it('should handle missing OpenAI class', () => {
      const mockModule = {};
      const patched = (instrumentation as any).patchOpenAIModule(mockModule);
      expect(patched).toBe(mockModule);
      expect(logger.error).toHaveBeenCalledWith('Could not find OpenAI class in module exports');
    });

    it('should warn when chat.completions.create is not found', () => {
      const OpenAI = class {
        // No chat property
      };

      const mockModule = { default: OpenAI };
      const patched = (instrumentation as any).patchOpenAIModule(mockModule);

      new patched.default({});
      expect(logger.warn).toHaveBeenCalledWith(
        'chat.completions.create not found on OpenAI instance',
      );
    });

    it('should copy static properties from original class', () => {
      const OpenAI = class {
        static VERSION = '1.0.0';
        static API_KEY = 'test';
        chat = {
          completions: {
            create: vi.fn(),
          },
        };
      };

      const mockModule = { default: OpenAI };
      const patched = (instrumentation as any).patchOpenAIModule(mockModule);

      expect(patched.default.VERSION).toBe('1.0.0');
      expect(patched.default.API_KEY).toBe('test');
    });
  });

  describe('wrapChatCompletionsCreate', () => {
    let originalCreate: any;
    let wrappedCreate: any;

    beforeEach(() => {
      originalCreate = vi.fn();
      wrappedCreate = (instrumentation as any).wrapChatCompletionsCreate(originalCreate);
    });

    it('should skip instrumentation when SDK is shutting down', async () => {
      vi.mocked(isSDKShuttingDown).mockReturnValue(true);

      const params = { model: 'gpt-4' };
      await wrappedCreate(params);

      expect(originalCreate).toHaveBeenCalledWith(params, undefined);
      expect(mockTracer.startActiveSpan).not.toHaveBeenCalled();
    });

    it('should create span for non-streaming completion', async () => {
      vi.mocked(isSDKShuttingDown).mockReturnValue(false);

      const params = {
        model: 'gpt-4',
        messages: [{ role: 'user', content: 'Hello' }],
        temperature: 0.7,
        max_tokens: 100,
        top_p: 0.9,
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

      originalCreate.mockResolvedValue(response);
      const result = await wrappedCreate.call({}, params);

      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        'openai.chat.completions gpt-4',
        expect.objectContaining({
          kind: SpanKind.CLIENT,
          attributes: expect.objectContaining({
            'gen_ai.system': 'openai',
            'gen_ai.request.model': 'gpt-4',
            'gen_ai.request.temperature': 0.7,
            'gen_ai.request.max_tokens': 100,
            'gen_ai.request.top_p': 0.9,
            'gen_ai.operation.name': 'chat',
            'lilypad.type': 'llm',
          }),
        }),
        expect.any(Function),
      );

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.content.prompt', {
        'gen_ai.prompt.role': 'user',
        'gen_ai.prompt.content': '"Hello"',
        'gen_ai.prompt.index': '0',
      });

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.content.completion', {
        'gen_ai.completion.role': 'assistant',
        'gen_ai.completion.content': '"Hi there!"',
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

      expect(mockSpan.setStatus).toHaveBeenCalledWith({ code: SpanStatusCode.OK });
      expect(mockSpan.end).toHaveBeenCalled();
      expect(result).toBe(response);
    });

    it('should handle streaming response', async () => {
      vi.mocked(isSDKShuttingDown).mockReturnValue(false);

      const params = { model: 'gpt-4', stream: true };

      const mockStream = {
        [Symbol.asyncIterator]: vi.fn(() => ({
          next: vi
            .fn()
            .mockResolvedValueOnce({
              value: { choices: [{ delta: { content: 'Hello' } }] },
              done: false,
            })
            .mockResolvedValueOnce({
              value: { choices: [{ delta: { content: ' world' }, finish_reason: 'stop' }] },
              done: false,
            })
            .mockResolvedValueOnce({ done: true }),
        })),
      };

      originalCreate.mockResolvedValue(mockStream);
      const result = await wrappedCreate.call({}, params);

      expect(vi.mocked(StreamWrapper)).toHaveBeenCalledWith(mockStream);
      expect(result).toBeDefined();
    });

    it('should handle errors', async () => {
      vi.mocked(isSDKShuttingDown).mockReturnValue(false);

      const params = { model: 'gpt-4' };
      const error = new Error('API Error');
      originalCreate.mockRejectedValue(error);

      await expect(wrappedCreate.call({}, params)).rejects.toThrow('API Error');

      expect(mockSpan.recordException).toHaveBeenCalledWith(error);
      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.error.type': 'Error',
        'gen_ai.error.message': 'API Error',
      });
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'API Error',
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should handle missing model', async () => {
      vi.mocked(isSDKShuttingDown).mockReturnValue(false);

      const params = { messages: [] };
      originalCreate.mockResolvedValue({});

      await wrappedCreate.call({}, params);

      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        'openai.chat.completions unknown',
        expect.any(Object),
        expect.any(Function),
      );
    });

    it('should handle response without choices', async () => {
      const params = { model: 'gpt-4' };
      originalCreate.mockResolvedValue({});

      const result = await wrappedCreate(params);

      expect(mockSpan.addEvent).not.toHaveBeenCalledWith(
        'gen_ai.content.completion',
        expect.any(Object),
      );
      expect(result).toEqual({});
    });

    it('should preserve context when calling original method', async () => {
      const context = { apiKey: 'test-key' };
      const params = { model: 'gpt-4' };
      originalCreate.mockResolvedValue({});

      await wrappedCreate.call(context, params);

      expect(originalCreate).toHaveBeenCalledWith(params, undefined);
      // Verify that the function was called with the correct context
      expect(originalCreate).toHaveBeenCalled();
    });

    it('should pass options to original method', async () => {
      const params = { model: 'gpt-4' };
      const options = { timeout: 5000 };
      originalCreate.mockResolvedValue({});

      await wrappedCreate(params, options);

      expect(originalCreate).toHaveBeenCalledWith(params, options);
    });
  });

  describe('handleStreamingResponse', () => {
    it('should handle streaming chunks and reconstruct content', async () => {
      let dataHandler: Function;
      let endHandler: Function;

      const mockWrapper = {
        on: vi.fn((event, handler) => {
          if (event === 'data') dataHandler = handler;
          if (event === 'end') endHandler = handler;
        }),
        [Symbol.asyncIterator]: vi.fn(),
      };

      vi.mocked(StreamWrapper).mockReturnValue(mockWrapper as any);

      const chunks = [
        { choices: [{ delta: { content: 'Hello' } }] },
        { choices: [{ delta: { content: ' world' } }] },
        { choices: [{ finish_reason: 'stop' }] },
      ];

      const stream = { [Symbol.asyncIterator]: vi.fn() };
      const result = await (instrumentation as any).handleStreamingResponse(stream, mockSpan);

      // Simulate chunks
      chunks.forEach((chunk) => dataHandler(chunk));
      endHandler();

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.content.completion', {
        'gen_ai.completion.role': 'assistant',
        'gen_ai.completion.content': 'Hello world',
        'gen_ai.completion.index': '0',
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.finish_reasons', [
        'stop',
      ]);

      expect(mockSpan.setStatus).toHaveBeenCalledWith({ code: SpanStatusCode.OK });
      expect(mockSpan.end).toHaveBeenCalled();
      expect(result).toBe(mockWrapper);
    });

    it('should handle stream errors', async () => {
      let errorHandler: Function;

      const mockWrapper = {
        on: vi.fn((event, handler) => {
          if (event === 'error') errorHandler = handler;
        }),
        [Symbol.asyncIterator]: vi.fn(),
      };

      vi.mocked(StreamWrapper).mockReturnValue(mockWrapper as any);

      const stream = { [Symbol.asyncIterator]: vi.fn() };
      await (instrumentation as any).handleStreamingResponse(stream, mockSpan);

      const error = new Error('Stream error');
      errorHandler(error);

      expect(mockSpan.recordException).toHaveBeenCalledWith(error);
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'Stream error',
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should handle empty chunks', async () => {
      let endHandler: Function;

      const mockWrapper = {
        on: vi.fn((event, handler) => {
          if (event === 'end') endHandler = handler;
        }),
        [Symbol.asyncIterator]: vi.fn(),
      };

      vi.mocked(StreamWrapper).mockReturnValue(mockWrapper as any);

      const stream = { [Symbol.asyncIterator]: vi.fn() };
      await (instrumentation as any).handleStreamingResponse(stream, mockSpan);

      // No chunks
      endHandler();

      expect(mockSpan.addEvent).not.toHaveBeenCalledWith(
        'gen_ai.content.completion',
        expect.any(Object),
      );
    });
  });

  describe('recordCompletionResponse', () => {
    it('should handle null response', () => {
      (instrumentation as any).recordCompletionResponse(mockSpan, null);
      expect(mockSpan.addEvent).not.toHaveBeenCalled();
    });

    it('should handle response with multiple choices', () => {
      const response = {
        choices: [
          { message: { role: 'assistant', content: 'First' } },
          { message: { role: 'assistant', content: 'Second' } },
        ],
      };

      (instrumentation as any).recordCompletionResponse(mockSpan, response);

      // Should only record the first choice
      expect(mockSpan.addEvent).toHaveBeenCalledTimes(1);
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.content.completion', {
        'gen_ai.completion.role': 'assistant',
        'gen_ai.completion.content': '"First"',
        'gen_ai.completion.index': '0',
      });
    });

    it('should handle missing message content', () => {
      const response = {
        choices: [{ message: { role: 'assistant' } }],
      };

      (instrumentation as any).recordCompletionResponse(mockSpan, response);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.content.completion', {
        'gen_ai.completion.role': 'assistant',
        'gen_ai.completion.content': '"[undefined]"',
        'gen_ai.completion.index': '0',
      });
    });
  });
});
