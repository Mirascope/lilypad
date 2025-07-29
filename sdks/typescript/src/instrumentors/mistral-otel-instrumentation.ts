import {
  InstrumentationBase,
  InstrumentationNodeModuleDefinition,
  InstrumentationConfig,
  isWrapped,
} from '@opentelemetry/instrumentation';
import { trace, SpanStatusCode, SpanKind, Span as OtelSpan, context } from '@opentelemetry/api';
import shimmer from 'shimmer';
import { logger } from '../utils/logger';
import { StreamWrapper } from '../utils/stream-wrapper';
import { isSDKShuttingDown } from '../shutdown';
import type { MistralChatParams, MistralChatResponse } from '../types/mistral';

// Import GenAI semantic conventions
import {
  SEMATTRS_GEN_AI_REQUEST_MODEL,
  SEMATTRS_GEN_AI_SYSTEM,
  SEMATTRS_GEN_AI_REQUEST_TEMPERATURE,
  SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS,
  SEMATTRS_GEN_AI_REQUEST_TOP_P,
  SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS,
  SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS,
  SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS,
  SEMATTRS_GEN_AI_OPERATION_NAME,
} from '../constants/gen-ai-semantic-conventions';

const MODULE_NAME = '@mistralai/mistralai';
const SUPPORTED_VERSIONS = ['>=0.1.0'];

export interface MistralInstrumentationConfig extends InstrumentationConfig {
  /**
   * Hook called before request is sent
   */
  requestHook?: (span: OtelSpan, params: MistralChatParams) => void;

  /**
   * Hook called after response is received
   */
  responseHook?: (span: OtelSpan, response: MistralChatResponse) => void;

  /**
   * Whether to use Proxy as fallback when shimmer fails
   */
  fallbackToProxy?: boolean;

  /**
   * Suppress internal instrumentation logs
   */
  suppressInternalInstrumentation?: boolean;
}

// Symbol to mark instrumented modules
const LILYPAD_INSTRUMENTED = Symbol.for('lilypad.mistral.instrumented');

export class MistralInstrumentation extends InstrumentationBase {
  constructor(config: MistralInstrumentationConfig = {}) {
    super('@lilypad/instrumentation-mistral', '0.1.0', config);
  }

  protected init() {
    logger.info('[MistralInstrumentation] Initializing Mistral instrumentation');
    const module = new InstrumentationNodeModuleDefinition(
      MODULE_NAME,
      SUPPORTED_VERSIONS,
      (moduleExports, moduleVersion) => {
        logger.info(
          `[MistralInstrumentation] Applying patch for @mistralai/mistralai@${moduleVersion}`,
        );
        return this._applyPatch(moduleExports);
      },
      (moduleExports, moduleVersion) => {
        logger.info(
          `[MistralInstrumentation] Removing patch for @mistralai/mistralai@${moduleVersion}`,
        );
        return this._removePatch(moduleExports);
      },
    );

    return [module];
  }

