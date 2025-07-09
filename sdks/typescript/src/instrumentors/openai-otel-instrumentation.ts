import {
  InstrumentationBase,
  InstrumentationNodeModuleDefinition,
  InstrumentationConfig,
  isWrapped,
} from '@opentelemetry/instrumentation';
import { trace, SpanStatusCode, SpanKind, Span as OtelSpan, context } from '@opentelemetry/api';
import shimmer from 'shimmer';
import { logger } from '../utils/logger';
import { StreamWrapper, isAsyncIterable } from '../utils/stream-wrapper';
import { isSDKShuttingDown } from '../shutdown';
import type {
  ChatCompletionParams,
  ChatCompletionResponse,
  ChatCompletionChunk,
} from '../types/openai';

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

const MODULE_NAME = 'openai';
const SUPPORTED_VERSIONS = ['>=4.0.0'];

export interface OpenAIInstrumentationConfig extends InstrumentationConfig {
  /**
   * Hook called before request is sent
   */
  requestHook?: (span: OtelSpan, params: ChatCompletionParams) => void;

  /**
   * Hook called after response is received
   */
  responseHook?: (span: OtelSpan, response: ChatCompletionResponse) => void;

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
const LILYPAD_INSTRUMENTED = Symbol.for('lilypad.openai.instrumented');

export class OpenAIInstrumentation extends InstrumentationBase {
  constructor(config: OpenAIInstrumentationConfig = {}) {
    super('@lilypad/instrumentation-openai', '0.1.0', config);
  }

  protected init() {
    logger.info('[OpenAIInstrumentation] Initializing OpenAI instrumentation');
    const module = new InstrumentationNodeModuleDefinition(
      MODULE_NAME,
      SUPPORTED_VERSIONS,
      (moduleExports, moduleVersion) => {
        logger.info(`[OpenAIInstrumentation] Applying patch for openai@${moduleVersion}`);
        return this._applyPatch(moduleExports);
      },
      (moduleExports, moduleVersion) => {
        logger.info(`[OpenAIInstrumentation] Removing patch for openai@${moduleVersion}`);
        return this._removePatch(moduleExports);
      },
    );

    return [module];
  }

  private _applyPatch(moduleExports: any): any {
    // Check if already instrumented by Lilypad
    if (moduleExports && moduleExports[LILYPAD_INSTRUMENTED]) {
      logger.warn('[OpenAIInstrumentation] Module already instrumented by Lilypad, skipping');
      return moduleExports;
    }

    // Check for other instrumentation libraries
    const otherInstrumentations = this._detectOtherInstrumentations(moduleExports);
    if (otherInstrumentations.length > 0) {
      logger.warn(
        '[OpenAIInstrumentation] Detected other instrumentations:',
        otherInstrumentations.join(', '),
      );
      if (!(this._config as OpenAIInstrumentationConfig).suppressInternalInstrumentation) {
        logger.warn('[OpenAIInstrumentation] Proceeding with caution - may cause conflicts');
      }
    }

    logger.info('[OpenAIInstrumentation] Patching OpenAI module');
    logger.info('[OpenAIInstrumentation] Module exports:', Object.keys(moduleExports || {}));

    // Handle different export patterns
    let OpenAIClass: any;
    if (moduleExports.default) {
      OpenAIClass = moduleExports.default;
      logger.info('[OpenAIInstrumentation] Found default export');
    } else if (moduleExports.OpenAI) {
      OpenAIClass = moduleExports.OpenAI;
      logger.info('[OpenAIInstrumentation] Found named export');
    } else {
      OpenAIClass = moduleExports;
      logger.info('[OpenAIInstrumentation] Using module directly');
    }

    if (!OpenAIClass || !OpenAIClass.prototype) {
      logger.error('[OpenAIInstrumentation] OpenAI class not found or has no prototype');
      if ((this._config as OpenAIInstrumentationConfig).fallbackToProxy) {
        return this._applyProxyFallback(moduleExports);
      }
      return moduleExports;
    }

    // Apply shimmer to wrap the method
    this._wrapChatCompletions(OpenAIClass.prototype);
    logger.info('[OpenAIInstrumentation] Successfully applied patch');

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
    logger.debug('[OpenAIInstrumentation] Removing OpenAI patches');

    let OpenAIClass: any;
    if (moduleExports.default) {
      OpenAIClass = moduleExports.default;
    } else if (moduleExports.OpenAI) {
      OpenAIClass = moduleExports.OpenAI;
    } else {
      OpenAIClass = moduleExports;
    }

    if (OpenAIClass?.prototype?.chat?.completions?.create) {
      shimmer.unwrap(OpenAIClass.prototype.chat.completions, 'create');
    }

    return moduleExports;
  }

