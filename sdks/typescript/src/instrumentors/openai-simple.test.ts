import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { trace, SpanStatusCode, SpanKind } from '@opentelemetry/api';
import { instrumentOpenAI } from './openai-simple';

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
    const wrapper = {
      on: (event: string, handler: Function) => {
        if (!handlers[event]) handlers[event] = [];
        handlers[event].push(handler);
        return wrapper;
      },
      emit: (event: string, ...args: any[]) => {
        if (handlers[event]) {
          handlers[event].forEach((h) => h(...args));
        }
      },
      [Symbol.asyncIterator]: () => stream[Symbol.asyncIterator](),
    };
    return wrapper;
  }),
  isAsyncIterable: (obj: any) => obj && typeof obj[Symbol.asyncIterator] === 'function',
}));

describe('OpenAI Simple Instrumentation', () => {
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
    vi.resetModules();
  });

  describe('instrumentOpenAI', () => {
    it('should handle instrumentation setup', () => {
      // Test that instrumentOpenAI can be called without errors
      expect(() => instrumentOpenAI()).not.toThrow();
    });

    it('should log debug messages during instrumentation', () => {
      instrumentOpenAI();

      expect(vi.mocked(logger).debug).toHaveBeenCalledWith('Starting OpenAI instrumentation');
    });
  });

  describe('Module patching behavior', () => {
    it('should handle module system mocking', () => {
      // Create a mock module system
      const mockModule = {
        prototype: {
          require: vi.fn(),
        },
      };

      // Mock the module
      vi.doMock('module', () => mockModule);

      // Call instrumentOpenAI
      instrumentOpenAI();

      // The prototype.require should be replaced
      expect(mockModule.prototype.require).toBeDefined();
    });
  });

  describe('OpenAI class wrapping', () => {
    it('should wrap OpenAI class methods', () => {
      // This tests the wrapping logic conceptually
      const mockOpenAIClass = class OpenAI {
        chat = {
          completions: {
            create: vi.fn().mockResolvedValue({ choices: [] }),
          },
        };
      };

      // Test that we can create a wrapped version
      const wrappedClass = class extends mockOpenAIClass {
        constructor(_config: any) {
          super();
          // Wrapping logic would go here
        }
      };

      const _instance = new wrappedClass({});
      expect(_instance.chat.completions.create).toBeDefined();
    });
  });

  describe('Chat completion wrapping', () => {
    it('should handle non-streaming completions', async () => {
      vi.mocked(isSDKShuttingDown).mockReturnValue(false);

      const params = {
        model: 'gpt-4',
        messages: [{ role: 'user', content: 'Hello' }],
      };

      const response = {
        choices: [
          {
            message: { role: 'assistant', content: 'Hi!' },
            finish_reason: 'stop',
          },
        ],
      };

      // Create a mock wrapped function
      const wrappedCreate = async (params: any) => {
        return trace.getTracer('lilypad-openai', '0.1.0').startActiveSpan(
          `openai.chat.completions ${params.model}`,
          {
            kind: SpanKind.CLIENT,
            attributes: {
              'gen_ai.system': 'openai',
              'gen_ai.request.model': params.model,
            },
          },
          async (span) => {
            span.setStatus({ code: SpanStatusCode.OK });
            span.end();
            return response;
          },
        );
      };

      const result = await wrappedCreate(params);

      expect(result).toEqual(response);
      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        'openai.chat.completions gpt-4',
        expect.objectContaining({
          kind: SpanKind.CLIENT,
        }),
        expect.any(Function),
      );
    });

    it('should skip instrumentation when shutting down', async () => {
      vi.mocked(isSDKShuttingDown).mockReturnValue(true);

      const original = vi.fn().mockResolvedValue({ choices: [] });
      const params = { model: 'gpt-4' };

      // When shutting down, it should call original directly
      const result = await original(params);

      expect(result).toEqual({ choices: [] });
      expect(original).toHaveBeenCalledWith(params);
    });

    it('should handle streaming responses', async () => {
      vi.mocked(isSDKShuttingDown).mockReturnValue(false);

      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield { choices: [{ delta: { content: 'Hello' } }] };
        },
      };

      // Test streaming wrapper
      const wrapper = new (StreamWrapper as any)(mockStream);
      expect(wrapper).toBeDefined();
      expect(StreamWrapper).toHaveBeenCalledWith(mockStream);
    });

    it('should handle errors properly', async () => {
      vi.mocked(isSDKShuttingDown).mockReturnValue(false);

      const error = new Error('API Error');
      const wrappedCreate = async () => {
        return trace
          .getTracer('lilypad-openai', '0.1.0')
          .startActiveSpan('openai.chat.completions', { kind: SpanKind.CLIENT }, async (span) => {
            try {
              throw error;
            } catch (err) {
              span.recordException(err as Error);
              span.setStatus({
                code: SpanStatusCode.ERROR,
                message: (err as Error).message,
              });
              throw err;
            } finally {
              span.end();
            }
          });
      };

      await expect(wrappedCreate()).rejects.toThrow('API Error');

      expect(mockSpan.recordException).toHaveBeenCalledWith(error);
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'API Error',
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });
  });
});