  private _applyPatch(moduleExports: any): any {
    // Check if already instrumented by Lilypad
    if (moduleExports && moduleExports[LILYPAD_INSTRUMENTED]) {
      logger.warn('[MistralInstrumentation] Module already instrumented by Lilypad, skipping');
      return moduleExports;
    }

    // Check for other instrumentation libraries
    const otherInstrumentations = this._detectOtherInstrumentations(moduleExports);
    if (otherInstrumentations.length > 0) {
      logger.warn(
        '[MistralInstrumentation] Detected other instrumentations:',
        otherInstrumentations.join(', '),
      );
      if (!(this._config as MistralInstrumentationConfig).suppressInternalInstrumentation) {
        logger.warn('[MistralInstrumentation] Proceeding with caution - may cause conflicts');
      }
    }

    logger.debug('[MistralInstrumentation] Patching Mistral module');
    logger.debug('[MistralInstrumentation] Module exports:', Object.keys(moduleExports || {}));

    // Handle different export patterns
    let MistralClass: any;
    if (moduleExports.default) {
      MistralClass = moduleExports.default;
      logger.debug('[MistralInstrumentation] Found default export');
    } else if (moduleExports.MistralClient) {
      MistralClass = moduleExports.MistralClient;
      logger.debug('[MistralInstrumentation] Found MistralClient export');
    } else if (moduleExports.Mistral) {
      MistralClass = moduleExports.Mistral;
      logger.debug('[MistralInstrumentation] Found Mistral export');
    } else {
      MistralClass = moduleExports;
      logger.debug('[MistralInstrumentation] Using module directly');
    }

    if (!MistralClass || !MistralClass.prototype) {
      logger.error('[MistralInstrumentation] Mistral class not found or has no prototype');
      if ((this._config as MistralInstrumentationConfig).fallbackToProxy) {
        return this._applyProxyFallback(moduleExports);
      }
      return moduleExports;
    }

    // Apply shimmer to wrap the methods
    this._wrapChatMethods(MistralClass.prototype);
    logger.debug('[MistralInstrumentation] Successfully applied patch');

    // Mark as instrumented by Lilypad
    Object.defineProperty(moduleExports, LILYPAD_INSTRUMENTED, {
      value: true,
      enumerable: false,
      configurable: false,
      writable: false,
    });

    return moduleExports;
  }

  private _removePatch(moduleExports: any): any {
    logger.debug('[MistralInstrumentation] Removing Mistral patches');

    let MistralClass: any;
    if (moduleExports.default) {
      MistralClass = moduleExports.default;
    } else if (moduleExports.MistralClient) {
      MistralClass = moduleExports.MistralClient;
    } else if (moduleExports.Mistral) {
      MistralClass = moduleExports.Mistral;
    } else {
      MistralClass = moduleExports;
    }

    if (MistralClass?.prototype?.chat) {
      // Check if it's the new structure
      const chatObj = MistralClass.prototype.chat;
      if (typeof chatObj === 'object' && chatObj._lilypadWrapped) {
        if (chatObj.complete) {
          shimmer.unwrap(chatObj, 'complete');
        }
        if (chatObj.stream) {
          shimmer.unwrap(chatObj, 'stream');
        }
      } else if (typeof chatObj === 'function') {
        // Legacy structure
        shimmer.unwrap(MistralClass.prototype, 'chat');
      }
    }
    if (MistralClass?.prototype?.chatStream) {
      shimmer.unwrap(MistralClass.prototype, 'chatStream');
    }

    return moduleExports;
  }

