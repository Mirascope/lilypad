import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock modules before imports
vi.mock('@opentelemetry/instrumentation', () => ({
  InstrumentationBase: class InstrumentationBase {
    constructor(name: string, version: string, config: any) {
      this._config = config;
      this.tracer = {
        startSpan: vi.fn(),
      };
    }
    init() {
      return [];
    }
    _wrap(target: any, name: string, wrapper: any) {
      target[name] = wrapper(target[name]);
      return target[name];
    }
    _unwrap(_target: any, _name: string) {
      // Mock unwrap
    }
  },
  InstrumentationNodeModuleDefinition: vi.fn(),
  isWrapped: vi.fn().mockReturnValue(false),
}));

vi.mock('@opentelemetry/api', () => ({
  trace: {
    getSpan: vi.fn(),
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

vi.mock('shimmer', () => {
  const shimmerMock = {
    wrap: vi.fn(),
    unwrap: vi.fn(),
  };
  return {
    default: shimmerMock,
    wrap: shimmerMock.wrap,
    unwrap: shimmerMock.unwrap,
  };
});

vi.mock('../utils/logger', () => ({
  logger: {
    info: vi.fn(),
    debug: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock('../utils/stream-wrapper', () => ({
  StreamWrapper: vi.fn().mockImplementation((stream, span, options) => {
    const wrappedStream = {
      async *[Symbol.asyncIterator]() {
        for await (const chunk of stream) {
          if (options?.onChunk) options.onChunk(chunk);
          yield chunk;
        }
        if (options?.onFinalize) options.onFinalize();
      },
    };
    return wrappedStream;
  }),
  isAsyncIterable: vi.fn().mockImplementation((obj) => {
    return (
      obj != null &&
      (typeof obj[Symbol.asyncIterator] === 'function' ||
        (typeof obj === 'object' && Symbol.asyncIterator in obj))
    );
  }),
}));

vi.mock('../shutdown', () => ({
  isSDKShuttingDown: vi.fn().mockReturnValue(false),
}));

import { GoogleInstrumentation } from './google-otel-instrumentation';
import { trace, context, SpanStatusCode } from '@opentelemetry/api';
import { isWrapped } from '@opentelemetry/instrumentation';
import shimmer from 'shimmer';
import { logger } from '../utils/logger';
import { isAsyncIterable } from '../utils/stream-wrapper';
import { isSDKShuttingDown } from '../shutdown';

describe('GoogleInstrumentation', () => {
  let instrumentation: GoogleInstrumentation;
  let mockConfig: any;
  let mockSpan: any;

  beforeEach(() => {
    vi.clearAllMocks();
    vi.resetAllMocks();

    mockConfig = {
      requestHook: vi.fn(),
      responseHook: vi.fn(),
      fallbackToProxy: true,
      suppressInternalInstrumentation: false,
    };

    mockSpan = {
      spanContext: vi.fn().mockReturnValue({
        traceId: 'trace-123',
        spanId: 'span-456',
      }),
      setAttribute: vi.fn(),
      setAttributes: vi.fn(),
      setStatus: vi.fn(),
      recordException: vi.fn(),
      addEvent: vi.fn(),
      end: vi.fn(),
    };

    instrumentation = new GoogleInstrumentation(mockConfig);

    // Mock tracer.startSpan to return our mock span
    vi.mocked(instrumentation.tracer.startSpan).mockReturnValue(mockSpan);

    // Setup context mock
    vi.mocked(context.active).mockReturnValue({});
    vi.mocked(context.with).mockImplementation((_ctx, fn) => fn());
    vi.mocked(trace.setSpan).mockReturnValue({});

    // Mock isWrapped to return false by default
    vi.mocked(isWrapped).mockReturnValue(false);

    // Reset shimmer mock
    vi.mocked(shimmer.wrap).mockClear();
    vi.mocked(shimmer.unwrap).mockClear();
  });

  describe('init', () => {
    it('should initialize instrumentation', () => {
      const result = instrumentation.init();
      expect(result).toHaveLength(1);
      expect(result[0]).toBeDefined();
    });
  });

  describe('_applyPatch', () => {
    it('should handle GoogleGenerativeAI export pattern', () => {
      const mockModule = {
        GoogleGenerativeAI: {
          prototype: {
            getGenerativeModel: vi.fn(),
          },
        },
      };

      const result = instrumentation['_applyPatch'](mockModule);

      expect(logger.info).toHaveBeenCalledWith('[GoogleInstrumentation] Patching Google module');
      expect(logger.info).toHaveBeenCalledWith(
        '[GoogleInstrumentation] Found GoogleGenerativeAI export',
      );
      expect(result).toBe(mockModule);
    });

    it('should handle default export pattern', () => {
      const mockModule = {
        default: {
          prototype: {
            getGenerativeModel: vi.fn(),
          },
        },
      };

      const result = instrumentation['_applyPatch'](mockModule);

      expect(logger.info).toHaveBeenCalledWith('[GoogleInstrumentation] Using default export');
      expect(result).toBe(mockModule);
    });

    it('should apply proxy fallback when getGenerativeModel not found', () => {
      const mockModule = {
        GoogleGenerativeAI: {
          prototype: {},
        },
      };

      const result = instrumentation['_applyPatch'](mockModule);

      expect(logger.error).toHaveBeenCalledWith(
        '[GoogleInstrumentation] getGenerativeModel not found on prototype',
      );
      expect(result).toBe(mockModule);
    });

    it('should skip if already instrumented', () => {
      const mockModule = {
        [Symbol.for('lilypad.google.instrumented')]: true,
      };

      const result = instrumentation['_applyPatch'](mockModule);

      expect(logger.warn).toHaveBeenCalledWith(
        '[GoogleInstrumentation] Module already instrumented by Lilypad, skipping',
      );
      expect(result).toBe(mockModule);
    });
  });

  describe('getGenerativeModel wrapping', () => {
    let mockGetGenerativeModel: any;
    let mockGenerateContent: any;
    let mockGenerateContentStream: any;
    let GoogleGenerativeAI: any;

    beforeEach(() => {
      mockGenerateContent = vi.fn().mockResolvedValue({
        candidates: [
          {
            content: {
              parts: [{ text: 'Hello from Google!' }],
              role: 'model',
            },
            finish_reason: 'STOP',
          },
        ],
        usage_metadata: {
          prompt_token_count: 10,
          candidates_token_count: 5,
          total_token_count: 15,
        },
      });

      // Google returns an object with a 'stream' property
      const mockAsyncIterator = {
        async *[Symbol.asyncIterator]() {
          yield {
            candidates: [
              {
                content: { parts: [{ text: 'Hello' }] },
              },
            ],
          };
          yield {
            candidates: [
              {
                content: { parts: [{ text: ' world!' }] },
                finishReason: 'STOP',
              },
            ],
            usageMetadata: {
              promptTokenCount: 5,
              candidatesTokenCount: 10,
              totalTokenCount: 15,
            },
          };
        },
      };

      mockGenerateContentStream = vi.fn().mockResolvedValue({
        stream: mockAsyncIterator,
      });

      mockGetGenerativeModel = vi.fn().mockReturnValue({
        generateContent: mockGenerateContent,
        generateContentStream: mockGenerateContentStream,
      });

      GoogleGenerativeAI = class {};
      GoogleGenerativeAI.prototype.getGenerativeModel = mockGetGenerativeModel;

      // Setup shimmer mock to actually wrap the method
      vi.mocked(shimmer.wrap).mockClear();
      vi.mocked(shimmer.wrap).mockImplementation((target, name, wrapper) => {
        const original = target[name];
        target[name] = wrapper(original);
        return target[name];
      });
    });

    it('should wrap getGenerativeModel method', () => {
      instrumentation['_wrapGetGenerativeModel'](GoogleGenerativeAI.prototype);

      expect(shimmer.wrap).toHaveBeenCalled();
    });

    it('should wrap generateContent method for regular calls', async () => {
      instrumentation['_wrapGetGenerativeModel'](GoogleGenerativeAI.prototype);

      const instance = new GoogleGenerativeAI();
      const model = instance.getGenerativeModel({ model: 'gemini-1.5-flash' });

      // Manually wrap the model methods since shimmer mock doesn't do it automatically
      const wrappedGenerateContent = instrumentation['_createWrappedGenerateContent'](
        mockGenerateContent,
        'gemini-1.5-flash',
      );
      model.generateContent = wrappedGenerateContent;

      const params = {
        contents: [{ role: 'user', parts: [{ text: 'Hello' }] }],
        generation_config: {
          temperature: 0.7,
          max_output_tokens: 100,
        },
      };

      await model.generateContent(params);

      expect(instrumentation.tracer.startSpan).toHaveBeenCalledWith(
        'google.generateContent gemini-1.5-flash',
        expect.objectContaining({
          kind: 2, // SpanKind.CLIENT
          attributes: expect.objectContaining({
            'gen_ai.system': 'google_genai',
            'gen_ai.request.model': 'gemini-1.5-flash',
            'gen_ai.request.temperature': 0.7,
            'gen_ai.request.max_tokens': 100,
            'gen_ai.operation.name': 'chat',
            'lilypad.type': 'trace',
            'server.address': 'generativelanguage.googleapis.com',
          }),
        }),
        expect.any(Object),
      );

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.user.message', {
        'gen_ai.system': 'google_genai',
        content: JSON.stringify(['Hello']),
      });

      expect(mockSpan.setStatus).toHaveBeenCalledWith({ code: SpanStatusCode.OK });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should handle string input', async () => {
      instrumentation['_wrapGetGenerativeModel'](GoogleGenerativeAI.prototype);

      const instance = new GoogleGenerativeAI();
      const model = instance.getGenerativeModel({ model: 'gemini-1.5-flash' });

      // Manually wrap the model methods
      const wrappedGenerateContent = instrumentation['_createWrappedGenerateContent'](
        mockGenerateContent,
        'gemini-1.5-flash',
      );
      model.generateContent = wrappedGenerateContent;

      await model.generateContent('Hello Google!');

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.user.message', {
        'gen_ai.system': 'google_genai',
        content: JSON.stringify(['Hello Google!']),
      });
    });

    it('should handle streaming responses', async () => {
      instrumentation['_wrapGetGenerativeModel'](GoogleGenerativeAI.prototype);

      const instance = new GoogleGenerativeAI();
      const model = instance.getGenerativeModel({ model: 'gemini-1.5-flash' });

      // Manually wrap the model methods
      const wrappedGenerateContentStream = instrumentation['_createWrappedGenerateContentStream'](
        mockGenerateContentStream,
        'gemini-1.5-flash',
      );
      model.generateContentStream = wrappedGenerateContentStream;

      const params = {
        contents: [{ role: 'user', parts: [{ text: 'Hello' }] }],
      };

      const result = await model.generateContentStream(params);

      expect(isAsyncIterable).toHaveBeenCalled();
      expect(result).toBeDefined();
      expect(result.stream).toBeDefined();

      // Iterate through the stream to trigger the wrapper
      const chunks = [];
      for await (const chunk of result.stream) {
        chunks.push(chunk);
      }
      expect(chunks.length).toBe(2);
    });

    it('should handle errors gracefully', async () => {
      const error = new Error('API error');
      mockGenerateContent.mockRejectedValue(error);

      instrumentation['_wrapGetGenerativeModel'](GoogleGenerativeAI.prototype);

      const instance = new GoogleGenerativeAI();
      const model = instance.getGenerativeModel({ model: 'gemini-1.5-flash' });

      // Manually wrap the model methods
      const wrappedGenerateContent = instrumentation['_createWrappedGenerateContent'](
        mockGenerateContent,
        'gemini-1.5-flash',
      );
      model.generateContent = wrappedGenerateContent;

      await expect(model.generateContent('Hello')).rejects.toThrow(error);

      expect(mockSpan.recordException).toHaveBeenCalledWith(error);
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'API error',
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should skip instrumentation when SDK is shutting down', async () => {
      vi.mocked(isSDKShuttingDown).mockReturnValue(true);

      instrumentation['_wrapGetGenerativeModel'](GoogleGenerativeAI.prototype);

      const instance = new GoogleGenerativeAI();
      const model = instance.getGenerativeModel({ model: 'gemini-1.5-flash' });

      // Manually wrap the model methods
      const wrappedGenerateContent = instrumentation['_createWrappedGenerateContent'](
        mockGenerateContent,
        'gemini-1.5-flash',
      );
      model.generateContent = wrappedGenerateContent;

      await model.generateContent('Hello');

      expect(instrumentation.tracer.startSpan).not.toHaveBeenCalled();
      expect(mockGenerateContent).toHaveBeenCalled();
    });
  });

  describe('_recordResponse', () => {
    it('should handle Google result.response structure', () => {
      const result = {
        response: {
          candidates: [
            {
              content: {
                parts: [{ text: 'Response text' }],
                role: 'model',
              },
              finishReason: 'STOP',
            },
          ],
          usageMetadata: {
            promptTokenCount: 5,
            candidatesTokenCount: 10,
            totalTokenCount: 15,
          },
        },
      };

      instrumentation['_recordResponse'](mockSpan, result);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'google_genai',
        index: 0,
        finish_reason: 'STOP',
        message: JSON.stringify({
          role: 'model',
          content: ['Response text'],
        }),
      });
    });

    it('should handle both camelCase and snake_case properties', () => {
      const responseWithSnakeCase = {
        response: {
          candidates: [
            {
              content: {
                parts: [{ text: 'Test' }],
                role: 'model',
              },
              finish_reason: 'STOP', // snake_case
            },
          ],
          usage_metadata: {
            // snake_case
            prompt_token_count: 10,
            candidates_token_count: 20,
            total_token_count: 30,
          },
        },
      };

      instrumentation['_recordResponse'](mockSpan, responseWithSnakeCase);

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.finish_reasons', [
        'STOP',
      ]);

      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.usage.input_tokens': 10,
        'gen_ai.usage.output_tokens': 20,
        'gen_ai.usage.total_tokens': 30,
      });
    });
    it('should record response attributes', () => {
      const response = {
        candidates: [
          {
            content: {
              parts: [{ text: 'Hello ' }, { text: 'world!' }],
              role: 'model',
            },
            finish_reason: 'STOP',
            index: 0,
          },
        ],
        usage_metadata: {
          prompt_token_count: 10,
          candidates_token_count: 20,
          total_token_count: 30,
        },
      };

      instrumentation['_recordResponse'](mockSpan, response);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'google_genai',
        index: 0,
        finish_reason: 'STOP',
        message: JSON.stringify({
          role: 'model',
          content: ['Hello ', 'world!'],
        }),
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.finish_reasons', [
        'STOP',
      ]);

      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.usage.input_tokens': 10,
        'gen_ai.usage.output_tokens': 20,
        'gen_ai.usage.total_tokens': 30,
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith(
        'server.address',
        'generativelanguage.googleapis.com',
      );
    });

    it('should handle image content', () => {
      const response = {
        candidates: [
          {
            content: {
              parts: [
                { text: 'I see an image of ' },
                { inline_data: { mime_type: 'image/jpeg', data: 'base64data' } },
              ],
              role: 'model',
            },
          },
        ],
      };

      instrumentation['_recordResponse'](mockSpan, response);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'google_genai',
        index: 0,
        finish_reason: 'stop',
        message: JSON.stringify({
          role: 'model',
          content: ['I see an image of '],
        }),
      });
    });
  });

  describe('hooks', () => {
    it('should call request hook if provided', async () => {
      const mockGenerateContent = vi.fn().mockResolvedValue({ candidates: [] });

      // Create a model class/object that shimmer can wrap
      class MockModel {
        _modelName = 'gemini-1.5-flash';
        generateContent = mockGenerateContent;
      }

      const mockGetGenerativeModel = vi.fn().mockImplementation((config) => {
        const model = new MockModel();
        model._modelName = config.model;
        return model;
      });

      const GoogleGenerativeAI = class {};
      GoogleGenerativeAI.prototype.getGenerativeModel = mockGetGenerativeModel;

      // Setup shimmer to actually call the wrapper function
      vi.mocked(shimmer.wrap).mockImplementation((target, name, wrapper) => {
        const original = target[name];
        target[name] = wrapper(original);
        return target[name];
      });

      instrumentation['_wrapGetGenerativeModel'](GoogleGenerativeAI.prototype);

      const instance = new GoogleGenerativeAI();
      const model = instance.getGenerativeModel({ model: 'gemini-1.5-flash' });

      const params = { contents: [] };
      await model.generateContent(params);

      // Request hook should be called with span and params
      expect(mockConfig.requestHook).toHaveBeenCalledWith(mockSpan, params);
    });

    it('should call response hook if provided', async () => {
      const response = { candidates: [] };
      const mockGenerateContent = vi.fn().mockResolvedValue(response);

      // Create a model class/object that shimmer can wrap
      class MockModel {
        _modelName = 'gemini-1.5-flash';
        generateContent = mockGenerateContent;
      }

      const mockGetGenerativeModel = vi.fn().mockImplementation((config) => {
        const model = new MockModel();
        model._modelName = config.model;
        return model;
      });

      const GoogleGenerativeAI = class {};
      GoogleGenerativeAI.prototype.getGenerativeModel = mockGetGenerativeModel;

      // Setup shimmer to actually call the wrapper function
      vi.mocked(shimmer.wrap).mockImplementation((target, name, wrapper) => {
        const original = target[name];
        target[name] = wrapper(original);
        return target[name];
      });

      instrumentation['_wrapGetGenerativeModel'](GoogleGenerativeAI.prototype);

      const instance = new GoogleGenerativeAI();
      const model = instance.getGenerativeModel({ model: 'gemini-1.5-flash' });

      await model.generateContent('Hello');

      // Response hook should be called with span and response
      expect(mockConfig.responseHook).toHaveBeenCalledWith(mockSpan, response);
    });
  });

  describe('_detectOtherInstrumentations', () => {
    it('should detect other instrumentation libraries', () => {
      const mockModule = {
        [Symbol.for('datadog.instrumented')]: true,
        __NR_instrumented: true,
      };

      const result = instrumentation['_detectOtherInstrumentations'](mockModule);

      expect(result).toContain('Datadog');
      expect(result).toContain('New Relic');
    });

    it('should detect wrapped methods', () => {
      const mockModule = {
        GoogleGenerativeAI: {
          prototype: {
            getGenerativeModel: function () {
              // Intentionally short function that might be a wrapper
            },
          },
        },
      };

      const result = instrumentation['_detectOtherInstrumentations'](mockModule);

      expect(result).toContain('Unknown (wrapped method detected)');
    });
  });

  describe('proxy fallback', () => {
    it('should apply proxy fallback when configured', () => {
      const mockModule = {
        GoogleGenerativeAI: vi.fn().mockImplementation(function () {
          this.getGenerativeModel = vi.fn().mockReturnValue({
            generateContent: vi.fn(),
            generateContentStream: vi.fn(),
          });
        }),
      };

      const result = instrumentation['_applyProxyFallback'](mockModule);

      expect(result).toBe(mockModule);
      expect(mockModule.GoogleGenerativeAI).toBeDefined();
    });

    it('should wrap methods through proxy', async () => {
      const mockGenerateContent = vi.fn().mockResolvedValue({ candidates: [] });

      // Create the model object that will be returned
      const mockModel = {
        _modelName: 'gemini-1.5-flash',
        generateContent: mockGenerateContent,
      };

      const mockGetGenerativeModel = vi.fn().mockReturnValue(mockModel);

      // Create a constructor function with getGenerativeModel on instance
      const GoogleGenerativeAIConstructor = function () {
        this.getGenerativeModel = mockGetGenerativeModel;
      };

      const mockModule = {
        GoogleGenerativeAI: GoogleGenerativeAIConstructor,
      };

      // Apply proxy fallback - this should wrap the constructor
      instrumentation['_applyProxyFallback'](mockModule);

      // Now the GoogleGenerativeAI constructor should be wrapped with a proxy
      // Create an instance through the proxied constructor
      const instance = new mockModule.GoogleGenerativeAI();

      // The instance should be automatically proxied by the constructor proxy
      const model = instance.getGenerativeModel({ model: 'gemini-1.5-flash' });

      // The generateContent method should be wrapped by the proxy
      await model.generateContent('Hello');

      // Verify the span was created
      expect(instrumentation.tracer.startSpan).toHaveBeenCalledWith(
        expect.stringContaining('google'),
        expect.objectContaining({
          kind: 2,
          attributes: expect.objectContaining({
            'gen_ai.system': 'google_genai',
          }),
        }),
        expect.any(Object),
      );
    });
  });

  describe('chat session support', () => {
    let mockGetGenerativeModel: any;
    let mockStartChat: any;
    let mockSendMessage: any;
    let GoogleGenerativeAI: any;

    beforeEach(() => {
      mockSendMessage = vi.fn().mockResolvedValue({
        response: {
          candidates: [
            {
              content: {
                parts: [{ text: '2 + 2 = 4' }],
                role: 'model',
              },
              finishReason: 'STOP',
            },
          ],
          usageMetadata: {
            promptTokenCount: 5,
            candidatesTokenCount: 10,
            totalTokenCount: 15,
          },
        },
      });

      const mockChatSession = {
        sendMessage: mockSendMessage,
      };

      mockStartChat = vi.fn().mockReturnValue(mockChatSession);

      mockGetGenerativeModel = vi.fn().mockReturnValue({
        startChat: mockStartChat,
        _modelName: 'gemini-1.5-flash',
      });

      GoogleGenerativeAI = class {};
      GoogleGenerativeAI.prototype.getGenerativeModel = mockGetGenerativeModel;

      // Setup shimmer mock to actually wrap the method
      vi.mocked(shimmer.wrap).mockClear();
      vi.mocked(shimmer.wrap).mockImplementation((target, name, wrapper) => {
        const original = target[name];
        target[name] = wrapper(original);
        return target[name];
      });
    });

    it('should wrap chat session methods', async () => {
      instrumentation['_wrapGetGenerativeModel'](GoogleGenerativeAI.prototype);

      const instance = new GoogleGenerativeAI();
      const model = instance.getGenerativeModel({ model: 'gemini-1.5-flash' });

      // Trigger startChat wrapping
      const chatSession = model.startChat();

      // The sendMessage method should be wrapped
      expect(shimmer.wrap).toHaveBeenCalledWith(chatSession, 'sendMessage', expect.any(Function));
    });

    it('should create span for chat messages', async () => {
      instrumentation['_wrapGetGenerativeModel'](GoogleGenerativeAI.prototype);

      const instance = new GoogleGenerativeAI();
      const model = instance.getGenerativeModel({ model: 'gemini-1.5-flash' });
      const chatSession = model.startChat();

      // Manually wrap sendMessage
      const wrappedSendMessage = instrumentation['_createWrappedSendMessage'](
        mockSendMessage,
        'gemini-1.5-flash',
      );
      chatSession.sendMessage = wrappedSendMessage;

      await chatSession.sendMessage('What is 2 + 2?');

      expect(instrumentation.tracer.startSpan).toHaveBeenCalledWith(
        'google.chat.sendMessage gemini-1.5-flash',
        expect.objectContaining({
          kind: 2, // SpanKind.CLIENT
          attributes: expect.objectContaining({
            'gen_ai.system': 'google_genai',
            'gen_ai.request.model': 'gemini-1.5-flash',
            'gen_ai.operation.name': 'chat',
            'lilypad.type': 'trace',
            'server.address': 'generativelanguage.googleapis.com',
          }),
        }),
        expect.any(Object),
      );

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.user.message', {
        'gen_ai.system': 'google_genai',
        content: JSON.stringify(['What is 2 + 2?']),
      });

      // Should record the response
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'google_genai',
        index: 0,
        finish_reason: 'STOP',
        message: JSON.stringify({
          role: 'model',
          content: ['2 + 2 = 4'],
        }),
      });

      expect(mockSpan.setStatus).toHaveBeenCalledWith({ code: SpanStatusCode.OK });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should handle chat errors', async () => {
      const error = new Error('Chat API error');
      mockSendMessage.mockRejectedValue(error);

      instrumentation['_wrapGetGenerativeModel'](GoogleGenerativeAI.prototype);

      const instance = new GoogleGenerativeAI();
      const model = instance.getGenerativeModel({ model: 'gemini-1.5-flash' });
      const chatSession = model.startChat();

      // Manually wrap sendMessage
      const wrappedSendMessage = instrumentation['_createWrappedSendMessage'](
        mockSendMessage,
        'gemini-1.5-flash',
      );
      chatSession.sendMessage = wrappedSendMessage;

      await expect(chatSession.sendMessage('Hello')).rejects.toThrow(error);

      expect(mockSpan.recordException).toHaveBeenCalledWith(error);
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'Chat API error',
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should preserve model name on chat session', () => {
      instrumentation['_wrapGetGenerativeModel'](GoogleGenerativeAI.prototype);

      const instance = new GoogleGenerativeAI();
      const model = instance.getGenerativeModel({ model: 'gemini-1.5-pro' });
      const chatSession = model.startChat();

      expect(chatSession._modelName).toBe('gemini-1.5-pro');
    });
  });
});
