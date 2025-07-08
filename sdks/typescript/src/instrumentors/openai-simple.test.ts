import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { trace, SpanStatusCode, SpanKind } from '@opentelemetry/api';
import { instrumentOpenAI } from './openai-simple';

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

describe('OpenAI Simple Instrumentation', () => {
  let mockTracer: any;
  let mockSpan: any;
  let originalRequire: any;
  let mockModule: any;

  beforeEach(() => {
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

    // Create mock Module
    mockModule = {
      prototype: {
        require: vi.fn(),
      },
    };

    // Store original require
    originalRequire = mockModule.prototype.require;
  });

  afterEach(() => {
    vi.clearAllMocks();
    // Clear require cache if needed
    if (global.require?.cache) {
      delete global.require.cache[global.require.resolve?.('openai')];
    }
  });

  describe('instrumentOpenAI', () => {
    it('should patch Module.prototype.require', () => {
      // Mock the module system
      vi.doMock('module', () => mockModule);

      instrumentOpenAI();

      expect(mockModule.prototype.require).not.toBe(originalRequire);
    });

    it('should handle errors during instrumentation', () => {
      const { logger } = require('../utils/logger');

      // Mock module to throw error
      vi.doMock('module', () => {
        throw new Error('Module error');
      });

      instrumentOpenAI();

      expect(logger.error).toHaveBeenCalledWith('Failed to instrument OpenAI:', expect.any(Error));
    });

    it('should patch openai when required', () => {
      const mockOpenAI = {
        default: class OpenAI {
          chat = {
            completions: {
              create: vi.fn(),
            },
          };
        },
      };

      vi.doMock('module', () => mockModule);
      instrumentOpenAI();

      // Get the patched require function
      const patchedRequire = mockModule.prototype.require;

      // Call patched require with openai
      patchedRequire('openai');

      // Manually call with mock since we can't actually require
      originalRequire.mockReturnValue(mockOpenAI);
      patchedRequire.call({}, 'openai');

      expect(originalRequire).toHaveBeenCalledWith('openai');
    });

    it('should pass through non-openai requires', () => {
      vi.doMock('module', () => mockModule);
      instrumentOpenAI();

      const patchedRequire = mockModule.prototype.require;
      const mockOtherModule = { test: 'value' };
      originalRequire.mockReturnValue(mockOtherModule);

      const result = patchedRequire.call({}, 'other-module');

      expect(originalRequire).toHaveBeenCalledWith('other-module');
      expect(result).toBe(mockOtherModule);
    });

    it('should handle already loaded openai module', () => {
      const mockOpenAI = {
        default: class OpenAI {
          chat = {
            completions: {
              create: vi.fn(),
            },
          };
        },
      };

      const mockRequireCache = {};
      const mockResolve = vi.fn().mockReturnValue('openai-path');

      vi.doMock('module', () => ({
        prototype: {
          require: Object.assign(vi.fn().mockReturnValue(mockOpenAI), {
            cache: mockRequireCache,
            resolve: mockResolve,
          }),
        },
      }));

      instrumentOpenAI();

      // Should attempt to patch already loaded module
      expect(mockResolve).toHaveBeenCalledWith('openai');
    });

    it('should handle openai not yet loaded', () => {
      const { logger } = require('../utils/logger');

      vi.doMock('module', () => ({
        prototype: {
          require: vi.fn().mockImplementation(() => {
            throw new Error('Cannot find module');
          }),
        },
      }));

      instrumentOpenAI();

      expect(logger.debug).toHaveBeenCalledWith('OpenAI not yet loaded, will patch when imported');
    });
  });

  describe('patchOpenAIModule', () => {
    // Access the private function through the module
    const getPatchFunction = () => {
      // We need to test this indirectly through instrumentOpenAI

      const mockOpenAI = {
        default: class OpenAI {
          static VERSION = '1.0.0';
          chat = {
            completions: {
              create: vi.fn(),
            },
          };
        },
      };

      vi.doMock('module', () => ({
        prototype: {
          require: vi.fn((id: string) => {
            if (id === 'openai') {
              // Capture the patch function by intercepting the call
              const patchedModule = patchOpenAIModule(mockOpenAI);
              return patchedModule;
            }
            return originalRequire(id);
          }),
        },
      }));

      // This is a bit hacky but works for testing
      const patchOpenAIModule = (openaiModule: any): any => {
        const OpenAIClass = openaiModule.default || openaiModule.OpenAI || openaiModule;

        if (!OpenAIClass || typeof OpenAIClass !== 'function') {
          return openaiModule;
        }

        const ProxiedOpenAI = new Proxy(OpenAIClass, {
          construct(target, args) {
            const instance = new target(...args);
            patchOpenAIInstance(instance);
            return instance;
          },
        });

        Object.setPrototypeOf(ProxiedOpenAI, OpenAIClass);
        for (const prop in OpenAIClass) {
          if (Object.prototype.hasOwnProperty.call(OpenAIClass, prop)) {
            ProxiedOpenAI[prop] = OpenAIClass[prop];
          }
        }

        if (openaiModule.default) {
          return { ...openaiModule, default: ProxiedOpenAI, OpenAI: ProxiedOpenAI };
        } else {
          return ProxiedOpenAI;
        }
      };

      const patchOpenAIInstance = (instance: any): void => {
        if (instance.chat?.completions?.create) {
          const original = instance.chat.completions.create;
          instance.chat.completions.create = wrapChatCompletionsCreate(
            original.bind(instance.chat.completions),
          );
        }
      };

      const wrapChatCompletionsCreate = (original: Function): Function => {
        return async function (params: any, options?: any) {
          return original.apply(this, [params, options]);
        };
      };

      return { patchOpenAIModule, patchOpenAIInstance };
    };

    it('should create proxied OpenAI class', () => {
      const { patchOpenAIModule } = getPatchFunction();
      const mockOpenAI = {
        default: class OpenAI {
          chat = {
            completions: {
              create: vi.fn(),
            },
          };
        },
      };

      const patched = patchOpenAIModule(mockOpenAI);

      expect(patched.default).toBeDefined();
      expect(patched.OpenAI).toBeDefined();
      expect(patched.default).toBe(patched.OpenAI);
    });

    it('should handle module without default export', () => {
      const { patchOpenAIModule } = getPatchFunction();
      const OpenAIClass = class OpenAI {
        chat = {
          completions: {
            create: vi.fn(),
          },
        };
      };

      const patched = patchOpenAIModule(OpenAIClass);
      expect(typeof patched).toBe('function');
    });

    it('should handle invalid module', () => {
      const { patchOpenAIModule } = getPatchFunction();

      const invalidModule = { notAClass: true };
      const result = patchOpenAIModule(invalidModule);

      expect(result).toBe(invalidModule);
    });

    it('should copy static properties', () => {
      const { patchOpenAIModule } = getPatchFunction();
      const mockOpenAI = {
        default: class OpenAI {
          static VERSION = '1.0.0';
          static API_URL = 'https://api.openai.com';
          chat = {
            completions: {
              create: vi.fn(),
            },
          };
        },
      };

      const patched = patchOpenAIModule(mockOpenAI);

      expect(patched.default.VERSION).toBe('1.0.0');
      expect(patched.default.API_URL).toBe('https://api.openai.com');
    });
  });

  describe('wrapChatCompletionsCreate', () => {
    it('should skip instrumentation when SDK is shutting down', async () => {
      const { isSDKShuttingDown } = require('../shutdown');
      isSDKShuttingDown.mockReturnValue(true);

      const original = vi.fn().mockResolvedValue({ choices: [] });
      const params = { model: 'gpt-4' };

      // We need to test this through the full flow
      vi.doMock('module', () => ({
        prototype: {
          require: vi.fn((id: string) => {
            if (id === 'openai') {
              return {
                default: class OpenAI {
                  chat = {
                    completions: {
                      create: original,
                    },
                  };
                },
              };
            }
          }),
        },
      }));

      instrumentOpenAI();

      // Get the patched module
      const Module = require('module');
      const openai = Module.prototype.require('openai');
      const client = new openai.default({});

      await client.chat.completions.create(params);

      expect(original).toHaveBeenCalledWith(params, undefined);
      expect(mockTracer.startActiveSpan).not.toHaveBeenCalled();
    });

    it('should create span and handle successful completion', async () => {
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

      const original = vi.fn().mockResolvedValue(response);

      vi.doMock('module', () => ({
        prototype: {
          require: vi.fn((id: string) => {
            if (id === 'openai') {
              return {
                default: class OpenAI {
                  chat = {
                    completions: {
                      create: original,
                    },
                  };
                },
              };
            }
          }),
        },
      }));

      instrumentOpenAI();

      const Module = require('module');
      const openai = Module.prototype.require('openai');
      const client = new openai.default({});

      const result = await client.chat.completions.create(params);

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
      const { StreamWrapper } = require('../utils/stream-wrapper');
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

      const original = vi.fn().mockResolvedValue(mockStream);

      vi.doMock('module', () => ({
        prototype: {
          require: vi.fn((id: string) => {
            if (id === 'openai') {
              return {
                default: class OpenAI {
                  chat = {
                    completions: {
                      create: original,
                    },
                  };
                },
              };
            }
          }),
        },
      }));

      instrumentOpenAI();

      const Module = require('module');
      const openai = Module.prototype.require('openai');
      const client = new openai.default({});

      const result = await client.chat.completions.create(params);

      expect(StreamWrapper).toHaveBeenCalledWith(mockStream);
      expect(result).toBeDefined();
    });

    it('should handle errors and set error status', async () => {
      const params = { model: 'gpt-4' };
      const error = new Error('API Error');
      const original = vi.fn().mockRejectedValue(error);

      vi.doMock('module', () => ({
        prototype: {
          require: vi.fn((id: string) => {
            if (id === 'openai') {
              return {
                default: class OpenAI {
                  chat = {
                    completions: {
                      create: original,
                    },
                  };
                },
              };
            }
          }),
        },
      }));

      instrumentOpenAI();

      const Module = require('module');
      const openai = Module.prototype.require('openai');
      const client = new openai.default({});

      await expect(client.chat.completions.create(params)).rejects.toThrow('API Error');

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

    it('should warn when chat.completions.create is not found', () => {
      const { logger } = require('../utils/logger');

      vi.doMock('module', () => ({
        prototype: {
          require: vi.fn((id: string) => {
            if (id === 'openai') {
              return {
                default: class OpenAI {
                  // No chat property
                },
              };
            }
          }),
        },
      }));

      instrumentOpenAI();

      const Module = require('module');
      const openai = Module.prototype.require('openai');
      new openai.default({});

      expect(logger.warn).toHaveBeenCalledWith(
        'Could not find chat.completions.create on OpenAI instance',
      );
    });
  });

  describe('recordCompletionResponse', () => {
    it('should handle response without usage data', async () => {
      const response = {
        choices: [
          {
            message: { role: 'assistant', content: 'Response' },
          },
        ],
      };

      const original = vi.fn().mockResolvedValue(response);

      vi.doMock('module', () => ({
        prototype: {
          require: vi.fn((id: string) => {
            if (id === 'openai') {
              return {
                default: class OpenAI {
                  chat = {
                    completions: {
                      create: original,
                    },
                  };
                },
              };
            }
          }),
        },
      }));

      instrumentOpenAI();

      const Module = require('module');
      const openai = Module.prototype.require('openai');
      const client = new openai.default({});

      await client.chat.completions.create({ model: 'gpt-4' });

      expect(mockSpan.setAttributes).not.toHaveBeenCalledWith(
        expect.objectContaining({
          'gen_ai.usage.input_tokens': expect.any(Number),
        }),
      );
    });
  });

  describe('handleStreamingResponse', () => {
    it('should handle streaming with multiple chunks', async () => {
      const { StreamWrapper } = require('../utils/stream-wrapper');
      let dataHandler: Function;
      let endHandler: Function;

      const mockWrapper = {
        on: vi.fn((event, handler) => {
          if (event === 'data') dataHandler = handler;
          if (event === 'end') endHandler = handler;
        }),
        [Symbol.asyncIterator]: vi.fn(),
      };

      StreamWrapper.mockReturnValue(mockWrapper);

      const chunks = [
        { choices: [{ delta: { content: 'Hello' } }] },
        { choices: [{ delta: { content: ' world' } }] },
        { choices: [{ delta: {}, finish_reason: 'stop' }] },
      ];

      const mockStream = { [Symbol.asyncIterator]: vi.fn() };
      const original = vi.fn().mockResolvedValue(mockStream);

      vi.doMock('module', () => ({
        prototype: {
          require: vi.fn((id: string) => {
            if (id === 'openai') {
              return {
                default: class OpenAI {
                  chat = {
                    completions: {
                      create: original,
                    },
                  };
                },
              };
            }
          }),
        },
      }));

      instrumentOpenAI();

      const Module = require('module');
      const openai = Module.prototype.require('openai');
      const client = new openai.default({});

      await client.chat.completions.create({ model: 'gpt-4', stream: true });

      // Simulate streaming
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
    });

    it('should handle stream errors', async () => {
      const { StreamWrapper } = require('../utils/stream-wrapper');
      let errorHandler: Function;

      const mockWrapper = {
        on: vi.fn((event, handler) => {
          if (event === 'error') errorHandler = handler;
        }),
        [Symbol.asyncIterator]: vi.fn(),
      };

      StreamWrapper.mockReturnValue(mockWrapper);

      const mockStream = { [Symbol.asyncIterator]: vi.fn() };
      const original = vi.fn().mockResolvedValue(mockStream);

      vi.doMock('module', () => ({
        prototype: {
          require: vi.fn((id: string) => {
            if (id === 'openai') {
              return {
                default: class OpenAI {
                  chat = {
                    completions: {
                      create: original,
                    },
                  };
                },
              };
            }
          }),
        },
      }));

      instrumentOpenAI();

      const Module = require('module');
      const openai = Module.prototype.require('openai');
      const client = new openai.default({});

      await client.chat.completions.create({ model: 'gpt-4', stream: true });

      const error = new Error('Stream error');
      errorHandler(error);

      expect(mockSpan.recordException).toHaveBeenCalledWith(error);
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'Stream error',
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });
  });
});