  private _wrapChatMethods(prototype: any): void {
    const instrumentation = this;

    // Check if chat is a getter property (new SDK structure)
    const chatDescriptor = Object.getOwnPropertyDescriptor(prototype, 'chat');

    if (chatDescriptor && chatDescriptor.get) {
      logger.debug('[MistralInstrumentation] Found chat getter on prototype, wrapping it');

      const originalGetter = chatDescriptor.get;
      const wrappedInstances = new WeakSet();

      Object.defineProperty(prototype, 'chat', {
        get: function () {
          const chatObj = originalGetter.call(this);

          if (chatObj && !wrappedInstances.has(chatObj)) {
            logger.debug('[MistralInstrumentation] Wrapping chat methods on instance');

            // Wrap complete method
            if (chatObj.complete && !isWrapped(chatObj.complete)) {
              const originalComplete = chatObj.complete;
              chatObj.complete = instrumentation._createWrappedChatMethod(
                originalComplete.bind(chatObj),
              );
              logger.info('[MistralInstrumentation] Successfully wrapped chat.complete');
            }

            // Wrap stream method
            if (chatObj.stream && !isWrapped(chatObj.stream)) {
              const originalStream = chatObj.stream;
              chatObj.stream = instrumentation._createWrappedChatStreamMethod(
                originalStream.bind(chatObj),
              );
              logger.info('[MistralInstrumentation] Successfully wrapped chat.stream');
            }

            wrappedInstances.add(chatObj);
          }

          return chatObj;
        },
        set: chatDescriptor.set,
        enumerable: chatDescriptor.enumerable,
        configurable: chatDescriptor.configurable,
      });

      return;
    }

    // Check for direct chat object (shouldn't happen with new SDK)
    if (prototype.chat && typeof prototype.chat === 'object') {
      logger.debug('[MistralInstrumentation] Found chat object directly on prototype (unexpected)');
    }

    // Legacy method names (for older SDK versions)
    if (prototype.chat && typeof prototype.chat === 'function') {
      if (isWrapped(prototype.chat)) {
        logger.debug('[MistralInstrumentation] chat already wrapped');
      } else {
        shimmer.wrap(prototype, 'chat', (original: Function) => {
          return instrumentation._createWrappedChatMethod(original);
        });
        logger.debug('[MistralInstrumentation] Successfully wrapped chat (legacy)');
      }
    }

    if (prototype.chatStream) {
      if (isWrapped(prototype.chatStream)) {
        logger.debug('[MistralInstrumentation] chatStream already wrapped');
      } else {
        shimmer.wrap(prototype, 'chatStream', (original: Function) => {
          return instrumentation._createWrappedChatStreamMethod(original);
        });
        logger.debug('[MistralInstrumentation] Successfully wrapped chatStream (legacy)');
      }
    }

    // If neither method exists directly, try lazy loading pattern
    if (!prototype.chat && !prototype.chatStream) {
      logger.warn('[MistralInstrumentation] Neither chat nor chatStream found on prototype');
      if ((this._config as MistralInstrumentationConfig).fallbackToProxy) {
        logger.info('[MistralInstrumentation] Applying lazy loading workaround');
        this._applyLazyLoadingWorkaround(prototype);
      }
    }
  }

