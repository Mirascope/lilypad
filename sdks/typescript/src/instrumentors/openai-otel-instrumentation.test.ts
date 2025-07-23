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
  isWrapped: vi.fn(),
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
  StreamWrapper: vi.fn(),
  isAsyncIterable: vi.fn(),
}));

vi.mock('../shutdown', () => ({
  isSDKShuttingDown: vi.fn(),
}));

// Import after mocks
import { OpenAIInstrumentation } from './openai-otel-instrumentation';
import { InstrumentationNodeModuleDefinition, isWrapped } from '@opentelemetry/instrumentation';
import { trace, context, SpanKind, SpanStatusCode } from '@opentelemetry/api';
import shimmer from 'shimmer';
import { logger } from '../utils/logger';
import { StreamWrapper, isAsyncIterable } from '../utils/stream-wrapper';
import { isSDKShuttingDown } from '../shutdown';

// Get mocked functions
const mockedInstrumentationNodeModuleDefinition = vi.mocked(InstrumentationNodeModuleDefinition);
const mockedIsWrapped = vi.mocked(isWrapped);
const mockedTrace = vi.mocked(trace);
const mockedContext = vi.mocked(context);
const mockedShimmer = vi.mocked(shimmer);
const mockedLogger = vi.mocked(logger);
const mockedStreamWrapper = vi.mocked(StreamWrapper);
const mockedIsAsyncIterable = vi.mocked(isAsyncIterable);
const mockedIsSDKShuttingDown = vi.mocked(isSDKShuttingDown);

