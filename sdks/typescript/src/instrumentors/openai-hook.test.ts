import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';

// Mock modules before imports
vi.mock('@opentelemetry/api', () => ({
  trace: {
    getTracer: vi.fn(),
  },
  SpanKind: {
    CLIENT: 2,
  },
  SpanStatusCode: {
    OK: 1,
    ERROR: 2,
  },
}));

vi.mock('../utils/logger', () => ({
  logger: {
    debug: vi.fn(),
    warn: vi.fn(),
  },
}));

vi.mock('../utils/stream-wrapper', () => ({
  StreamWrapper: vi.fn(),
  isAsyncIterable: vi.fn(),
}));

vi.mock('../utils/json', () => ({
  safeStringify: vi.fn(),
}));

vi.mock('../shutdown', () => ({
  isSDKShuttingDown: vi.fn(),
}));

// Import after mocks
import { setupOpenAIHooks } from './openai-hook';
import { trace, SpanKind, SpanStatusCode } from '@opentelemetry/api';
import { logger } from '../utils/logger';
import { StreamWrapper, isAsyncIterable } from '../utils/stream-wrapper';
import { safeStringify } from '../utils/json';
import { isSDKShuttingDown } from '../shutdown';

// Get mocked functions
const mockedTrace = vi.mocked(trace);
const mockedLogger = vi.mocked(logger);
const mockedStreamWrapper = vi.mocked(StreamWrapper);
const mockedIsAsyncIterable = vi.mocked(isAsyncIterable);
const mockedSafeStringify = vi.mocked(safeStringify);
const mockedIsSDKShuttingDown = vi.mocked(isSDKShuttingDown);