  private _createWrappedChatMethod(original: Function): Function {
    const instrumentation = this;
    return async function (this: any, ...args: any[]) {
      // Skip if shutting down
      if (isSDKShuttingDown()) {
        return original.apply(this, args);
      }

      const [params] = args;
      const tracer = instrumentation.tracer;
      const config = instrumentation._config as MistralInstrumentationConfig;

      // Get the active context to preserve parent-child relationships
      const activeContext = context.active();
      const parentSpan = trace.getSpan(activeContext);

      if (parentSpan) {
        logger.debug('[MistralInstrumentation] Found parent span:', {
          parentSpanId: parentSpan.spanContext().spanId,
          parentTraceId: parentSpan.spanContext().traceId,
          parentSpanName: (parentSpan as any).name || 'unknown',
        });
      } else {
        logger.debug('[MistralInstrumentation] No parent span found in context');
      }

      // Start span using the OTel way with active context
      const span = tracer.startSpan(
        `mistral.chat ${params?.model || 'unknown'}`,
        {
          kind: SpanKind.CLIENT,
          attributes: {
            [SEMATTRS_GEN_AI_SYSTEM]: 'mistral',
            [SEMATTRS_GEN_AI_REQUEST_MODEL]: params?.model,
            [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: params?.temperature,
            [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: params?.maxTokens || params?.max_tokens,
            [SEMATTRS_GEN_AI_REQUEST_TOP_P]: params?.top_p,
            [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
            'lilypad.type': 'llm',
            'server.address': 'api.mistral.ai',
            'gen_ai.request.safe_prompt': params?.safe_prompt,
            'gen_ai.request.random_seed': params?.random_seed,
          },
        },
        activeContext,
      );

      logger.debug('[MistralInstrumentation] Created Mistral span:', {
        spanId: span.spanContext().spanId,
        traceId: span.spanContext().traceId,
        parentSpanId: (span as any).parentSpanId,
      });

      // Set span in context for proper context propagation
      const contextWithSpan = trace.setSpan(context.active(), span);

      return context.with(contextWithSpan, async () => {
        try {
          // Call request hook if provided
          if (config.requestHook) {
            config.requestHook(span, params);
          }

          // Record messages
          if (params?.messages) {
            params.messages.forEach((message: any) => {
              span.addEvent(`gen_ai.${message.role}.message`, {
                'gen_ai.system': 'mistral',
                content: message.content,
              });
            });
          }

          // Call original method
          const result = await original.apply(this, args);

          // Handle regular response
          instrumentation._recordResponse(span, result);

          // Call response hook if provided
          if (config.responseHook) {
            config.responseHook(span, result);
          }

          span.setStatus({ code: SpanStatusCode.OK });
          return result;
        } catch (error) {
          span.recordException(error as Error);
          span.setStatus({
            code: SpanStatusCode.ERROR,
            message: error instanceof Error ? error.message : String(error),
          });
          throw error;
        } finally {
          span.end();
        }
      });
    };
  }

  private _createWrappedChatStreamMethod(original: Function): Function {
    const instrumentation = this;
    return async function* (this: any, ...args: any[]) {
      // Skip if shutting down
      if (isSDKShuttingDown()) {
        yield* original.apply(this, args);
        return;
      }

      const [params] = args;
      const tracer = instrumentation.tracer;
      const config = instrumentation._config as MistralInstrumentationConfig;

      // Get the active context to preserve parent-child relationships
      const activeContext = context.active();

      // Start span using the OTel way with active context
      const span = tracer.startSpan(
        `mistral.chat_stream ${params?.model || 'unknown'}`,
        {
          kind: SpanKind.CLIENT,
          attributes: {
            [SEMATTRS_GEN_AI_SYSTEM]: 'mistral',
            [SEMATTRS_GEN_AI_REQUEST_MODEL]: params?.model,
            [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: params?.temperature,
            [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: params?.maxTokens || params?.max_tokens,
            [SEMATTRS_GEN_AI_REQUEST_TOP_P]: params?.top_p,
            [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
            'lilypad.type': 'llm',
            'server.address': 'api.mistral.ai',
            'gen_ai.request.safe_prompt': params?.safe_prompt,
            'gen_ai.request.random_seed': params?.random_seed,
          },
        },
        activeContext,
      );

      // Set span in context for proper context propagation
      const contextWithSpan = trace.setSpan(context.active(), span);

      // Use yield* to properly handle the async generator within context
      const self = this;
      yield* await context.with(contextWithSpan, async function* () {
        try {
          // Call request hook if provided
          if (config.requestHook) {
            config.requestHook(span, params);
          }

          // Record messages
          if (params?.messages) {
            params.messages.forEach((message: any) => {
              span.addEvent(`gen_ai.${message.role}.message`, {
                'gen_ai.system': 'mistral',
                content: message.content,
              });
            });
          }

          // Call original method - it might return a Promise<AsyncIterable>
          const streamOrPromise = original.apply(self, args);

          // Wait for the stream if it's a promise
          const stream = await streamOrPromise;

          // Debug stream type
          if (process.env.LILYPAD_DEBUG === 'true') {
            logger.debug('[MistralInstrumentation] Stream type:', {
              type: typeof stream,
              constructor: stream?.constructor?.name,
              isAsyncIterable:
                stream && typeof stream === 'object' && Symbol.asyncIterator in stream,
              keys: stream ? Object.keys(stream) : [],
            });
          }

          // Wrap the stream
          const wrapper = instrumentation._wrapStream(span, stream, config);
          for await (const chunk of wrapper) {
            yield chunk;
          }
        } catch (error) {
          span.recordException(error as Error);
          span.setStatus({
            code: SpanStatusCode.ERROR,
            message: error instanceof Error ? error.message : String(error),
          });
          span.end();
          throw error;
        }
      });
    };
  }

  private _wrapStream(
    span: OtelSpan,
    stream: AsyncIterable<any>,
    _config: MistralInstrumentationConfig,
  ): AsyncIterable<any> {
    let content = '';
    let finishReason: string | null = null;
    let model: string | null = null;

    const onChunk = (rawChunk: any) => {
      // Handle wrapped format from Mistral SDK
      const chunk = rawChunk.data || rawChunk;

      if (chunk.model && !model) {
        model = chunk.model;
      }

      if (chunk.choices && chunk.choices.length > 0) {
        const delta = chunk.choices[0].delta;
        if (delta?.content) {
          content += delta.content;
        }
        if (chunk.choices[0].finish_reason || chunk.choices[0].finishReason) {
          finishReason = chunk.choices[0].finish_reason || chunk.choices[0].finishReason;
        }
      }

      // Add chunk event
      span.addEvent('gen_ai.chunk', {
        size: chunk.choices?.[0]?.delta?.content?.length || 0,
      });
    };

    const onFinalize = () => {
      // Record the completed stream
      if (content) {
        span.addEvent('gen_ai.choice', {
          'gen_ai.system': 'mistral',
          index: 0,
          message: JSON.stringify({ role: 'assistant', content: content }),
          finish_reason: finishReason || 'stop',
        });
      }

      if (finishReason) {
        span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, [finishReason]);
      }

      if (model) {
        span.setAttribute('gen_ai.response.model', model);
      }

      // Note: Mistral streaming doesn't typically include usage in chunks
      // If it does in the future, record it here

      span.setStatus({ code: SpanStatusCode.OK });
      span.end();
    };

    return new StreamWrapper(stream, span, { onChunk, onFinalize });
  }

  private _recordResponse(span: OtelSpan, response: any): void {
    if (!response) return;

    // Record response attributes
    if (response.choices && response.choices.length > 0) {
      response.choices.forEach((choice: any, index: number) => {
        if (choice.message) {
          // Match Python's event format
          span.addEvent('gen_ai.choice', {
            'gen_ai.system': 'mistral',
            index: index,
            message: JSON.stringify(choice.message),
            finish_reason: choice.finish_reason || '',
          });
        }
      });

      // Record finish reason from first choice
      const firstChoice = response.choices[0];
      if (firstChoice?.finish_reason) {
        span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, [firstChoice.finish_reason]);
      }
    }

    // Record usage
    if (response.usage) {
      span.setAttributes({
        [SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS]: response.usage.prompt_tokens,
        [SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS]: response.usage.completion_tokens,
        'gen_ai.usage.total_tokens': response.usage.total_tokens,
      });
    }

    // Record model (might be different from requested)
    if (response.model) {
      span.setAttribute('gen_ai.response.model', response.model);
    }

    // Record ID
    if (response.id) {
      span.setAttribute('gen_ai.response.id', response.id);
    }
  }

  private _applyLazyLoadingWorkaround(prototype: any): void {
    const instrumentation = this;

    // Define getters for both methods
    Object.defineProperty(prototype, 'chat', {
      get: function () {
        if (!this._chat) {
          return undefined;
        }
        if (!this._wrappedChat) {
          this._wrappedChat = instrumentation._createWrappedChatMethod(this._chat.bind(this));
        }
        return this._wrappedChat;
      },
      set: function (value) {
        this._chat = value;
        this._wrappedChat = null; // Reset wrapped version
      },
      configurable: true,
      enumerable: true,
    });

    Object.defineProperty(prototype, 'chatStream', {
      get: function () {
        if (!this._chatStream) {
          return undefined;
        }
        if (!this._wrappedChatStream) {
          this._wrappedChatStream = instrumentation._createWrappedChatStreamMethod(
            this._chatStream.bind(this),
          );
        }
        return this._wrappedChatStream;
      },
      set: function (value) {
        this._chatStream = value;
        this._wrappedChatStream = null; // Reset wrapped version
      },
      configurable: true,
      enumerable: true,
    });
  }

  private _applyProxyFallback(moduleExports: any): any {
    logger.debug('[MistralInstrumentation] Applying Proxy fallback');

    const instrumentation = this;
    const handler = {
      construct(target: any, args: any[]) {
        const instance = new target(...args);
        return instrumentation._proxyInstance(instance);
      },
    };

    if (moduleExports.default) {
      moduleExports.default = new Proxy(moduleExports.default, handler);
    } else if (moduleExports.MistralClient) {
      moduleExports.MistralClient = new Proxy(moduleExports.MistralClient, handler);
    } else if (moduleExports.Mistral) {
      moduleExports.Mistral = new Proxy(moduleExports.Mistral, handler);
    } else if (typeof moduleExports === 'function') {
      return new Proxy(moduleExports, handler);
    }

    return moduleExports;
  }

  private _proxyInstance(instance: any): any {
    const instrumentation = this;

    // Deep proxy to intercept method calls
    const handler: ProxyHandler<any> = {
      get(target, prop, receiver) {
        const value = Reflect.get(target, prop, receiver);

        // Intercept chat method
        if (prop === 'chat' && typeof value === 'function') {
          return instrumentation._createWrappedChatMethod(value.bind(target));
        }

        // Intercept chatStream method
        if (prop === 'chatStream' && typeof value === 'function') {
          return instrumentation._createWrappedChatStreamMethod(value.bind(target));
        }

        return value;
      },
    };

    return new Proxy(instance, handler);
  }

  private _detectOtherInstrumentations(moduleExports: any): string[] {
    const detectedInstrumentations: string[] = [];

    if (!moduleExports) return detectedInstrumentations;

    // Check for common instrumentation markers
    const markers = [
      // Datadog
      { symbol: Symbol.for('dd-trace.instrumented'), name: 'Datadog' },
      { symbol: Symbol.for('datadog.instrumented'), name: 'Datadog' },
      { property: '_datadog_instrumented', name: 'Datadog' },

      // New Relic
      { symbol: Symbol.for('newrelic.instrumented'), name: 'New Relic' },
      { property: '__NR_instrumented', name: 'New Relic' },

      // AppDynamics
      { symbol: Symbol.for('appdynamics.instrumented'), name: 'AppDynamics' },
      { property: '_appdInstrumented', name: 'AppDynamics' },

      // Elastic APM
      { symbol: Symbol.for('elastic-apm.instrumented'), name: 'Elastic APM' },
      { property: '_elasticAPMInstrumented', name: 'Elastic APM' },

      // AWS X-Ray
      { symbol: Symbol.for('aws-xray.instrumented'), name: 'AWS X-Ray' },
      { property: '_awsXrayInstrumented', name: 'AWS X-Ray' },

      // Generic OpenTelemetry
      { symbol: Symbol.for('opentelemetry.instrumentation'), name: 'OpenTelemetry' },
      { property: '__otel_instrumented', name: 'OpenTelemetry' },
    ];

    // Check symbols
    for (const marker of markers) {
      if (marker.symbol && moduleExports[marker.symbol]) {
        detectedInstrumentations.push(marker.name);
      }
      if (marker.property && moduleExports[marker.property]) {
        detectedInstrumentations.push(marker.name);
      }
    }

    // Check if methods have been wrapped (common patterns)
    const checkWrapped = (obj: any, path: string[]) => {
      try {
        let current = obj;
        for (const prop of path) {
          current = current?.[prop];
        }

        if (current && typeof current === 'function') {
          // Check for common wrapper patterns
          const funcStr = current.toString();
          if (
            funcStr.includes('__wrapped') ||
            funcStr.includes('_original') ||
            funcStr.includes('__original__') ||
            funcStr.length < 100
          ) {
            // Wrapper functions are typically short
            return true;
          }
        }
      } catch {
        // Ignore errors when checking
      }
      return false;
    };

    // Check Mistral specific paths
    const mistralPaths = [
      ['default', 'prototype', 'chat'],
      ['MistralClient', 'prototype', 'chat'],
      ['Mistral', 'prototype', 'chat'],
      ['prototype', 'chat'],
      ['default', 'prototype', 'chatStream'],
      ['MistralClient', 'prototype', 'chatStream'],
      ['Mistral', 'prototype', 'chatStream'],
      ['prototype', 'chatStream'],
    ];

    for (const path of mistralPaths) {
      if (checkWrapped(moduleExports, path)) {
        detectedInstrumentations.push('Unknown (wrapped method detected)');
        break;
      }
    }

    // Remove duplicates
    return [...new Set(detectedInstrumentations)];
  }
}
