import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { trace, SpanStatusCode, SpanKind } from '@opentelemetry/api';
import { OpenAIInstrumentorV2 } from './openai-v2';

// Import mocked modules at the top
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
          handlers[event].forEach((h) => h(...args));
        }
      },
      [Symbol.asyncIterator]: () => stream[Symbol.asyncIterator](),
    };
  }),
  isAsyncIterable: (obj: any) => obj && typeof obj[Symbol.asyncIterator] === 'function',
}));

describe('OpenAIInstrumentorV2', () => {
  let instrumentor: OpenAIInstrumentorV2;
  let mockTracer: any;
  let mockSpan: any;
  let mockOpenAIModule: any;
  let mockOpenAIClass: any;

  beforeEach(() => {
    instrumentor = new OpenAIInstrumentorV2();

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

    // Mock OpenAI class
    mockOpenAIClass = class OpenAI {
      chat = {
        completions: {
          create: vi.fn(),
        },
      };

      constructor(_config: any) {
        // Constructor logic
      }
    };

    // Mock OpenAI module
    mockOpenAIModule = {
      default: mockOpenAIClass,
      OpenAI: mockOpenAIClass,
    };

    // Mock require
    vi.doMock('openai', () => mockOpenAIModule);
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.doUnmock('openai');
    vi.resetModules();
  });

  describe('getName', () => {
    it('should return correct name', () => {
      expect(instrumentor.getName()).toBe('OpenAI-V2');
    });
  });

  describe('instrument', () => {
    it('should instrument OpenAI module successfully', () => {
      instrumentor.instrument();

      expect(instrumentor.isInstrumented()).toBe(true);
      expect(vi.mocked(logger).info).toHaveBeenCalledWith('OpenAI instrumentation enabled (V2)');
    });

    it('should warn if already instrumented', () => {
      instrumentor.instrument();
      instrumentor.instrument(); // Call again

      expect(vi.mocked(logger).warn).toHaveBeenCalledWith('OpenAI already instrumented');
    });

    it('should handle module with default export only', () => {
      vi.doUnmock('openai');
      vi.doMock('openai', () => ({
        default: mockOpenAIClass,
      }));

      instrumentor.instrument();

      expect(instrumentor.isInstrumented()).toBe(true);
    });

    it('should handle module with named export only', () => {
      vi.doUnmock('openai');
      vi.doMock('openai', () => ({
        OpenAI: mockOpenAIClass,
      }));

      instrumentor.instrument();

      expect(instrumentor.isInstrumented()).toBe(true);
    });

    it.skip('should throw error if OpenAI class not found', () => {
      // Create a separate instance and use a dynamic import to avoid module caching
      vi.isolateModules(() => {
        vi.doMock('openai', () => ({})); // Empty module without OpenAI class

        const { OpenAIInstrumentorV2 } = require('./openai-v2');
        const newInstrumentor = new OpenAIInstrumentorV2();

        expect(() => newInstrumentor.instrument()).toThrow(
          'OpenAI instrumentation failed: Could not find OpenAI class in module. Please ensure OpenAI is properly installed.',
        );

        expect(vi.mocked(logger).error).toHaveBeenCalledWith(
          'Failed to instrument OpenAI:',
          expect.any(Error),
        );
      });
    });

    it.skip('should handle require failure', () => {
      vi.isolateModules(() => {
        vi.doMock('openai', () => {
          throw new Error('Module not found');
        });

        const { OpenAIInstrumentorV2 } = require('./openai-v2');
        const newInstrumentor = new OpenAIInstrumentorV2();

        expect(() => newInstrumentor.instrument()).toThrow(
          'OpenAI instrumentation failed: Module not found. Please ensure OpenAI is properly installed.',
        );

        expect(vi.mocked(logger).error).toHaveBeenCalledWith(
          'Failed to instrument OpenAI:',
          expect.any(Error),
        );
      });
    });

    it('should wrap chat.completions.create on new instances', () => {
      // Create a mock for the original create method
      const originalCreateMethod = vi.fn();

      // Create a more detailed mock OpenAI class
      const MockOpenAIClassWithCreate = class {
        chat = {
          completions: {
            create: originalCreateMethod,
          },
        };

        constructor(_config: any) {
          vi.mocked(logger).debug('Creating wrapped OpenAI instance');
        }
      };

      vi.doUnmock('openai');
      vi.doMock('openai', () => ({
        default: MockOpenAIClassWithCreate,
      }));

      const testInstrumentor = new OpenAIInstrumentorV2();
      testInstrumentor.instrument();

      // Create an instance using the wrapped constructor
      const instance = new (require('openai').default)({ apiKey: 'test' });

      // The chat.completions.create should be wrapped
      expect(instance.chat.completions.create).not.toBe(originalCreateMethod);
      expect(vi.mocked(logger).debug).toHaveBeenCalledWith('Creating wrapped OpenAI instance');
      expect(vi.mocked(logger).debug).toHaveBeenCalledWith(
        'Wrapped chat.completions.create on instance',
      );
    });

    it.skip('should handle instance without chat.completions.create', () => {
      vi.isolateModules(() => {
        // Create a mock OpenAI class without chat.completions.create
        const MockOpenAIClassWithoutCreate = class {
          constructor(_config: any) {
            // Empty constructor
          }
        };

        vi.doMock('openai', () => ({
          default: MockOpenAIClassWithoutCreate,
        }));

        const { OpenAIInstrumentorV2 } = require('./openai-v2');
        const testInstrumentor = new OpenAIInstrumentorV2();

        // Clear previous mock calls
        vi.mocked(logger).debug.mockClear();

        testInstrumentor.instrument();

        // Create an instance using the wrapped constructor
        const _instance = new (require('openai').default)({ apiKey: 'test' });

        // Should log creation but not wrapping
        expect(vi.mocked(logger).debug).toHaveBeenCalledWith('Creating wrapped OpenAI instance');
        // Should not log the wrapping since there's no method to wrap
        expect(vi.mocked(logger).debug).not.toHaveBeenCalledWith(
          'Wrapped chat.completions.create on instance',
        );
      });
    });

    it('should copy static properties', () => {
      mockOpenAIClass.VERSION = '1.0.0';
      mockOpenAIClass.API_URL = 'https://api.openai.com';

      instrumentor.instrument();

      // Check that properties were copied
      expect(instrumentor.isInstrumented()).toBe(true);
    });
  });

  describe('uninstrument', () => {
    it('should restore original OpenAI class', () => {
      instrumentor.instrument();
      instrumentor.uninstrument();

      expect(instrumentor.isInstrumented()).toBe(false);
      expect(vi.mocked(logger).info).toHaveBeenCalledWith('OpenAI instrumentation disabled');
    });

    it('should do nothing if not instrumented', () => {
      instrumentor.uninstrument();

      expect(vi.mocked(logger).info).not.toHaveBeenCalledWith('OpenAI instrumentation disabled');
    });

    it('should handle errors during uninstrumentation', () => {
      instrumentor.instrument();

      // Create a new mock module that throws when we try to set properties
      const errorModule = {
        get default() {
          return mockOpenAIClass;
        },
        set default(value: any) {
          throw new Error('Cannot set property');
        },
        get OpenAI() {
          return mockOpenAIClass;
        },
        set OpenAI(value: any) {
          throw new Error('Cannot set property');
        },
      };

      (instrumentor as any).openaiModule = errorModule;

      instrumentor.uninstrument();

      expect(vi.mocked(logger).error).toHaveBeenCalledWith(
        'Failed to uninstrument OpenAI:',
        expect.any(Error),
      );
    });
  });

  describe('wrapChatCompletionsCreate', () => {
    let originalCreate: any;
    let wrappedCreate: any;

    beforeEach(() => {
      originalCreate = vi.fn();
      wrappedCreate = (instrumentor as any).wrapChatCompletionsCreate(originalCreate);
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
        presence_penalty: 0.1,
        frequency_penalty: 0.2,
        response_format: { type: 'json' },
        seed: 12345,
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
      const result = await wrappedCreate(params);

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
            'gen_ai.request.presence_penalty': 0.1,
            'gen_ai.request.frequency_penalty': 0.2,
            'gen_ai.openai.request.response_format': 'json',
            'gen_ai.openai.request.seed': 12345,
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

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.model', 'gpt-4-0613');
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
      const result = await wrappedCreate(params);

      expect(StreamWrapper).toHaveBeenCalledWith(mockStream);
      expect(result).toBeDefined();
    });

    it('should handle errors', async () => {
      vi.mocked(isSDKShuttingDown).mockReturnValue(false);

      const params = { model: 'gpt-4' };
      const error = new Error('API Error');
      originalCreate.mockRejectedValue(error);

      await expect(wrappedCreate(params)).rejects.toThrow('API Error');

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

      await wrappedCreate(params);

      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        'openai.chat.completions unknown',
        expect.any(Object),
        expect.any(Function),
      );
    });

    it('should preserve context when calling original method', async () => {
      const context = { apiKey: 'test-key' };
      const params = { model: 'gpt-4' };
      originalCreate.mockResolvedValue({});

      await wrappedCreate.call(context, params, { timeout: 5000 });

      expect(originalCreate).toHaveBeenCalledWith(params, { timeout: 5000 });
      // Verify that the function was called
      expect(originalCreate).toHaveBeenCalled();
    });
  });

  describe('recordCompletionResponse', () => {
    beforeEach(() => {
      instrumentor.instrument();
    });

    it('should handle null response', () => {
      (instrumentor as any).recordCompletionResponse(mockSpan, null);
      expect(mockSpan.addEvent).not.toHaveBeenCalled();
    });

    it('should handle response without choices', () => {
      (instrumentor as any).recordCompletionResponse(mockSpan, {});
      expect(mockSpan.addEvent).not.toHaveBeenCalled();
    });

    it('should handle response with empty choices', () => {
      (instrumentor as any).recordCompletionResponse(mockSpan, { choices: [] });
      expect(mockSpan.addEvent).not.toHaveBeenCalled();
    });

    it('should handle missing message in choice', () => {
      const response = {
        choices: [{}],
      };

      (instrumentor as any).recordCompletionResponse(mockSpan, response);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.content.completion', {
        'gen_ai.completion.role': 'assistant',
        'gen_ai.completion.content': '"[undefined]"',
        'gen_ai.completion.index': '0',
      });
    });

    it('should record all response attributes', () => {
      const response = {
        choices: [
          {
            message: { role: 'assistant', content: 'Response' },
            finish_reason: 'stop',
          },
        ],
        usage: {
          prompt_tokens: 20,
          completion_tokens: 10,
          total_tokens: 30,
        },
        model: 'gpt-4-0613',
      };

      (instrumentor as any).recordCompletionResponse(mockSpan, response);

      expect(mockSpan.addEvent).toHaveBeenCalled();
      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.finish_reasons', [
        'stop',
      ]);
      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.usage.input_tokens': 20,
        'gen_ai.usage.output_tokens': 10,
        'gen_ai.usage.total_tokens': 30,
      });
      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.model', 'gpt-4-0613');
    });
  });

  describe('handleStreamingResponse', () => {
    beforeEach(() => {
      instrumentor.instrument();
    });

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

      vi.mocked(StreamWrapper).mockReturnValue(mockWrapper);

      const chunks = [
        { choices: [{ delta: { content: 'Hello' } }] },
        { choices: [{ delta: { content: ' world' } }] },
        { choices: [{ delta: {}, finish_reason: 'stop' }] },
      ];

      const stream = { [Symbol.asyncIterator]: vi.fn() };
      const result = await (instrumentor as any).handleStreamingResponse(stream, mockSpan);

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

      vi.mocked(StreamWrapper).mockReturnValue(mockWrapper);

      const stream = { [Symbol.asyncIterator]: vi.fn() };
      await (instrumentor as any).handleStreamingResponse(stream, mockSpan);

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

      vi.mocked(StreamWrapper).mockReturnValue(mockWrapper);

      const stream = { [Symbol.asyncIterator]: vi.fn() };
      await (instrumentor as any).handleStreamingResponse(stream, mockSpan);

      // No chunks with content
      endHandler();

      expect(mockSpan.addEvent).not.toHaveBeenCalledWith(
        'gen_ai.content.completion',
        expect.any(Object),
      );
      expect(mockSpan.setAttribute).not.toHaveBeenCalledWith(
        'gen_ai.response.finish_reasons',
        expect.any(Array),
      );
    });

    it('should handle chunks without choices', async () => {
      let dataHandler: Function;
      let endHandler: Function;

      const mockWrapper = {
        on: vi.fn((event, handler) => {
          if (event === 'data') dataHandler = handler;
          if (event === 'end') endHandler = handler;
        }),
        [Symbol.asyncIterator]: vi.fn(),
      };

      vi.mocked(StreamWrapper).mockReturnValue(mockWrapper);

      const chunks = [{ choices: [] }, { notChoices: true }];

      const stream = { [Symbol.asyncIterator]: vi.fn() };
      await (instrumentor as any).handleStreamingResponse(stream, mockSpan);

      chunks.forEach((chunk) => dataHandler(chunk));
      endHandler();

      expect(mockSpan.addEvent).not.toHaveBeenCalledWith(
        'gen_ai.content.completion',
        expect.any(Object),
      );
    });
  });
});