  private _wrapChatCompletions(prototype: any): void {
    const instrumentation = this;

    // Check if prototype chain has chat.completions.create
    if (!prototype.chat) {
      // Try to use Proxy if lazy getter pattern is detected
      if ((this._config as OpenAIInstrumentationConfig).fallbackToProxy) {
        logger.info('[OpenAIInstrumentation] chat not found, applying Proxy fallback');
        this._applyProxyToChatGetter(prototype);
        return;
      }
      logger.error('[OpenAIInstrumentation] chat not found on prototype');
      return;
    }

    if (!prototype.chat.completions?.create) {
      logger.error('[OpenAIInstrumentation] chat.completions.create not found');
      return;
    }

    if (isWrapped(prototype.chat.completions.create)) {
      logger.debug('[OpenAIInstrumentation] chat.completions.create already wrapped');
      return;
    }

    shimmer.wrap(prototype.chat.completions, 'create', (original: Function) => {
      return async function (this: any, ...args: any[]) {
        // Skip if shutting down
        if (isSDKShuttingDown()) {
          return original.apply(this, args);
        }

        const [params] = args;
        const tracer = instrumentation.tracer;
        const config = instrumentation._config as OpenAIInstrumentationConfig;

        // Start span using the OTel way
        const span = tracer.startSpan(`openai.chat.completions ${params?.model || 'unknown'}`, {
          kind: SpanKind.CLIENT,
          attributes: {
            [SEMATTRS_GEN_AI_SYSTEM]: 'openai',
            [SEMATTRS_GEN_AI_REQUEST_MODEL]: params?.model,
            [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: params?.temperature,
            [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: params?.max_tokens,
            [SEMATTRS_GEN_AI_REQUEST_TOP_P]: params?.top_p,
            [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
            'lilypad.type': 'llm',
          },
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
                  'gen_ai.system': 'openai',
                  content:
                    typeof message.content === 'string'
                      ? message.content
                      : JSON.stringify(message.content),
                });
              });
            }

            // Call original method
            const result = await original.apply(this, args);

            // Handle streaming
            if (params?.stream && isAsyncIterable(result)) {
              return instrumentation._wrapStream(
                span,
                result as AsyncIterable<ChatCompletionChunk>,
                config,
              );
            }

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
      } as typeof original;
    });

    logger.debug('[OpenAIInstrumentation] Successfully wrapped chat.completions.create');
  }

  private _applyProxyToChatGetter(prototype: any): void {
    const instrumentation = this;

    // Store the original property descriptor
    const originalDescriptor = Object.getOwnPropertyDescriptor(prototype, 'chat');

    // Define a getter that applies wrapping when chat is accessed
    Object.defineProperty(prototype, 'chat', {
      get: function () {
        // Get the original chat object
        const chat =
          originalDescriptor && originalDescriptor.get
            ? originalDescriptor.get.call(this)
            : this._chat;

        if (
          chat &&
          chat.completions &&
          chat.completions.create &&
          !isWrapped(chat.completions.create)
        ) {
          logger.info('[OpenAIInstrumentation] Applying lazy wrapping to chat.completions.create');
          shimmer.wrap(chat.completions, 'create', (original: Function) => {
            return instrumentation._createWrappedMethod(original);
          });
        }

        return chat;
      },
      set: function (value) {
        if (originalDescriptor && originalDescriptor.set) {
          originalDescriptor.set.call(this, value);
        } else {
          this._chat = value;
        }
      },
      configurable: true,
      enumerable: true,
    });
  }

