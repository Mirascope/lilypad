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
  AnthropicMessageParams,
  AnthropicMessageResponse,
  AnthropicMessageChunk,
} from '../types/anthropic';

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

const MODULE_NAME = '@anthropic-ai/sdk';
const SUPPORTED_VERSIONS = ['>=0.1.0'];

export interface AnthropicInstrumentationConfig extends InstrumentationConfig {
  /**
   * Hook called before request is sent
   */
  requestHook?: (span: OtelSpan, params: AnthropicMessageParams) => void;

  /**
   * Hook called after response is received
   */
  responseHook?: (span: OtelSpan, response: AnthropicMessageResponse) => void;

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
const LILYPAD_INSTRUMENTED = Symbol.for('lilypad.anthropic.instrumented');

export class AnthropicInstrumentation extends InstrumentationBase {
  constructor(config: AnthropicInstrumentationConfig = {}) {
    super('@lilypad/instrumentation-anthropic', '0.1.0', config);
  }

  protected init() {
    logger.info('[AnthropicInstrumentation] Initializing Anthropic instrumentation');
    const module = new InstrumentationNodeModuleDefinition(
      MODULE_NAME,
      SUPPORTED_VERSIONS,
      (moduleExports, moduleVersion) => {
        logger.info(`[AnthropicInstrumentation] Applying patch for @anthropic-ai/sdk@${moduleVersion}`);
        return this._applyPatch(moduleExports);
      },
      (moduleExports, moduleVersion) => {
        logger.info(`[AnthropicInstrumentation] Removing patch for @anthropic-ai/sdk@${moduleVersion}`);
        return this._removePatch(moduleExports);
      },
    );

    return [module];
  }

  private _applyPatch(moduleExports: any): any {
    // Check if already instrumented by Lilypad
    if (moduleExports && moduleExports[LILYPAD_INSTRUMENTED]) {
      logger.warn('[AnthropicInstrumentation] Module already instrumented by Lilypad, skipping');
      return moduleExports;
    }

    // Check for other instrumentation libraries
    const otherInstrumentations = this._detectOtherInstrumentations(moduleExports);
    if (otherInstrumentations.length > 0) {
      logger.warn(
        '[AnthropicInstrumentation] Detected other instrumentations:',
        otherInstrumentations.join(', '),
      );
      if (!(this._config as AnthropicInstrumentationConfig).suppressInternalInstrumentation) {
        logger.warn('[AnthropicInstrumentation] Proceeding with caution - may cause conflicts');
      }
    }

    logger.info('[AnthropicInstrumentation] Patching Anthropic module');
    logger.info('[AnthropicInstrumentation] Module exports:', Object.keys(moduleExports || {}));

    // Handle different export patterns
    let AnthropicClass: any;
    if (moduleExports.default) {
      AnthropicClass = moduleExports.default;
      logger.info('[AnthropicInstrumentation] Found default export');
    } else if (moduleExports.Anthropic) {
      AnthropicClass = moduleExports.Anthropic;
      logger.info('[AnthropicInstrumentation] Found named export');
    } else {
      AnthropicClass = moduleExports;
      logger.info('[AnthropicInstrumentation] Using module directly');
    }

    if (!AnthropicClass || !AnthropicClass.prototype) {
      logger.error('[AnthropicInstrumentation] Anthropic class not found or has no prototype');
      if ((this._config as AnthropicInstrumentationConfig).fallbackToProxy) {
        return this._applyProxyFallback(moduleExports);
      }
      return moduleExports;
    }

    // Apply shimmer to wrap the method
    this._wrapMessagesCreate(AnthropicClass.prototype);
    logger.info('[AnthropicInstrumentation] Successfully applied patch');

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
    logger.debug('[AnthropicInstrumentation] Removing Anthropic patches');

    let AnthropicClass: any;
    if (moduleExports.default) {
      AnthropicClass = moduleExports.default;
    } else if (moduleExports.Anthropic) {
      AnthropicClass = moduleExports.Anthropic;
    } else {
      AnthropicClass = moduleExports;
    }

    if (AnthropicClass?.prototype?.messages?.create) {
      shimmer.unwrap(AnthropicClass.prototype.messages, 'create');
    }

    return moduleExports;
  }