describe('OpenAIInstrumentation', () => {
  let instrumentation: OpenAIInstrumentation;
  let mockSpan: any;
  let mockTracer: any;

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock span
    mockSpan = {
      spanContext: vi.fn(() => ({
        spanId: 'span123',
        traceId: 'trace123',
      })),
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
    mockedInstrumentationNodeModuleDefinition.mockImplementation(
      (name, versions, patch, unpatch) => ({
        name,
        versions,
        patch,
        unpatch,
      }),
    );
    mockedIsWrapped.mockReturnValue(false);
    mockedContext.with.mockImplementation((ctx, fn) => fn());
    mockedStreamWrapper.mockImplementation((stream, span, options) => {
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
    mockedIsSDKShuttingDown.mockReturnValue(false);

    instrumentation = new OpenAIInstrumentation();
    instrumentation.tracer = mockTracer;
  });

  describe('initialization', () => {
    it('should create instrumentation with default config', () => {
      expect(instrumentation).toBeDefined();
      // Call init to trigger the logging
      instrumentation['init']();
      expect(mockedLogger.info).toHaveBeenCalledWith(
        '[OpenAIInstrumentation] Initializing OpenAI instrumentation',
      );
    });

    it('should create instrumentation with custom config', () => {
      const config = {
        requestHook: vi.fn(),
        responseHook: vi.fn(),
        fallbackToProxy: true,
        suppressInternalInstrumentation: true,
      };

      const customInstrumentation = new OpenAIInstrumentation(config);
      expect(customInstrumentation['_config']).toEqual(config);
    });

    it('should return module definition on init', () => {
      const modules = instrumentation['init']();
      expect(modules).toHaveLength(1);
      expect(mockedInstrumentationNodeModuleDefinition).toHaveBeenCalledWith(
        'openai',
        ['>=4.0.0'],
        expect.any(Function),
        expect.any(Function),
      );
    });
  });

  describe('_applyPatch', () => {
    let mockOpenAIClass: any;
    let mockModuleExports: any;

    beforeEach(() => {
      mockOpenAIClass = class OpenAI {};
      mockOpenAIClass.prototype.chat = {
        completions: {
          create: vi.fn(),
        },
      };

      mockModuleExports = {
        default: mockOpenAIClass,
      };
    });

    it('should patch default export', () => {
      // Add the _wrapChatCompletions method to the spy
      vi.spyOn(instrumentation as any, '_wrapChatCompletions').mockImplementation((prototype) => {
        if (prototype.chat?.completions) {
          mockedShimmer.wrap(prototype.chat.completions, 'create', vi.fn());
        }
      });

      const result = instrumentation['_applyPatch'](mockModuleExports);

      expect(mockedLogger.info).toHaveBeenCalledWith(
        '[OpenAIInstrumentation] Patching OpenAI module',
      );
      expect(mockedLogger.info).toHaveBeenCalledWith(
        '[OpenAIInstrumentation] Found default export',
      );
      expect(instrumentation['_wrapChatCompletions']).toHaveBeenCalled();
      expect(result[Symbol.for('lilypad.openai.instrumented')]).toBe(true);
    });

    it('should patch named export', () => {
      const moduleExports = {
        OpenAI: mockOpenAIClass,
      };

      // Add the _wrapChatCompletions method to the spy
      vi.spyOn(instrumentation as any, '_wrapChatCompletions').mockImplementation((prototype) => {
        if (prototype.chat?.completions) {
          mockedShimmer.wrap(prototype.chat.completions, 'create', vi.fn());
        }
      });

      const result = instrumentation['_applyPatch'](moduleExports);

      expect(mockedLogger.info).toHaveBeenCalledWith('[OpenAIInstrumentation] Found named export');
      expect(instrumentation['_wrapChatCompletions']).toHaveBeenCalled();
      expect(result[Symbol.for('lilypad.openai.instrumented')]).toBe(true);
    });

    it('should handle direct module export', () => {
      const moduleExports = mockOpenAIClass;

      // Add the _wrapChatCompletions method to the spy
      vi.spyOn(instrumentation as any, '_wrapChatCompletions').mockImplementation((prototype) => {
        if (prototype.chat?.completions) {
          mockedShimmer.wrap(prototype.chat.completions, 'create', vi.fn());
        }
      });

      instrumentation['_applyPatch'](moduleExports);

      expect(mockedLogger.info).toHaveBeenCalledWith(
        '[OpenAIInstrumentation] Using module directly',
      );
      expect(instrumentation['_wrapChatCompletions']).toHaveBeenCalled();
    });

    it('should skip if already instrumented by Lilypad', () => {
      mockModuleExports[Symbol.for('lilypad.openai.instrumented')] = true;

      const result = instrumentation['_applyPatch'](mockModuleExports);

      expect(mockedLogger.warn).toHaveBeenCalledWith(
        '[OpenAIInstrumentation] Module already instrumented by Lilypad, skipping',
      );
      expect(mockedShimmer.wrap).not.toHaveBeenCalled();
      expect(result).toBe(mockModuleExports);
    });

    it('should detect other instrumentations', () => {
      mockModuleExports[Symbol.for('dd-trace.instrumented')] = true;

      instrumentation['_applyPatch'](mockModuleExports);

      expect(mockedLogger.warn).toHaveBeenCalledWith(
        '[OpenAIInstrumentation] Detected other instrumentations:',
        'Datadog',
      );
    });

    it('should handle missing OpenAI class', () => {
      const emptyExports = {};

      const result = instrumentation['_applyPatch'](emptyExports);

      expect(mockedLogger.error).toHaveBeenCalledWith(
        '[OpenAIInstrumentation] OpenAI class not found or has no prototype',
      );
      expect(mockedShimmer.wrap).not.toHaveBeenCalled();
      expect(result).toBe(emptyExports);
    });

    it('should use proxy fallback when configured', () => {
      const emptyExports = {};
      const configuredInstrumentation = new OpenAIInstrumentation({
        fallbackToProxy: true,
      });
      configuredInstrumentation.tracer = mockTracer;

      const applyProxyFallbackSpy = vi.spyOn(
        configuredInstrumentation as any,
        '_applyProxyFallback',
      );
      configuredInstrumentation['_applyPatch'](emptyExports);

      expect(applyProxyFallbackSpy).toHaveBeenCalledWith(emptyExports);
    });
  });

  describe('_removePatch', () => {
    it('should unwrap default export', () => {
      const mockCreate = vi.fn();
      const mockOpenAIClass = class OpenAI {};
      mockOpenAIClass.prototype.chat = {
        completions: {
          create: mockCreate,
        },
      };

      const moduleExports = {
        default: mockOpenAIClass,
      };

      instrumentation['_removePatch'](moduleExports);

      expect(mockedShimmer.unwrap).toHaveBeenCalledWith(
        mockOpenAIClass.prototype.chat.completions,
        'create',
      );
    });

    it('should unwrap named export', () => {
      const mockOpenAIClass = {
        prototype: {
          chat: {
            completions: {
              create: vi.fn(),
            },
          },
        },
      };

      const moduleExports = {
        OpenAI: mockOpenAIClass,
      };

      instrumentation['_removePatch'](moduleExports);

      expect(mockedShimmer.unwrap).toHaveBeenCalledWith(
        mockOpenAIClass.prototype.chat.completions,
        'create',
      );
    });

    it('should handle missing properties gracefully', () => {
      const moduleExports = {};

      expect(() => {
        instrumentation['_removePatch'](moduleExports);
      }).not.toThrow();
    });
  });

  describe('_wrapChatCompletions', () => {
    let mockPrototype: any;
    let mockOriginalCreate: any;

    beforeEach(() => {
      mockOriginalCreate = vi.fn();
      mockPrototype = {
        chat: {
          completions: {
            create: mockOriginalCreate,
          },
        },
      };
    });

    it('should wrap chat.completions.create', () => {
      instrumentation['_wrapChatCompletions'](mockPrototype);

      expect(mockedShimmer.wrap).toHaveBeenCalledWith(
        mockPrototype.chat.completions,
        'create',
        expect.any(Function),
      );
    });

    it('should handle missing chat property', () => {
      const prototypeWithoutChat = {};

      instrumentation['_wrapChatCompletions'](prototypeWithoutChat);

      expect(mockedLogger.error).toHaveBeenCalledWith(
        '[OpenAIInstrumentation] chat not found on prototype',
      );
      expect(mockedShimmer.wrap).not.toHaveBeenCalled();
    });

    it('should handle missing create method', () => {
      const prototypeWithoutCreate = {
        chat: {
          completions: {},
        },
      };

      instrumentation['_wrapChatCompletions'](prototypeWithoutCreate);

      expect(mockedLogger.error).toHaveBeenCalledWith(
        '[OpenAIInstrumentation] chat.completions.create not found',
      );
      expect(mockedShimmer.wrap).not.toHaveBeenCalled();
    });

    it('should skip if already wrapped', () => {
      mockedIsWrapped.mockReturnValue(true);

      instrumentation['_wrapChatCompletions'](mockPrototype);

      expect(mockedLogger.debug).toHaveBeenCalledWith(
        '[OpenAIInstrumentation] chat.completions.create already wrapped',
      );
      expect(mockedShimmer.wrap).not.toHaveBeenCalled();
    });

    it('should use proxy fallback for lazy getter pattern', () => {
      const prototypeWithoutChat = {};
      const configuredInstrumentation = new OpenAIInstrumentation({
        fallbackToProxy: true,
      });
      configuredInstrumentation.tracer = mockTracer;

      const applyProxyToChatGetterSpy = vi.spyOn(
        configuredInstrumentation as any,
        '_applyProxyToChatGetter',
      );
      configuredInstrumentation['_wrapChatCompletions'](prototypeWithoutChat);

      expect(applyProxyToChatGetterSpy).toHaveBeenCalledWith(prototypeWithoutChat);
    });
  });

  describe('wrapped method behavior', () => {
    let wrappedMethod: any;
    let mockOriginalCreate: any;
    let mockContext: any;

    beforeEach(() => {
      mockOriginalCreate = vi.fn();
      mockContext = {};

      // Get the wrapper function from shimmer.wrap
      mockedShimmer.wrap.mockImplementation((target, method, wrapper) => {
        wrappedMethod = wrapper(mockOriginalCreate);
        return wrappedMethod;
      });

      mockedContext.active.mockReturnValue(mockContext);
      mockedTrace.setSpan.mockReturnValue(mockContext);
      mockedTrace.getSpan.mockReturnValue(mockSpan);

      // Apply the patch to trigger wrapping
      const mockPrototype = {
        chat: {
          completions: {
            create: mockOriginalCreate,
          },
        },
      };
      instrumentation['_wrapChatCompletions'](mockPrototype);
    });

    it('should skip when SDK is shutting down', async () => {
      mockedIsSDKShuttingDown.mockReturnValue(true);

      const params = { model: 'gpt-4' };
      mockOriginalCreate.mockResolvedValue({ choices: [] });

      await wrappedMethod.call({}, params);

      expect(mockOriginalCreate).toHaveBeenCalledWith(params);
      expect(mockTracer.startSpan).not.toHaveBeenCalled();
    });

    it('should create span with correct attributes', async () => {
      const params = {
        model: 'gpt-4',
        temperature: 0.7,
        max_tokens: 100,
        top_p: 0.9,
      };

      mockOriginalCreate.mockResolvedValue({ choices: [] });

      await wrappedMethod.call({}, params);

      expect(mockTracer.startSpan).toHaveBeenCalledWith(
        'openai.chat.completions gpt-4',
        {
          kind: SpanKind.CLIENT,
          attributes: {
            'gen_ai.system': 'openai',
            'gen_ai.request.model': 'gpt-4',
            'gen_ai.request.temperature': 0.7,
            'gen_ai.request.max_tokens': 100,
            'gen_ai.request.top_p': 0.9,
            'gen_ai.operation.name': 'chat',
            'lilypad.type': 'llm',
          },
        },
        mockContext,
      );
    });

    it('should preserve parent span context', async () => {
      const parentSpan = {
        spanContext: vi.fn(() => ({
          spanId: 'parent123',
          traceId: 'trace123',
        })),
      };
      mockedTrace.getSpan.mockReturnValue(parentSpan);

      mockOriginalCreate.mockResolvedValue({ choices: [] });

      await wrappedMethod.call({}, { model: 'gpt-4' });

      expect(mockedLogger.debug).toHaveBeenCalledWith(
        '[OpenAIInstrumentation] Found parent span:',
        expect.objectContaining({
          parentSpanId: 'parent123',
          parentTraceId: 'trace123',
        }),
      );
    });

    it('should call request hook if provided', async () => {
      const requestHook = vi.fn();
      const configuredInstrumentation = new OpenAIInstrumentation({ requestHook });
      configuredInstrumentation.tracer = mockTracer;

      // Re-wrap with configured instrumentation
      mockedShimmer.wrap.mockImplementation((target, method, wrapper) => {
        wrappedMethod = wrapper(mockOriginalCreate);
        return wrappedMethod;
      });

      const mockPrototype = {
        chat: {
          completions: {
            create: mockOriginalCreate,
          },
        },
      };
      configuredInstrumentation['_wrapChatCompletions'](mockPrototype);

      const params = { model: 'gpt-4' };
      mockOriginalCreate.mockResolvedValue({ choices: [] });

      await wrappedMethod.call({}, params);

      expect(requestHook).toHaveBeenCalledWith(mockSpan, params);
    });

    it('should record messages as events', async () => {
      const params = {
        model: 'gpt-4',
        messages: [
          { role: 'system', content: 'You are helpful' },
          { role: 'user', content: 'Hello' },
          { role: 'assistant', content: { type: 'text', text: 'Hi' } },
        ],
      };

      mockOriginalCreate.mockResolvedValue({ choices: [] });

      await wrappedMethod.call({}, params);

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
        content: '{"type":"text","text":"Hi"}',
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
          {
            message: { role: 'assistant', content: 'Hi!' },
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

      await wrappedMethod.call({}, { model: 'gpt-4' });

      // Should record all choices
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'openai',
        index: 0,
        message: '{"role":"assistant","content":"Hello!"}',
        finish_reason: 'stop',
      });
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'openai',
        index: 1,
        message: '{"role":"assistant","content":"Hi!"}',
        finish_reason: 'stop',
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

      expect(mockSpan.setStatus).toHaveBeenCalledWith({ code: SpanStatusCode.OK });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should call response hook if provided', async () => {
      const responseHook = vi.fn();
      const configuredInstrumentation = new OpenAIInstrumentation({ responseHook });
      configuredInstrumentation.tracer = mockTracer;

      // Re-wrap with configured instrumentation
      mockedShimmer.wrap.mockImplementation((target, method, wrapper) => {
        wrappedMethod = wrapper(mockOriginalCreate);
        return wrappedMethod;
      });

      const mockPrototype = {
        chat: {
          completions: {
            create: mockOriginalCreate,
          },
        },
      };
      configuredInstrumentation['_wrapChatCompletions'](mockPrototype);

      const response = { choices: [] };
      mockOriginalCreate.mockResolvedValue(response);

      await wrappedMethod.call({}, { model: 'gpt-4' });

      expect(responseHook).toHaveBeenCalledWith(mockSpan, response);
    });

    it('should handle errors', async () => {
      const error = new Error('API Error');
      mockOriginalCreate.mockRejectedValue(error);

      await expect(wrappedMethod.call({}, { model: 'gpt-4' })).rejects.toThrow('API Error');

      expect(mockSpan.recordException).toHaveBeenCalledWith(error);
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'API Error',
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should handle streaming response', async () => {
      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield { choices: [{ delta: { content: 'Hello' } }] };
          yield {
            choices: [{ delta: { content: ' world' }, finish_reason: 'stop' }],
            usage: { prompt_tokens: 5, completion_tokens: 10, total_tokens: 15 },
          };
        },
      };

      mockOriginalCreate.mockResolvedValue(mockStream);
      mockedIsAsyncIterable.mockReturnValue(true);

      const result = await wrappedMethod.call({}, { model: 'gpt-4', stream: true });

      expect(mockedStreamWrapper).toHaveBeenCalledWith(mockStream, mockSpan, {
        onChunk: expect.any(Function),
        onFinalize: expect.any(Function),
      });

      // Should return wrapped stream
      expect(result).toBeDefined();
    });
  });

  describe('_applyProxyToChatGetter', () => {
    it('should define getter for chat property', () => {
      const prototype = {};
      instrumentation['_applyProxyToChatGetter'](prototype);

      expect(Object.getOwnPropertyDescriptor(prototype, 'chat')).toBeDefined();
      expect(Object.getOwnPropertyDescriptor(prototype, 'chat')?.get).toBeDefined();
    });

    it('should wrap create method when chat is accessed', () => {
      const mockCreate = vi.fn();
      const prototype = {
        _chat: {
          completions: {
            create: mockCreate,
          },
        },
      };

      instrumentation['_applyProxyToChatGetter'](prototype);

      // Access chat to trigger lazy wrapping
      const descriptor = Object.getOwnPropertyDescriptor(prototype, 'chat');
      const chat = descriptor?.get?.call(prototype);

      expect(mockedLogger.info).toHaveBeenCalledWith(
        '[OpenAIInstrumentation] Applying lazy wrapping to chat.completions.create',
      );
      expect(mockedShimmer.wrap).toHaveBeenCalledWith(
        chat.completions,
        'create',
        expect.any(Function),
      );
    });

    it('should preserve original getter behavior', () => {
      const originalGetter = vi.fn(() => ({ completions: { create: vi.fn() } }));
      const prototype = {};
      Object.defineProperty(prototype, 'chat', {
        get: originalGetter,
        configurable: true,
      });

      instrumentation['_applyProxyToChatGetter'](prototype);

      const descriptor = Object.getOwnPropertyDescriptor(prototype, 'chat');
      descriptor?.get?.call(prototype);

      expect(originalGetter).toHaveBeenCalled();
    });

    it('should preserve setter behavior', () => {
      const originalSetter = vi.fn();
      const prototype = {};
      Object.defineProperty(prototype, 'chat', {
        set: originalSetter,
        get: () => ({}),
        configurable: true,
      });

      instrumentation['_applyProxyToChatGetter'](prototype);

      const descriptor = Object.getOwnPropertyDescriptor(prototype, 'chat');
      const newValue = { test: true };
      descriptor?.set?.call(prototype, newValue);

      expect(originalSetter).toHaveBeenCalledWith(newValue);
    });

    it('should not wrap if already wrapped', () => {
      mockedIsWrapped.mockReturnValue(true);

      const prototype = {
        _chat: {
          completions: {
            create: vi.fn(),
          },
        },
      };

      instrumentation['_applyProxyToChatGetter'](prototype);

      const descriptor = Object.getOwnPropertyDescriptor(prototype, 'chat');
      descriptor?.get?.call(prototype);

      expect(mockedShimmer.wrap).not.toHaveBeenCalled();
    });
  });

  describe('_applyProxyFallback', () => {
    it('should proxy default export', () => {
      const OriginalClass = class OpenAI {};
      const moduleExports = {
        default: OriginalClass,
      };

      const result = instrumentation['_applyProxyFallback'](moduleExports);

      expect(result.default).not.toBe(OriginalClass);
      expect(result.default).toBeDefined();
    });

    it('should proxy named export', () => {
      const OriginalClass = class OpenAI {};
      const moduleExports = {
        OpenAI: OriginalClass,
      };

      const result = instrumentation['_applyProxyFallback'](moduleExports);

      expect(result.OpenAI).not.toBe(OriginalClass);
      expect(result.OpenAI).toBeDefined();
    });

    it('should proxy function export', () => {
      const originalFunction = function OpenAI() {};
      const result = instrumentation['_applyProxyFallback'](originalFunction);

      expect(result).not.toBe(originalFunction);
      expect(typeof result).toBe('function');
    });
  });

  describe('_proxyInstance', () => {
    it('should intercept chat.completions.create access', () => {
      const mockCreate = vi.fn();
      const instance = {
        chat: {
          completions: {
            create: mockCreate,
          },
        },
      };

      const proxiedInstance = instrumentation['_proxyInstance'](instance);
      const wrappedCreate = proxiedInstance.chat.completions.create;

      expect(wrappedCreate).not.toBe(mockCreate);
      expect(typeof wrappedCreate).toBe('function');
    });

    it('should preserve other properties', () => {
      const instance = {
        otherProp: 'value',
        chat: {
          otherMethod: vi.fn(),
          completions: {
            otherMethod: vi.fn(),
            create: vi.fn(),
          },
        },
      };

      const proxiedInstance = instrumentation['_proxyInstance'](instance);

      expect(proxiedInstance.otherProp).toBe('value');
      expect(proxiedInstance.chat.otherMethod).toBe(instance.chat.otherMethod);
      expect(proxiedInstance.chat.completions.otherMethod).toBe(
        instance.chat.completions.otherMethod,
      );
    });
  });

  describe('_detectOtherInstrumentations', () => {
    it('should detect Datadog instrumentation', () => {
      const moduleExports = {
        [Symbol.for('dd-trace.instrumented')]: true,
      };

      const detected = instrumentation['_detectOtherInstrumentations'](moduleExports);

      expect(detected).toContain('Datadog');
    });

    it('should detect New Relic instrumentation', () => {
      const moduleExports = {
        __NR_instrumented: true,
      };

      const detected = instrumentation['_detectOtherInstrumentations'](moduleExports);

      expect(detected).toContain('New Relic');
    });

    it('should detect multiple instrumentations', () => {
      const moduleExports = {
        [Symbol.for('elastic-apm.instrumented')]: true,
        _appdInstrumented: true,
      };

      const detected = instrumentation['_detectOtherInstrumentations'](moduleExports);

      expect(detected).toContain('Elastic APM');
      expect(detected).toContain('AppDynamics');
    });

    it('should detect wrapped methods', () => {
      const wrappedFunction = function __wrapped() {};
      const moduleExports = {
        default: {
          prototype: {
            chat: {
              completions: {
                create: wrappedFunction,
              },
            },
          },
        },
      };

      const detected = instrumentation['_detectOtherInstrumentations'](moduleExports);

      expect(detected).toContain('Unknown (wrapped method detected)');
    });

    it('should handle null/undefined exports', () => {
      expect(instrumentation['_detectOtherInstrumentations'](null)).toEqual([]);
      expect(instrumentation['_detectOtherInstrumentations'](undefined)).toEqual([]);
    });

    it('should remove duplicates', () => {
      const moduleExports = {
        [Symbol.for('dd-trace.instrumented')]: true,
        _datadog_instrumented: true,
      };

      const detected = instrumentation['_detectOtherInstrumentations'](moduleExports);

      expect(detected).toEqual(['Datadog']);
    });
  });
});