  private _createWrappedMethod(original: Function): Function {
    const instrumentation = this;
    return async function (this: any, ...args: any[]) {
      // Skip if shutting down
      if (isSDKShuttingDown()) {
        return original.apply(this, args);
      }

      const [params] = args;
      const tracer = instrumentation.tracer;
      const config = instrumentation._config as OpenAIInstrumentationConfig;

      // Use the same span creation logic as the main wrapped method
      const span = tracer.startSpan(`chat ${params?.model || 'unknown'}`, {
        kind: SpanKind.CLIENT,
        attributes: {
          [SEMATTRS_GEN_AI_SYSTEM]: 'openai',
          'server.address': 'api.openai.com',
          [SEMATTRS_GEN_AI_REQUEST_MODEL]: params?.model,
          [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: params?.temperature,
          [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: params?.max_tokens,
          [SEMATTRS_GEN_AI_REQUEST_TOP_P]: params?.top_p,
          [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
        },
      });

      return context.with(trace.setSpan(context.active(), span), async () => {
        try {
          // Call request hook
          if (config.requestHook) {
            config.requestHook(span, params);
          }

          // Record messages
          if (params?.messages) {
            params.messages.forEach((message: any) => {
              span.addEvent(`gen_ai.${message.role}.message`, {
                'gen_ai.system': 'openai',
                content:
                  typeof message.content === 'string'
                    ? message.content
                    : JSON.stringify(message.content),
              });
            });
          }

          // Call original
          const result = await original.apply(this, args);

          // Handle streaming
          if (params?.stream && isAsyncIterable(result)) {
            return instrumentation._wrapStream(
              span,
              result as AsyncIterable<ChatCompletionChunk>,
              config,
            );
          }

          // Handle regular response
          instrumentation._recordResponse(span, result);

          // Call response hook
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
          if (!params?.stream) {
            span.end();
          }
        }
      });
    };
  }

  private _wrapStream(
    span: OtelSpan,
    stream: AsyncIterable<ChatCompletionChunk>,
    _config: OpenAIInstrumentationConfig,
  ): AsyncIterable<ChatCompletionChunk> {
    let content = '';
    let finishReason: string | null = null;
    let usage: any = null;

    const onChunk = (chunk: ChatCompletionChunk) => {
      if (chunk.choices && chunk.choices.length > 0) {
        const delta = chunk.choices[0].delta;
        if (delta?.content) {
          content += delta.content;
        }
        if (chunk.choices[0].finish_reason) {
          finishReason = chunk.choices[0].finish_reason;
        }
      }
      // Capture usage data if present
      if (chunk.usage) {
        usage = chunk.usage;
      }

      // Add chunk event
      span.addEvent('gen_ai.chunk', {
        size: chunk.choices?.[0]?.delta?.content?.length || 0,
      });
    };

    const onFinalize = () => {
      // Record the completed stream
      if (content) {
        span.addEvent('gen_ai.assistant.message', {
          'gen_ai.system': 'openai',
          content: content,
        });
      }

      if (finishReason) {
        span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, [finishReason]);
      }

      // Record usage if available
      if (usage) {
        span.setAttributes({
          [SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS]: usage.prompt_tokens,
          [SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS]: usage.completion_tokens,
          'gen_ai.usage.total_tokens': usage.total_tokens,
        });
      }

      span.setStatus({ code: SpanStatusCode.OK });
      span.end();
    };

    return new StreamWrapper(stream, span, { onChunk, onFinalize });
  }

  private _recordResponse(span: OtelSpan, response: any): void {
    if (!response) return;

    // Record response attributes
    if (response.choices && response.choices.length > 0) {
      response.choices.forEach((choice: any) => {
        if (choice.message) {
          span.addEvent('gen_ai.assistant.message', {
            'gen_ai.system': 'openai',
            content: choice.message.content || '',
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
  }

  private _applyProxyFallback(moduleExports: any): any {
    logger.debug('[OpenAIInstrumentation] Applying Proxy fallback');

    const instrumentation = this;
    const handler = {
      construct(target: any, args: any[]) {
        const instance = new target(...args);
        return instrumentation._proxyInstance(instance);
      },
    };

    if (moduleExports.default) {
      moduleExports.default = new Proxy(moduleExports.default, handler);
    } else if (moduleExports.OpenAI) {
      moduleExports.OpenAI = new Proxy(moduleExports.OpenAI, handler);
    } else if (typeof moduleExports === 'function') {
      return new Proxy(moduleExports, handler);
    }

    return moduleExports;
  }

  private _proxyInstance(instance: any): any {
    const instrumentation = this;

    // Deep proxy to intercept nested method calls
    const handler: ProxyHandler<any> = {
      get(target, prop, receiver) {
        const value = Reflect.get(target, prop, receiver);

        // Intercept chat.completions.create
        if (prop === 'chat') {
          return new Proxy(value, {
            get(chatTarget, chatProp) {
              const chatValue = Reflect.get(chatTarget, chatProp);

              if (chatProp === 'completions') {
                return new Proxy(chatValue, {
                  get(completionsTarget, completionsProp) {
                    const completionsValue = Reflect.get(completionsTarget, completionsProp);

                    if (completionsProp === 'create') {
                      return instrumentation._wrapMethod(completionsValue.bind(completionsTarget));
                    }

                    return completionsValue;
                  },
                });
              }

              return chatValue;
            },
          });
        }

        return value;
      },
    };

    return new Proxy(instance, handler);
  }

  private _wrapMethod(original: Function): Function {
    const instrumentation = this;
    return async function (this: any, ...args: any[]) {
      // Skip if shutting down
      if (isSDKShuttingDown()) {
        return original.apply(this, args);
      }

      const [params] = args;
      const tracer = instrumentation.tracer;
      const config = instrumentation._config as OpenAIInstrumentationConfig;

      // Create span
      const span = tracer.startSpan(`chat ${params?.model || 'unknown'}`, {
        kind: SpanKind.CLIENT,
        attributes: {
          [SEMATTRS_GEN_AI_SYSTEM]: 'openai',
          'server.address': 'api.openai.com',
          [SEMATTRS_GEN_AI_REQUEST_MODEL]: params?.model,
          [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: params?.temperature,
          [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: params?.max_tokens,
          [SEMATTRS_GEN_AI_REQUEST_TOP_P]: params?.top_p,
          [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
        },
      });

      return context.with(trace.setSpan(context.active(), span), async () => {
        try {
          // Call request hook
          if (config.requestHook) {
            config.requestHook(span, params);
          }

          // Record messages
          if (params?.messages) {
            params.messages.forEach((message: any) => {
              span.addEvent(`gen_ai.${message.role}.message`, {
                'gen_ai.system': 'openai',
                content:
                  typeof message.content === 'string'
                    ? message.content
                    : JSON.stringify(message.content),
              });
            });
          }

          // Call original
          const result = await original.apply(this, args);

          // Handle streaming
          if (params?.stream && isAsyncIterable(result)) {
            return instrumentation._wrapStream(
              span,
              result as AsyncIterable<ChatCompletionChunk>,
              config,
            );
          }

          // Handle regular response
          instrumentation._recordResponse(span, result);

          // Call response hook
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
          if (!params?.stream) {
            span.end();
          }
        }
      });
    };
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

    // Check OpenAI specific paths
    const openAIPaths = [
      ['default', 'prototype', 'chat', 'completions', 'create'],
      ['OpenAI', 'prototype', 'chat', 'completions', 'create'],
      ['prototype', 'chat', 'completions', 'create'],
    ];

    for (const path of openAIPaths) {
      if (checkWrapped(moduleExports, path)) {
        detectedInstrumentations.push('Unknown (wrapped method detected)');
        break;
      }
    }

    // Remove duplicates
    return [...new Set(detectedInstrumentations)];
  }
}