  private _wrapMessagesCreate(prototype: any): void {
    const instrumentation = this;

    // Check if prototype chain has messages.create
    if (!prototype.messages) {
      // Try to use Proxy if lazy getter pattern is detected
      if ((this._config as AnthropicInstrumentationConfig).fallbackToProxy) {
        logger.info('[AnthropicInstrumentation] messages not found, applying Proxy fallback');
        this._applyProxyToMessagesGetter(prototype);
        return;
      }
      logger.error('[AnthropicInstrumentation] messages not found on prototype');
      return;
    }

    if (!prototype.messages.create) {
      logger.error('[AnthropicInstrumentation] messages.create not found');
      return;
    }

    if (isWrapped(prototype.messages.create)) {
      logger.debug('[AnthropicInstrumentation] messages.create already wrapped');
      return;
    }

    shimmer.wrap(prototype.messages, 'create', (original: Function) => {
      return async function (this: any, ...args: any[]) {
        // Skip if shutting down
        if (isSDKShuttingDown()) {
          return original.apply(this, args);
        }

        const [params] = args;
        const tracer = instrumentation.tracer;
        const config = instrumentation._config as AnthropicInstrumentationConfig;

        // Get the active context to preserve parent-child relationships
        const activeContext = context.active();
        const parentSpan = trace.getSpan(activeContext);

        if (parentSpan) {
          logger.debug('[AnthropicInstrumentation] Found parent span:', {
            parentSpanId: parentSpan.spanContext().spanId,
            parentTraceId: parentSpan.spanContext().traceId,
            parentSpanName: (parentSpan as any).name || 'unknown',
          });
        } else {
          logger.debug('[AnthropicInstrumentation] No parent span found in context');
        }

        // Start span using the OTel way with active context
        const span = tracer.startSpan(
          `anthropic.messages ${params?.model || 'unknown'}`,
          {
            kind: SpanKind.CLIENT,
            attributes: {
              [SEMATTRS_GEN_AI_SYSTEM]: 'anthropic',
              [SEMATTRS_GEN_AI_REQUEST_MODEL]: params?.model,
              [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: params?.temperature,
              [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: params?.max_tokens,
              [SEMATTRS_GEN_AI_REQUEST_TOP_P]: params?.top_p,
              'gen_ai.request.top_k': params?.top_k,
              [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
              'lilypad.type': 'llm',
              'server.address': 'api.anthropic.com',
            },
          },
          activeContext,
        );

        logger.debug('[AnthropicInstrumentation] Created Anthropic span:', {
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

            // Record system message if present
            if (params?.system) {
              span.addEvent('gen_ai.system.message', {
                'gen_ai.system': 'anthropic',
                content: params.system,
              });
            }

            // Record messages
            if (params?.messages) {
              params.messages.forEach((message: any) => {
                const content = typeof message.content === 'string' 
                  ? message.content 
                  : JSON.stringify(message.content);
                
                span.addEvent(`gen_ai.${message.role}.message`, {
                  'gen_ai.system': 'anthropic',
                  content: content,
                });
              });
            }

            // Call original method
            const result = await original.apply(this, args);

            // Handle streaming
            if (params?.stream && isAsyncIterable(result)) {
              return instrumentation._wrapStream(
                span,
                result as AsyncIterable<AnthropicMessageChunk>,
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
            if (!params?.stream) {
              span.end();
            }
          }
        });
      } as typeof original;
    });

    logger.debug('[AnthropicInstrumentation] Successfully wrapped messages.create');
  }

  private _applyProxyToMessagesGetter(prototype: any): void {
    const instrumentation = this;

    // Store the original property descriptor
    const originalDescriptor = Object.getOwnPropertyDescriptor(prototype, 'messages');

    // Define a getter that applies wrapping when messages is accessed
    Object.defineProperty(prototype, 'messages', {
      get: function () {
        // Get the original messages object
        const messages =
          originalDescriptor && originalDescriptor.get
            ? originalDescriptor.get.call(this)
            : this._messages;

        if (
          messages &&
          messages.create &&
          !isWrapped(messages.create)
        ) {
          logger.info('[AnthropicInstrumentation] Applying lazy wrapping to messages.create');
          
          // Store the original create method
          const originalCreate = messages.create;
          
          // Create wrapped function that preserves all properties
          const wrappedCreate = instrumentation._createWrappedMethod(originalCreate.bind(messages));
          
          // Copy all properties from original to wrapped function
          Object.setPrototypeOf(wrappedCreate, Object.getPrototypeOf(originalCreate));
          for (const prop of Object.getOwnPropertyNames(originalCreate)) {
            if (prop !== 'length' && prop !== 'name' && prop !== 'prototype') {
              try {
                wrappedCreate[prop] = originalCreate[prop];
              } catch {
                // Ignore read-only properties
              }
            }
          }
          
          // Replace the method
          messages.create = wrappedCreate;
        }

        return messages;
      },
      set: function (value) {
        if (originalDescriptor && originalDescriptor.set) {
          originalDescriptor.set.call(this, value);
        } else {
          this._messages = value;
        }
      },
      configurable: true,
      enumerable: true,
    });
  }

  private _createWrappedMethod(original: Function): Function {
    const instrumentation = this;
    const wrapped = function (this: any, ...args: any[]) {
      // Skip if shutting down
      if (isSDKShuttingDown()) {
        return original.apply(this, args);
      }

      const [params] = args;
      const tracer = instrumentation.tracer;
      const config = instrumentation._config as AnthropicInstrumentationConfig;

      // Get the active context to preserve parent-child relationships
      const activeContext = context.active();

      // Use the same span creation logic as the main wrapped method
      const span = tracer.startSpan(
        `messages ${params?.model || 'unknown'}`,
        {
          kind: SpanKind.CLIENT,
          attributes: {
            [SEMATTRS_GEN_AI_SYSTEM]: 'anthropic',
            'server.address': 'api.anthropic.com',
            [SEMATTRS_GEN_AI_REQUEST_MODEL]: params?.model,
            [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: params?.temperature,
            [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: params?.max_tokens,
            [SEMATTRS_GEN_AI_REQUEST_TOP_P]: params?.top_p,
            'gen_ai.request.top_k': params?.top_k,
            [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
          },
        },
        activeContext,
      );

      // Call original to get the special promise-like object
      const originalResult = original.apply(this, args);
      
      // If it's not an object with special methods, handle it normally
      if (!originalResult || typeof originalResult !== 'object') {
        // Simple case - just a regular promise
        return context.with(trace.setSpan(context.active(), span), async () => {
          try {
            const result = await originalResult;
            instrumentation._handleResult(span, params, result, config);
            return result;
          } catch (error) {
            instrumentation._handleError(span, error);
            throw error;
          } finally {
            if (!params?.stream) {
              span.end();
            }
          }
        });
      }
      
      // For the Anthropic SDK, we need to preserve special methods like withResponse
      // Create a proxy that intercepts promise resolution
      const wrappedResult = Object.create(Object.getPrototypeOf(originalResult));
      
      // Copy all properties and methods from the original
      for (const key in originalResult) {
        if (key === 'then' || key === 'catch' || key === 'finally') {
          continue; // We'll handle these specially
        }
        try {
          const descriptor = Object.getOwnPropertyDescriptor(originalResult, key);
          if (descriptor) {
            Object.defineProperty(wrappedResult, key, descriptor);
          }
        } catch {
          // Some properties might not be accessible
        }
      }
      
      // Wrap the then method to add our instrumentation
      wrappedResult.then = (onfulfilled?: any, onrejected?: any) => {
        return originalResult.then(
          (result: any) => {
            return context.with(trace.setSpan(context.active(), span), async () => {
              try {
                instrumentation._handleResult(span, params, result, config);
                return onfulfilled ? onfulfilled(result) : result;
              } catch (error) {
                instrumentation._handleError(span, error);
                throw error;
              } finally {
                if (!params?.stream) {
                  span.end();
                }
              }
            });
          },
          (error: any) => {
            instrumentation._handleError(span, error);
            span.end();
            return onrejected ? onrejected(error) : Promise.reject(error);
          }
        );
      };
      
      // Wrap catch and finally methods
      wrappedResult.catch = (onrejected: any) => wrappedResult.then(undefined, onrejected);
      wrappedResult.finally = (onfinally: any) => wrappedResult.then(
        (value: any) => { onfinally?.(); return value; },
        (reason: any) => { onfinally?.(); throw reason; }
      );
      
      return wrappedResult;
    };
    
    // Copy all properties from original to wrapped function
    Object.setPrototypeOf(wrapped, Object.getPrototypeOf(original));
    for (const prop in original) {
      if (original.hasOwnProperty(prop)) {
        try {
          wrapped[prop] = original[prop];
        } catch {
          // Ignore errors when copying properties
        }
      }
    }
    
    return wrapped;
  }

  private _handleResult(span: OtelSpan, params: any, result: any, config: AnthropicInstrumentationConfig): void {
    // Call request hook
    if (config.requestHook) {
      config.requestHook(span, params);
    }

    // Record system message if present
    if (params?.system) {
      span.addEvent('gen_ai.system.message', {
        'gen_ai.system': 'anthropic',
        content: params.system,
      });
    }

    // Record messages
    if (params?.messages) {
      params.messages.forEach((message: any) => {
        const content = typeof message.content === 'string' 
          ? message.content 
          : JSON.stringify(message.content);
        
        span.addEvent(`gen_ai.${message.role}.message`, {
          'gen_ai.system': 'anthropic',
          content: content,
        });
      });
    }

    // Handle streaming
    if (params?.stream && isAsyncIterable(result)) {
      return this._wrapStream(
        span,
        result as AsyncIterable<AnthropicMessageChunk>,
        config,
      );
    }

    // Handle regular response
    this._recordResponse(span, result);

    // Call response hook
    if (config.responseHook) {
      config.responseHook(span, result);
    }

    span.setStatus({ code: SpanStatusCode.OK });
  }

  private _handleError(span: OtelSpan, error: any): void {
    span.recordException(error as Error);
    span.setStatus({
      code: SpanStatusCode.ERROR,
      message: error instanceof Error ? error.message : String(error),
    });
  }

  private _wrapStream(
    span: OtelSpan,
    stream: AsyncIterable<AnthropicMessageChunk>,
    _config: AnthropicInstrumentationConfig,
  ): AsyncIterable<AnthropicMessageChunk> {
    let content = '';
    let stopReason: string | null = null;
    let usage: { input_tokens: number; output_tokens: number } = {
      input_tokens: 0,
      output_tokens: 0,
    };

    const onChunk = (chunk: AnthropicMessageChunk) => {
      // Process chunk based on type
      if (chunk.type === 'message_start' && chunk.message) {
        // Initial message with usage info
        if (chunk.message.usage) {
          usage.input_tokens = chunk.message.usage.input_tokens;
          usage.output_tokens = chunk.message.usage.output_tokens;
        }
      } else if (chunk.type === 'content_block_delta' && chunk.delta) {
        // Text content
        if (chunk.delta.type === 'text_delta' && chunk.delta.text) {
          content += chunk.delta.text;
        }
      } else if (chunk.type === 'message_delta' && chunk.delta) {
        // Message delta with stop reason
        if (chunk.delta.stop_reason) {
          stopReason = chunk.delta.stop_reason;
        }
      } else if (chunk.type === 'message_stop' && chunk.usage) {
        // Final usage info
        usage.output_tokens = chunk.usage.output_tokens;
      }

      // Add chunk event
      span.addEvent('gen_ai.chunk', {
        size: chunk.delta?.text?.length || 0,
      });
    };

    const onFinalize = () => {
      // Record the completed stream
      if (content || stopReason) {
        const message: Record<string, unknown> = {
          role: 'assistant',
          content: content,
        };

        span.addEvent('gen_ai.choice', {
          'gen_ai.system': 'anthropic',
          index: 0,
          finish_reason: stopReason || 'error',
          message: JSON.stringify(message),
        });
      }

      if (stopReason) {
        span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, [stopReason]);
      }

      // Record usage if available
      if (usage) {
        span.setAttributes({
          [SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS]: usage.input_tokens,
          [SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS]: usage.output_tokens,
          'gen_ai.usage.total_tokens': usage.input_tokens + usage.output_tokens,
        });
      }

      span.setStatus({ code: SpanStatusCode.OK });
      span.end();
    };

    return new StreamWrapper(stream, span, { onChunk, onFinalize });
  }

  private _recordResponse(span: OtelSpan, response: any): void {
    if (!response) return;

    // Type guard for AnthropicMessageResponse
    if (!response.type || response.type !== 'message') return;

    // Record response attributes
    if (response.content && response.content.length > 0) {
      response.content.forEach((content: any, index: number) => {
        if (content.type === 'text') {
          const message: Record<string, unknown> = {
            role: response.role,
            content: content.text,
          };

          span.addEvent('gen_ai.choice', {
            'gen_ai.system': 'anthropic',
            index: index,
            finish_reason: response.stop_reason || 'error',
            message: JSON.stringify(message),
          });
        }
      });

      // Record finish reasons
      if (response.stop_reason) {
        span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, [response.stop_reason]);
      }
    }

    // Record usage
    if (response.usage) {
      span.setAttributes({
        [SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS]: response.usage.input_tokens,
        [SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS]: response.usage.output_tokens,
        'gen_ai.usage.total_tokens': response.usage.input_tokens + response.usage.output_tokens,
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

  private _applyProxyFallback(moduleExports: any): any {
    logger.debug('[AnthropicInstrumentation] Applying Proxy fallback');

    const instrumentation = this;
    const handler = {
      construct(target: any, args: any[]) {
        const instance = new target(...args);
        return instrumentation._proxyInstance(instance);
      },
    };

    if (moduleExports.default) {
      moduleExports.default = new Proxy(moduleExports.default, handler);
    } else if (moduleExports.Anthropic) {
      moduleExports.Anthropic = new Proxy(moduleExports.Anthropic, handler);
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

        // Intercept messages.create
        if (prop === 'messages') {
          return new Proxy(value, {
            get(messagesTarget, messagesProp) {
              const messagesValue = Reflect.get(messagesTarget, messagesProp);

              if (messagesProp === 'create') {
                return instrumentation._wrapMethod(messagesValue.bind(messagesTarget));
              }

              return messagesValue;
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
      const config = instrumentation._config as AnthropicInstrumentationConfig;

      // Get the active context to preserve parent-child relationships
      const activeContext = context.active();

      // Create span
      const span = tracer.startSpan(
        `messages ${params?.model || 'unknown'}`,
        {
          kind: SpanKind.CLIENT,
          attributes: {
            [SEMATTRS_GEN_AI_SYSTEM]: 'anthropic',
            'server.address': 'api.anthropic.com',
            [SEMATTRS_GEN_AI_REQUEST_MODEL]: params?.model,
            [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: params?.temperature,
            [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: params?.max_tokens,
            [SEMATTRS_GEN_AI_REQUEST_TOP_P]: params?.top_p,
            'gen_ai.request.top_k': params?.top_k,
            [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
          },
        },
        activeContext,
      );

      return context.with(trace.setSpan(context.active(), span), async () => {
        try {
          // Call request hook
          if (config.requestHook) {
            config.requestHook(span, params);
          }

          // Record system message if present
          if (params?.system) {
            span.addEvent('gen_ai.system.message', {
              'gen_ai.system': 'anthropic',
              content: params.system,
            });
          }

          // Record messages
          if (params?.messages) {
            params.messages.forEach((message: any) => {
              const content = typeof message.content === 'string' 
                ? message.content 
                : JSON.stringify(message.content);
              
              span.addEvent(`gen_ai.${message.role}.message`, {
                'gen_ai.system': 'anthropic',
                content: content,
              });
            });
          }

          // Call original
          const result = await original.apply(this, args);

          // Handle streaming
          if (params?.stream && isAsyncIterable(result)) {
            return instrumentation._wrapStream(
              span,
              result as AsyncIterable<AnthropicMessageChunk>,
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

    // Check Anthropic specific paths
    const anthropicPaths = [
      ['default', 'prototype', 'messages', 'create'],
      ['Anthropic', 'prototype', 'messages', 'create'],
      ['prototype', 'messages', 'create'],
    ];

    for (const path of anthropicPaths) {
      if (checkWrapped(moduleExports, path)) {
        detectedInstrumentations.push('Unknown (wrapped method detected)');
        break;
      }
    }

    // Remove duplicates
    return [...new Set(detectedInstrumentations)];
  }
}