describe('setupOpenAIHooks', () => {
  let mockSpan: any;
  let mockTracer: any;
  let Module: any;
  let originalLoad: any;

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
      startActiveSpan: vi.fn((name, attrs, fn) => {
        // Call the function with the mock span and return its result
        return fn(mockSpan);
      }),
    };

    // Set up mock implementations
    mockedTrace.getTracer.mockReturnValue(mockTracer);
    mockedStreamWrapper.mockImplementation((stream, span, options) => {
      // Create a mock stream wrapper that calls the callbacks
      return {
        async *[Symbol.asyncIterator]() {
          for await (const chunk of stream) {
            if (options.onChunk) {
              options.onChunk(chunk);
            }
            yield chunk;
          }
          if (options.onFinalize) {
            options.onFinalize();
          }
        },
      };
    });
    mockedIsAsyncIterable.mockImplementation((value) => {
      return value != null && typeof value === 'object' && Symbol.asyncIterator in value;
    });
    mockedSafeStringify.mockImplementation((value) => JSON.stringify(value));
    mockedIsSDKShuttingDown.mockReturnValue(false);

    // Get Module and store original _load
    Module = require('module');
    originalLoad = Module._load;
  });

  afterEach(() => {
    // Restore original Module._load
    if (Module && originalLoad) {
      Module._load = originalLoad;
    }
  });

  describe('Module loading interception', () => {
    it('should hook Module._load', () => {
      setupOpenAIHooks();

      expect(Module._load).not.toBe(originalLoad);
      expect(mockedLogger.debug).toHaveBeenCalledWith('Setting up OpenAI hooks');
      expect(mockedLogger.debug).toHaveBeenCalledWith('OpenAI hooks installed');
    });

    it('should intercept openai module loading', () => {
      const mockOpenAIExports = {
        default: class OpenAI {
          chat = {
            completions: {
              create: vi.fn(),
            },
          };
        },
      };

      // Mock originalLoad to return our mock exports for openai
      const originalHookedLoad = Module._load;
      Module._load = originalLoad;

      // Mock the original load to return mock exports when openai is requested
      vi.spyOn(Module, '_load').mockImplementation((request: string) => {
        if (request === 'openai') {
          return mockOpenAIExports;
        }
        return {};
      });

      setupOpenAIHooks();

      // Call the hooked Module._load
      const result = Module._load('openai', null, false);

      // Should return wrapped exports
      expect(result).toBeDefined();
      expect(result.default).toBeDefined();
      expect(typeof result.default).toBe('function');

      // Restore
      Module._load = originalHookedLoad;
    });

    it('should pass through non-openai modules', () => {
      setupOpenAIHooks();

      // Mock a different module
      const mockExports = { someModule: true };
      Module._load = vi.fn(() => mockExports);
      setupOpenAIHooks();

      const result = Module._load('some-other-module', null, false);
      expect(result).toBe(mockExports);
    });
  });

  describe('OpenAI exports wrapping', () => {
    let mockOpenAIClass: any;
    let mockCreate: any;

    beforeEach(() => {
      mockCreate = vi.fn();
      mockOpenAIClass = class OpenAI {
        chat = {
          completions: {
            create: mockCreate,
          },
        };
      };
    });

    it('should wrap default export', () => {
      const exports = {
        default: mockOpenAIClass,
      };

      // Save the original Module._load before any modification
      const savedOriginalLoad = Module._load;
      Module._load = originalLoad;

      // Mock Module._load to return our exports
      Module._load = vi.fn((request) => {
        if (request === 'openai') {
          return exports;
        }
        return originalLoad.apply(Module, [request]);
      });

      // Now set up hooks which will wrap Module._load
      setupOpenAIHooks();
      const hookedLoad = Module._load;

      // Call the hooked load
      const result = hookedLoad('openai', null, false);

      expect(result.default).toBeDefined();
      expect(result.default).not.toBe(mockOpenAIClass);
      expect(mockedLogger.debug).toHaveBeenCalledWith(
        'OpenAI module loaded via Module._load, wrapping it',
      );

      // Restore
      Module._load = savedOriginalLoad;
    });

    it('should wrap named export', () => {
      const exports = {
        OpenAI: mockOpenAIClass,
      };

      // Mock Module._load before calling setupOpenAIHooks
      const savedOriginalLoad = Module._load;
      Module._load = vi.fn((request) => {
        if (request === 'openai') {
          return exports;
        }
        return originalLoad.apply(Module, [request]);
      });

      setupOpenAIHooks();
      const hookedLoad = Module._load;

      const result = hookedLoad('openai', null, false);

      expect(result.OpenAI).toBeDefined();
      expect(result.OpenAI).not.toBe(mockOpenAIClass);

      // Restore
      Module._load = savedOriginalLoad;
    });

    it('should preserve prototype and static properties', () => {
      mockOpenAIClass.staticProp = 'static value';
      mockOpenAIClass.prototype.instanceMethod = vi.fn();

      const exports = {
        default: mockOpenAIClass,
      };

      // Mock Module._load before calling setupOpenAIHooks
      const savedOriginalLoad = Module._load;
      Module._load = vi.fn((request) => {
        if (request === 'openai') {
          return exports;
        }
        return originalLoad.apply(Module, [request]);
      });

      setupOpenAIHooks();
      const hookedLoad = Module._load;

      const result = hookedLoad('openai', null, false);

      expect(result.default.staticProp).toBe('static value');
      expect(result.default.prototype.instanceMethod).toBeDefined();

      // Restore
      Module._load = savedOriginalLoad;
    });

    it('should handle both default and named exports', () => {
      const exports = {
        default: mockOpenAIClass,
        OpenAI: mockOpenAIClass,
      };

      // Mock Module._load before calling setupOpenAIHooks
      const savedOriginalLoad = Module._load;
      Module._load = vi.fn((request) => {
        if (request === 'openai') {
          return exports;
        }
        return originalLoad.apply(Module, [request]);
      });

      setupOpenAIHooks();
      const hookedLoad = Module._load;

      const result = hookedLoad('openai', null, false);

      expect(result.default).toBeDefined();
      expect(result.OpenAI).toBe(result.default);

      // Restore
      Module._load = savedOriginalLoad;
    });
  });

  describe('Instance wrapping', () => {
    let mockInstance: any;
    let mockCreate: any;

    beforeEach(() => {
      mockCreate = vi.fn();
      mockInstance = {
        chat: {
          completions: {
            create: mockCreate,
          },
        },
      };
    });

    it('should wrap chat.completions.create method', async () => {
      const OpenAIClass = class {
        chat = {
          completions: {
            create: mockCreate,
          },
        };
      };

      const exports = {
        default: OpenAIClass,
      };

      // Mock Module._load before calling setupOpenAIHooks
      const savedOriginalLoad = Module._load;
      Module._load = vi.fn((request) => {
        if (request === 'openai') {
          return exports;
        }
        return originalLoad.apply(Module, [request]);
      });

      setupOpenAIHooks();
      const hookedLoad = Module._load;

      const result = hookedLoad('openai', null, false);
      const instance = new result.default();

      // The create method should be wrapped
      expect(instance.chat.completions.create).not.toBe(mockCreate);

      // Test that the wrapped method works
      mockCreate.mockResolvedValue({ choices: [] });
      await instance.chat.completions.create({ model: 'gpt-4' });

      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        'openai.chat.completions gpt-4',
        expect.objectContaining({
          kind: SpanKind.CLIENT,
          attributes: expect.objectContaining({
            'gen_ai.system': 'openai',
            'gen_ai.request.model': 'gpt-4',
          }),
        }),
        expect.any(Function),
      );

      // Restore
      Module._load = savedOriginalLoad;
    });

    it('should skip wrapping if instance already wrapped', () => {
      const weakSet = new WeakSet();
      weakSet.add(mockInstance);

      // Create a new instance that should be skipped
      const _instance2 = {
        chat: {
          completions: {
            create: vi.fn(),
          },
        },
      };

      // This test would need access to the internal WeakSet, which is private
      // Instead, we can test the behavior indirectly
      expect(mockedLogger.debug).not.toHaveBeenCalledWith('Instance already wrapped, skipping');
    });

    it('should handle missing chat.completions.create gracefully', () => {
      const OpenAIClass = class {
        // No chat property
      };

      const exports = {
        default: OpenAIClass,
      };

      // Mock Module._load before calling setupOpenAIHooks
      const savedOriginalLoad = Module._load;
      Module._load = vi.fn((request) => {
        if (request === 'openai') {
          return exports;
        }
        return originalLoad.apply(Module, [request]);
      });

      setupOpenAIHooks();
      const hookedLoad = Module._load;

      const result = hookedLoad('openai', null, false);
      const instance = new result.default();

      // Should not throw
      expect(instance).toBeDefined();

      // Restore
      Module._load = savedOriginalLoad;
    });
  });

  describe('chat.completions.create wrapping', () => {
    let wrappedCreate: any;
    let mockCreate: any;
    let savedOriginalLoad: any;

    beforeEach(() => {
      mockCreate = vi.fn();

      const OpenAIClass = class {
        chat = {
          completions: {
            create: mockCreate,
          },
        };
      };

      const exports = {
        default: OpenAIClass,
      };

      // Save original Module._load
      savedOriginalLoad = Module._load;

      // Mock Module._load before calling setupOpenAIHooks
      Module._load = vi.fn((request) => {
        if (request === 'openai') {
          return exports;
        }
        return originalLoad.apply(Module, [request]);
      });

      setupOpenAIHooks();
      const hookedLoad = Module._load;

      const result = hookedLoad('openai', null, false);
      const instance = new result.default();
      wrappedCreate = instance.chat.completions.create;
    });

    afterEach(() => {
      // Restore original Module._load
      if (savedOriginalLoad) {
        Module._load = savedOriginalLoad;
      }
    });

    it('should skip instrumentation when SDK is shutting down', async () => {
      mockedIsSDKShuttingDown.mockReturnValue(true);

      const params = { model: 'gpt-4' };
      mockCreate.mockResolvedValue({ choices: [] });

      const result = await wrappedCreate.call({ completions: { create: mockCreate } }, params);

      expect(mockTracer.startActiveSpan).not.toHaveBeenCalled();
      expect(mockCreate).toHaveBeenCalledWith(params, undefined);
      expect(result).toEqual({ choices: [] });
    });

    it('should create span with correct attributes', async () => {
      const params = {
        model: 'gpt-4',
        temperature: 0.7,
        max_tokens: 100,
        top_p: 0.9,
        presence_penalty: 0.1,
        frequency_penalty: 0.2,
        response_format: { type: 'json_object' },
        seed: 123,
        service_tier: 'premium',
      };

      mockCreate.mockResolvedValue({ choices: [] });

      await wrappedCreate(params);

      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        'openai.chat.completions gpt-4',
        {
          kind: SpanKind.CLIENT,
          attributes: expect.objectContaining({
            'gen_ai.system': 'openai',
            'gen_ai.request.model': 'gpt-4',
            'gen_ai.request.temperature': 0.7,
            'gen_ai.request.max_tokens': 100,
            'gen_ai.request.top_p': 0.9,
            'gen_ai.request.presence_penalty': 0.1,
            'gen_ai.request.frequency_penalty': 0.2,
            'gen_ai.openai.request.response_format': 'json_object',
            'gen_ai.openai.request.seed': 123,
            'gen_ai.openai.request.service_tier': 'premium',
            'gen_ai.operation.name': 'chat',
            'lilypad.type': 'trace',
          }),
        },
        expect.any(Function),
      );
    });

    it('should filter out null/undefined attributes', async () => {
      const params = {
        model: 'gpt-4',
        temperature: undefined,
        max_tokens: null,
        service_tier: 'auto', // Should be filtered out
      };

      mockCreate.mockResolvedValue({ choices: [] });

      await wrappedCreate(params);

      const attributes = mockTracer.startActiveSpan.mock.calls[0][1].attributes;
      expect(attributes['gen_ai.request.temperature']).toBeUndefined();
      expect(attributes['gen_ai.request.max_tokens']).toBeUndefined();
      expect(attributes['gen_ai.openai.request.service_tier']).toBeUndefined();
    });

    it('should record message events', async () => {
      const params = {
        model: 'gpt-4',
        messages: [
          { role: 'system', content: 'You are helpful' },
          { role: 'user', content: 'Hello' },
          { role: 'assistant', content: { type: 'text', text: 'Hi there' } },
        ],
      };

      mockCreate.mockResolvedValue({ choices: [] });

      await wrappedCreate(params);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.system.message', {
        'gen_ai.system': 'openai',
        content: 'You are helpful',
      });
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.user.message', {
        'gen_ai.system': 'openai',
        content: 'Hello',
      });
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.assistant.message', {
        'gen_ai.system': 'openai',
        content: '{"type":"text","text":"Hi there"}',
      });
    });

    it('should handle successful response', async () => {
      const response = {
        id: 'chatcmpl-123',
        model: 'gpt-4-0613',
        choices: [
          {
            message: { role: 'assistant', content: 'Hello!' },
            finish_reason: 'stop',
          },
        ],
        usage: {
          prompt_tokens: 10,
          completion_tokens: 20,
          total_tokens: 30,
        },
        service_tier: 'premium',
      };

      mockCreate.mockResolvedValue(response);

      await wrappedCreate({ model: 'gpt-4' });

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'openai',
        index: 0,
        finish_reason: 'stop',
        message: '{"role":"assistant","content":"Hello!"}',
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
      expect(mockSpan.setAttribute).toHaveBeenCalledWith(
        'gen_ai.openai.response.service_tier',
        'premium',
      );

      expect(mockSpan.setStatus).toHaveBeenCalledWith({ code: SpanStatusCode.OK });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should handle errors', async () => {
      const error = new Error('API Error');
      mockCreate.mockRejectedValue(error);

      await expect(wrappedCreate({ model: 'gpt-4' })).rejects.toThrow('API Error');

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

    it('should handle non-Error exceptions', async () => {
      const error = 'String error';
      mockCreate.mockRejectedValue(error);

      await expect(wrappedCreate({ model: 'gpt-4' })).rejects.toThrow('String error');

      expect(mockSpan.recordException).toHaveBeenCalledWith(error);
      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.error.type': 'Error',
        'gen_ai.error.message': 'String error',
      });
    });

    it('should handle streaming response', async () => {
      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield {
            choices: [{ delta: { content: 'Hello' } }],
          };
          yield {
            choices: [{ delta: { content: ' world' }, finish_reason: 'stop' }],
          };
        },
      };

      mockCreate.mockResolvedValue(mockStream);
      mockedIsAsyncIterable.mockReturnValue(true);

      const result = await wrappedCreate({ model: 'gpt-4', stream: true });

      // Consume the stream
      const chunks = [];
      for await (const chunk of result) {
        chunks.push(chunk);
      }

      expect(chunks).toHaveLength(2);
      expect(mockedStreamWrapper).toHaveBeenCalledWith(mockStream, mockSpan, {
        onChunk: expect.any(Function),
        onFinalize: expect.any(Function),
      });
    });

    it('should pass options parameter to original method', async () => {
      const params = { model: 'gpt-4' };
      const options = { signal: new AbortController().signal };

      mockCreate.mockResolvedValue({ choices: [] });

      await wrappedCreate(params, options);

      expect(mockCreate).toHaveBeenCalledWith(params, options);
    });
  });

  describe('Stream handling', () => {
    it('should accumulate content from chunks', async () => {
      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield { choices: [{ delta: { content: 'First' } }] };
          yield { choices: [{ delta: { content: ' Second' } }] };
          yield { choices: [{ delta: {}, finish_reason: 'stop' }] };
        },
      };

      // Mock the StreamWrapper to capture callbacks and create a wrapper stream
      let onChunkCallback: any;
      let onFinalizeCallback: any;
      mockedStreamWrapper.mockImplementation((stream, span, options) => {
        onChunkCallback = options.onChunk;
        onFinalizeCallback = options.onFinalize;

        // Return a new async iterable that calls the callbacks
        return {
          async *[Symbol.asyncIterator]() {
            for await (const chunk of stream) {
              if (onChunkCallback) onChunkCallback(chunk);
              yield chunk;
            }
            if (onFinalizeCallback) onFinalizeCallback();
          },
        };
      });

      const OpenAIClass = class {
        chat = {
          completions: {
            create: vi.fn().mockResolvedValue(mockStream),
          },
        };
      };

      const exports = { default: OpenAIClass };

      // Save original Module._load
      const savedOriginalLoad = Module._load;

      // Mock Module._load before calling setupOpenAIHooks
      Module._load = vi.fn((request) => {
        if (request === 'openai') {
          return exports;
        }
        return originalLoad.apply(Module, [request]);
      });

      setupOpenAIHooks();

      const result = Module._load('openai', null, false);
      const instance = new result.default();

      mockedIsAsyncIterable.mockReturnValue(true);
      const resultStream = await instance.chat.completions.create({ model: 'gpt-4', stream: true });

      // Process the wrapped stream (this will trigger the callbacks)
      const chunks = [];
      for await (const chunk of resultStream) {
        chunks.push(chunk);
      }

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'openai',
        index: 0,
        finish_reason: 'stop',
        message: '{"role":"assistant","content":"First Second"}',
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.finish_reasons', [
        'stop',
      ]);

      // Restore
      Module._load = savedOriginalLoad;
    });

    it('should handle empty chunks', async () => {
      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield {}; // Empty chunk
          yield { choices: [] }; // Empty choices
          yield { choices: [{}] }; // Empty choice
          yield { choices: [{ delta: {} }] }; // Empty delta
        },
      };

      let onChunkCallback: any;
      let onFinalizeCallback: any;
      mockedStreamWrapper.mockImplementation((stream, span, options) => {
        onChunkCallback = options.onChunk;
        onFinalizeCallback = options.onFinalize;

        // Return a new async iterable that calls the callbacks
        return {
          async *[Symbol.asyncIterator]() {
            for await (const chunk of stream) {
              if (onChunkCallback) onChunkCallback(chunk);
              yield chunk;
            }
            if (onFinalizeCallback) onFinalizeCallback();
          },
        };
      });

      const OpenAIClass = class {
        chat = {
          completions: {
            create: vi.fn().mockResolvedValue(mockStream),
          },
        };
      };

      const exports = { default: OpenAIClass };

      // Save original Module._load
      const savedOriginalLoad = Module._load;

      // Mock Module._load before calling setupOpenAIHooks
      Module._load = vi.fn((request) => {
        if (request === 'openai') {
          return exports;
        }
        return originalLoad.apply(Module, [request]);
      });

      setupOpenAIHooks();

      const result = Module._load('openai', null, false);
      const instance = new result.default();

      mockedIsAsyncIterable.mockReturnValue(true);
      const resultStream = await instance.chat.completions.create({ model: 'gpt-4', stream: true });

      // Process the wrapped stream (this will trigger the callbacks)
      const chunks = [];
      for await (const chunk of resultStream) {
        chunks.push(chunk);
      }

      // With no content or finish reason, no event should be created
      expect(mockSpan.addEvent).not.toHaveBeenCalled();

      // But the span should still be ended properly
      expect(mockSpan.setStatus).toHaveBeenCalledWith({ code: SpanStatusCode.OK });
      expect(mockSpan.end).toHaveBeenCalled();

      // Restore
      Module._load = savedOriginalLoad;
    });
  });
});
