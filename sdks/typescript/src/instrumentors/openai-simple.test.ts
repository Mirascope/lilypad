import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { trace, SpanStatusCode, SpanKind } from '@opentelemetry/api';
import Module from 'module';

// Mock logger before importing the module
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

vi.mock('../utils/json', () => ({
  safeStringify: vi.fn((obj) => JSON.stringify(obj)),
}));

vi.mock('../utils/stream-wrapper', () => ({
  StreamWrapper: vi.fn((stream) => stream),
  isAsyncIterable: vi.fn((obj) => obj && typeof obj[Symbol.asyncIterator] === 'function'),
}));

import { instrumentOpenAI } from './openai-simple';
import { logger } from '../utils/logger';
import { isSDKShuttingDown } from '../shutdown';
// safeStringify is mocked but not used directly in tests
import { StreamWrapper, isAsyncIterable } from '../utils/stream-wrapper';

describe('OpenAI Simple Instrumentation', () => {
  let mockTracer: any;
  let mockSpan: any;
  let originalRequire: any;
  let originalResolve: any;
  let originalCache: any;

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

    // Save original Module methods
    originalRequire = Module.prototype.require;
    originalResolve = require.resolve;
    originalCache = { ...require.cache };
  });

  afterEach(() => {
    // Restore Module methods
    Module.prototype.require = originalRequire;
    require.resolve = originalResolve;
    require.cache = originalCache;
    vi.restoreAllMocks();
  });

  describe('instrumentOpenAI', () => {
    it('should patch Module.prototype.require', () => {
      instrumentOpenAI();

      expect(Module.prototype.require).not.toBe(originalRequire);
      expect(vi.mocked(logger).debug).toHaveBeenCalledWith('Starting OpenAI instrumentation');
      expect(vi.mocked(logger).debug).toHaveBeenCalledWith('Patching Module.prototype.require');
      expect(vi.mocked(logger).debug).toHaveBeenCalledWith('OpenAI instrumentation setup complete');
    });

    it('should intercept openai module require', () => {
      instrumentOpenAI();

      // Create a mock OpenAI module
      const mockOpenAIModule = {
        default: vi.fn(function OpenAI() {
          this.chat = {
            completions: {
              create: vi.fn(),
            },
          };
        }),
      };

      // Mock originalRequire to return the mock module
      const patchedRequire = Module.prototype.require;
      Module.prototype.require = function (id: string, ...args: any[]) {
        if (id === 'openai') {
          // Call the patched require which should intercept
          return patchedRequire.call(this, id, ...args);
        }
        if (id === 'original-openai-for-test') {
          return mockOpenAIModule;
        }
        return originalRequire.call(this, id, ...args);
      };

      // Override originalRequire temporarily
      const tempOriginal = originalRequire;
      originalRequire = vi.fn((id: string) => {
        if (id === 'openai') {
          return mockOpenAIModule;
        }
        return tempOriginal.call(this, id);
      });

      // Test requiring openai
      const result = require('openai');

      expect(vi.mocked(logger).debug).toHaveBeenCalledWith('require called for: openai');
      expect(vi.mocked(logger).debug).toHaveBeenCalledWith(
        'OpenAI module detected in require, patching it',
      );
      expect(result).toBeDefined();
      expect(result.default).toBeDefined();

      // Restore
      originalRequire = tempOriginal;
    });

    it('should handle when OpenAI is already loaded', () => {
      // Mock require.cache with openai
      const mockOpenAIModule = {
        default: vi.fn(function OpenAI() {
          this.chat = { completions: { create: vi.fn() } };
        }),
      };

      const mockPath = '/path/to/openai';
      require.cache[mockPath] = { exports: mockOpenAIModule };

      // Mock require.resolve
      require.resolve = vi.fn((id: string) => {
        if (id === 'openai') return mockPath;
        return originalResolve(id);
      });

      // Mock the Module's require to return openai
      Module.prototype.require = vi.fn((id: string) => {
        if (id === 'openai') return mockOpenAIModule;
        return originalRequire.call(this, id);
      });

      instrumentOpenAI();

      expect(vi.mocked(logger).debug).toHaveBeenCalledWith(
        'OpenAI already loaded, patching it now',
      );
    });

    it('should handle when OpenAI is not yet loaded', () => {
      // Make Module.prototype.require throw for openai
      Module.prototype.require = vi.fn((id: string) => {
        if (id === 'openai') throw new Error('Cannot find module');
        return originalRequire.call(this, id);
      });

      instrumentOpenAI();

      expect(vi.mocked(logger).debug).toHaveBeenCalledWith(
        'OpenAI not yet loaded, will patch when imported',
      );
    });

    it('should handle errors during instrumentation', () => {
      // Make require('module') throw
      const tempRequire = globalThis.require as any;
      globalThis.require = vi.fn((id: string) => {
        if (id === 'module') throw new Error('Module error');
        return tempRequire(id);
      }) as any;

      instrumentOpenAI();

      expect(vi.mocked(logger).error).toHaveBeenCalledWith(
        'Failed to instrument OpenAI:',
        expect.any(Error),
      );

      // Restore
      globalThis.require = tempRequire;
    });
  });

  describe('patchOpenAIModule', () => {
    it('should create proxy for OpenAI constructor with default export', () => {
      instrumentOpenAI();

      const MockOpenAI = vi.fn(function (this: any) {
        this.chat = {
          completions: {
            create: vi.fn().mockResolvedValue({ choices: [] }),
          },
        };
      });
      MockOpenAI.staticProp = 'value';

      const mockModule = { default: MockOpenAI };

      // Test the patching by calling require
      const patchedRequire = Module.prototype.require;
      Module.prototype.require = function (id: string) {
        if (id === 'openai') {
          return patchedRequire.call(this, id);
        }
        if (id === 'openai-original') {
          return mockModule;
        }
        return originalRequire.call(this, id);
      };

      // Mock originalRequire to return our module
      const tempOriginal = originalRequire;
      originalRequire = vi.fn((id: string) => {
        if (id === 'openai') {
          return mockModule;
        }
        return tempOriginal.call(this, id);
      });

      const result = require('openai');

      // Verify structure
      expect(result).toBeDefined();
      expect(result.default).toBeDefined();
      expect(result.OpenAI).toBeDefined();
      expect(typeof result.default).toBe('function');

      // Create instance and verify it's proxied
      const _instance = new result.default();
      expect(vi.mocked(logger).debug).toHaveBeenCalledWith('Creating OpenAI instance');
      expect(vi.mocked(logger).debug).toHaveBeenCalledWith('Patching OpenAI instance');

      // Restore
      originalRequire = tempOriginal;
    });

    it('should handle module with only OpenAI named export', () => {
      instrumentOpenAI();

      const MockOpenAI = vi.fn(function (this: any) {
        this.chat = {
          completions: {
            create: vi.fn(),
          },
        };
      });

      const mockModule = { OpenAI: MockOpenAI };

      const patchedRequire = Module.prototype.require;
      Module.prototype.require = function (id: string) {
        if (id === 'openai') {
          return patchedRequire.call(this, id);
        }
        return originalRequire.call(this, id);
      };

      const tempOriginal = originalRequire;
      originalRequire = vi.fn((id: string) => {
        if (id === 'openai') {
          return mockModule;
        }
        return tempOriginal.call(this, id);
      });

      const result = require('openai');
      expect(result).toBeDefined();

      // Restore
      originalRequire = tempOriginal;
    });

    it('should handle direct function export', () => {
      instrumentOpenAI();

      const MockOpenAI = vi.fn(function (this: any) {
        this.chat = {
          completions: {
            create: vi.fn(),
          },
        };
      });

      const patchedRequire = Module.prototype.require;
      Module.prototype.require = function (id: string) {
        if (id === 'openai') {
          return patchedRequire.call(this, id);
        }
        return originalRequire.call(this, id);
      };

      const tempOriginal = originalRequire;
      originalRequire = vi.fn((id: string) => {
        if (id === 'openai') {
          return MockOpenAI;
        }
        return tempOriginal.call(this, id);
      });

      const result = require('openai');
      expect(result).toBeDefined();

      // Restore
      originalRequire = tempOriginal;
    });

    it('should return module as-is when OpenAI class not found', () => {
      instrumentOpenAI();

      const invalidModule = { foo: 'bar' };

      const patchedRequire = Module.prototype.require;
      Module.prototype.require = function (id: string) {
        if (id === 'openai') {
          return patchedRequire.call(this, id);
        }
        return originalRequire.call(this, id);
      };

      const tempOriginal = originalRequire;
      originalRequire = vi.fn((id: string) => {
        if (id === 'openai') {
          return invalidModule;
        }
        return tempOriginal.call(this, id);
      });

      const result = require('openai');

      expect(vi.mocked(logger).error).toHaveBeenCalledWith('Could not find OpenAI class');
      expect(result).toBe(invalidModule);

      // Restore
      originalRequire = tempOriginal;
    });

    it('should preserve static properties on proxied class', () => {
      instrumentOpenAI();

      const MockOpenAI = vi.fn(function (this: any) {
        this.chat = {
          completions: {
            create: vi.fn(),
          },
        };
      });
      MockOpenAI.VERSION = '1.0.0';
      MockOpenAI.customStatic = 'test';

      const mockModule = { default: MockOpenAI };

      const patchedRequire = Module.prototype.require;
      Module.prototype.require = function (id: string) {
        if (id === 'openai') {
          return patchedRequire.call(this, id);
        }
        return originalRequire.call(this, id);
      };

      const tempOriginal = originalRequire;
      originalRequire = vi.fn((id: string) => {
        if (id === 'openai') {
          return mockModule;
        }
        return tempOriginal.call(this, id);
      });

      const result = require('openai');

      expect(result.default.VERSION).toBe('1.0.0');
      expect(result.default.customStatic).toBe('test');

      // Restore
      originalRequire = tempOriginal;
    });
  });

  describe('patchOpenAIInstance', () => {
    it('should patch chat.completions.create method', () => {
      instrumentOpenAI();

      const mockCreate = vi.fn().mockResolvedValue({ choices: [] });
      const MockOpenAI = vi.fn(function (this: any) {
        this.chat = {
          completions: {
            create: mockCreate,
          },
        };
      });

      const mockModule = { default: MockOpenAI };

      const patchedRequire = Module.prototype.require;
      Module.prototype.require = function (id: string) {
        if (id === 'openai') {
          return patchedRequire.call(this, id);
        }
        return originalRequire.call(this, id);
      };

      const tempOriginal = originalRequire;
      originalRequire = vi.fn((id: string) => {
        if (id === 'openai') {
          return mockModule;
        }
        return tempOriginal.call(this, id);
      });

      const OpenAI = require('openai').default;
      const instance = new OpenAI();

      // Verify the create method was replaced
      expect(instance.chat.completions.create).not.toBe(mockCreate);
      expect(instance.chat.completions.create).toBeDefined();
      expect(vi.mocked(logger).debug).toHaveBeenCalledWith('Patched chat.completions.create');

      // Restore
      originalRequire = tempOriginal;
    });

    it('should warn when chat.completions.create not found', () => {
      instrumentOpenAI();

      const MockOpenAI = vi.fn(function (this: any) {
        // No chat property - intentionally empty for test
      });

      const mockModule = { default: MockOpenAI };

      const patchedRequire = Module.prototype.require;
      Module.prototype.require = function (id: string) {
        if (id === 'openai') {
          return patchedRequire.call(this, id);
        }
        return originalRequire.call(this, id);
      };

      const tempOriginal = originalRequire;
      originalRequire = vi.fn((id: string) => {
        if (id === 'openai') {
          return mockModule;
        }
        return tempOriginal.call(this, id);
      });

      const OpenAI = require('openai').default;
      new OpenAI();

      expect(vi.mocked(logger).warn).toHaveBeenCalledWith(
        'Could not find chat.completions.create on OpenAI instance',
      );

      // Restore
      originalRequire = tempOriginal;
    });
  });

  describe('wrapChatCompletionsCreate', () => {
    let wrappedCreate: any;
    let mockOriginal: any;

    beforeEach(() => {
      instrumentOpenAI();

      mockOriginal = vi.fn();
      const MockOpenAI = vi.fn(function (this: any) {
        this.chat = {
          completions: {
            create: mockOriginal,
          },
        };
      });

      const mockModule = { default: MockOpenAI };

      const patchedRequire = Module.prototype.require;
      Module.prototype.require = function (id: string) {
        if (id === 'openai') {
          return patchedRequire.call(this, id);
        }
        return originalRequire.call(this, id);
      };

      const tempOriginal = originalRequire;
      originalRequire = vi.fn((id: string) => {
        if (id === 'openai') {
          return mockModule;
        }
        return tempOriginal.call(this, id);
      });

      const OpenAI = require('openai').default;
      const instance = new OpenAI();
      wrappedCreate = instance.chat.completions.create;

      // Restore for the tests
      originalRequire = tempOriginal;
    });

    it('should skip instrumentation when SDK is shutting down', async () => {
      vi.mocked(isSDKShuttingDown).mockReturnValue(true);

      const params = { model: 'gpt-4', messages: [] };
      const expectedResult = { choices: [] };

      mockOriginal.mockResolvedValue(expectedResult);

      const result = await wrappedCreate(params);

      expect(result).toBe(expectedResult);
      expect(mockOriginal).toHaveBeenCalledWith(params, undefined);
      expect(mockTracer.startActiveSpan).not.toHaveBeenCalled();
    });

    it('should create span and record attributes', async () => {
      const params = {
        model: 'gpt-4',
        messages: [{ role: 'user', content: 'Hello' }],
        temperature: 0.7,
        max_tokens: 100,
      };

      mockOriginal.mockResolvedValue({ choices: [] });

      await wrappedCreate(params);

      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        'openai.chat.completions gpt-4',
        expect.objectContaining({
          kind: SpanKind.CLIENT,
          attributes: expect.objectContaining({
            'gen_ai.system': 'openai',
            'gen_ai.request.model': 'gpt-4',
            'gen_ai.request.temperature': 0.7,
            'gen_ai.request.max_tokens': 100,
          }),
        }),
        expect.any(Function),
      );
    });

    it('should handle streaming response', async () => {
      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield { choices: [{ delta: { content: 'Hello' } }] };
        },
      };

      mockOriginal.mockResolvedValue(mockStream);
      vi.mocked(isAsyncIterable).mockReturnValue(true);

      const params = { model: 'gpt-4', messages: [], stream: true };
      const result = await wrappedCreate(params);

      expect(StreamWrapper).toHaveBeenCalledWith(mockStream);
      expect(result).toBeDefined();
    });

    it('should handle errors and record them in span', async () => {
      const error = new Error('API Error');
      mockOriginal.mockRejectedValue(error);

      await expect(wrappedCreate({ model: 'gpt-4', messages: [] })).rejects.toThrow('API Error');

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

    it('should record completion response details', async () => {
      const response = {
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
        model: 'gpt-4-0613',
      };

      mockOriginal.mockResolvedValue(response);

      await wrappedCreate({ model: 'gpt-4', messages: [] });

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.content.completion', {
        'gen_ai.completion.role': 'assistant',
        'gen_ai.completion.content': '"Hello!"',
        'gen_ai.completion.index': '0',
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.finish_reasons', [
        'stop',
      ]);

      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.usage.prompt_tokens': 10,
        'gen_ai.usage.completion_tokens': 20,
        'gen_ai.usage.total_tokens': 30,
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.model', 'gpt-4-0613');
    });
  });
});
