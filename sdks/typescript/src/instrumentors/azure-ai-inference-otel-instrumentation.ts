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
  AzureInferenceChatCompletionParams,
  AzureInferenceChatCompletionChunk,
} from '../types/azure-ai-inference';

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

const MODULE_NAME = '@azure-rest/ai-inference';
const SUPPORTED_VERSIONS = ['*'];

export interface AzureInferenceInstrumentationConfig extends InstrumentationConfig {
  /**
   * Hook called before request is sent
   */
  requestHook?: (span: OtelSpan, params: AzureInferenceChatCompletionParams) => void;

  /**
   * Hook called after response is received
   */
  responseHook?: (span: OtelSpan, response: any) => void;

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
const LILYPAD_INSTRUMENTED = Symbol.for('lilypad.azure-ai-inference.instrumented');

export class AzureInferenceInstrumentation extends InstrumentationBase {
  constructor(config: AzureInferenceInstrumentationConfig = {}) {
    super('@lilypad/instrumentation-azure-ai-inference', '0.1.0', config);
  }

  enable() {
    const result = super.enable();

    // Monkey-patch require to intercept module loading
    const self = this;
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const Module = require('module');
    const originalRequire = Module.prototype.require;

    Module.prototype.require = function (id: string, ...args: any[]) {
      const exports = originalRequire.apply(this, [id, ...args]);

      if (id === MODULE_NAME && exports && !exports[LILYPAD_INSTRUMENTED]) {
        return self._applyPatch(exports);
      }

      return exports;
    };

    return result;
  }

  protected init() {
    // Check if module is already loaded and patch it immediately
    // This is needed for cases where the module is imported before our instrumentation
    try {
      const resolvedPath = require.resolve(MODULE_NAME);
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      const moduleExports = require.cache[resolvedPath]?.exports;

      if (moduleExports) {
        const patchedExports = this._applyPatch(moduleExports);
        // Update the cache with patched exports
        const cacheEntry = require.cache[resolvedPath];
        if (cacheEntry) {
          cacheEntry.exports = patchedExports;
        }
      }
    } catch (e) {
      // Module not yet loaded, will patch on load
    }

    const module = new InstrumentationNodeModuleDefinition(
      MODULE_NAME,
      SUPPORTED_VERSIONS,
      (moduleExports, moduleVersion) => {
        logger.debug(
          `[AzureInferenceInstrumentation] Patching @azure-rest/ai-inference@${moduleVersion}`,
        );
        return this._applyPatch(moduleExports);
      },
      (moduleExports, moduleVersion) => {
        logger.debug(
          `[AzureInferenceInstrumentation] Removing patch for @azure-rest/ai-inference@${moduleVersion}`,
        );
        return this._removePatch(moduleExports);
      },
    );

    return [module];
  }

  private _applyPatch(moduleExports: any): any {
    // Check if already instrumented by Lilypad
    if (moduleExports && moduleExports[LILYPAD_INSTRUMENTED]) {
      logger.warn(
        '[AzureInferenceInstrumentation] Module already instrumented by Lilypad, skipping',
      );
      return moduleExports;
    }

    // Check for other instrumentation libraries
    const otherInstrumentations = this._detectOtherInstrumentations(moduleExports);
    if (otherInstrumentations.length > 0) {
      logger.warn(
        '[AzureInferenceInstrumentation] Detected other instrumentations:',
        otherInstrumentations.join(', '),
      );
      if (!(this._config as AzureInferenceInstrumentationConfig).suppressInternalInstrumentation) {
        logger.warn(
          '[AzureInferenceInstrumentation] Proceeding with caution - may cause conflicts',
        );
      }
    }

    // Handle different export patterns
    let factoryFunction: any;

    // Check for default export (ESM style)
    if (moduleExports.default && typeof moduleExports.default === 'function') {
      factoryFunction = moduleExports.default;
    } else if (typeof moduleExports === 'function') {
      // Direct function export
      factoryFunction = moduleExports;
    }

    if (factoryFunction) {
      // Wrap the factory function to instrument clients
      const wrappedFactory = (endpoint: string, options?: any) => {
        const client = factoryFunction(endpoint, options);
        return this._instrumentClient(client);
      };

      // Copy over any static properties
      Object.keys(factoryFunction).forEach((key) => {
        (wrappedFactory as any)[key] = factoryFunction[key];
      });

      // Replace the appropriate export
      if (moduleExports.default) {
        moduleExports.default = wrappedFactory;
      } else {
        // For direct function export, we need to return the wrapped function
        // with all properties copied
        Object.keys(moduleExports).forEach((key) => {
          if (key !== 'default') {
            (wrappedFactory as any)[key] = moduleExports[key];
          }
        });
        moduleExports = wrappedFactory;
      }
    } else {
      logger.error('[AzureInferenceInstrumentation] Factory function not found in module exports');
      return moduleExports;
    }

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
    logger.debug('[AzureInferenceInstrumentation] Removing Azure AI Inference patches');
    // Since we wrap the factory function, we can't easily unwrap it
    // This is a limitation of the current approach
    return moduleExports;
  }

  private _instrumentClient(client: any): any {
    // Check if client has path method (REST client pattern)
    if (client.path) {
      const originalPath = client.path.bind(client);
      client.path = (...args: any[]) => {
        const pathClient = originalPath(...args);

        // Wrap the post method for chat completions
        if (pathClient.post) {
          this._wrapChatCompletions(pathClient);
        }

        return pathClient;
      };
    }

    // Also check for direct ChatCompletionsClient
    if (client.complete) {
      this._wrapDirectChatCompletions(client);
    }

    return client;
  }

  private _wrapChatCompletions(pathClient: any): void {
    const instrumentation = this;

    if (isWrapped(pathClient.post)) {
      logger.debug('[AzureInferenceInstrumentation] post already wrapped');
      return;
    }

    shimmer.wrap(pathClient, 'post', (original: Function) => {
      return async function (this: any, options?: any) {
        // Skip if shutting down
        if (isSDKShuttingDown()) {
          return original.apply(this, [options]);
        }

        const body = options?.body;
        if (!body || !body.messages) {
          // Not a chat completion request
          return original.apply(this, [options]);
        }

        const tracer = instrumentation.tracer;
        const config = instrumentation._config as AzureInferenceInstrumentationConfig;

        // Extract model and endpoint info
        const model = body.model || 'Ministral-3B';
        const serverAddress = instrumentation._extractEndpoint(
          this._client?._baseUrl || this._baseUrl,
        );

        // Get the active context
        const activeContext = context.active();

        // Start span
        const span = tracer.startSpan(
          `azure.ai.inference.chat ${model}`,
          {
            kind: SpanKind.CLIENT,
            attributes: {
              [SEMATTRS_GEN_AI_SYSTEM]: 'azure',
              'server.address': serverAddress,
              [SEMATTRS_GEN_AI_REQUEST_MODEL]: model,
              [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: body.temperature,
              [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: body.max_tokens,
              [SEMATTRS_GEN_AI_REQUEST_TOP_P]: body.top_p,
              [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
              'lilypad.type': 'trace',
            },
          },
          activeContext,
        );

        // Set span in context
        const contextWithSpan = trace.setSpan(context.active(), span);

        return context.with(contextWithSpan, async () => {
          try {
            // Call request hook if provided
            if (config.requestHook) {
              config.requestHook(span, body);
            }

            // Record messages
            if (body.messages) {
              body.messages.forEach((message: any) => {
                span.addEvent(`gen_ai.${message.role}.message`, {
                  'gen_ai.system': 'azure',
                  content:
                    typeof message.content === 'string'
                      ? message.content
                      : JSON.stringify(message.content),
                });
              });
            }

            // Call original method
            const result = await original.apply(this, [options]);

            // Handle streaming
            if (body.stream && (result.asNodeStream || result.bodyAsText)) {
              return instrumentation._wrapStreamResponse(span, result, config, serverAddress);
            }

            // Handle regular response
            if (result.body) {
              instrumentation._recordResponse(span, result.body, serverAddress);

              // Call response hook if provided
              if (config.responseHook) {
                config.responseHook(span, result.body);
              }
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
            if (!body.stream) {
              span.end();
            }
          }
        });
      };
    });
  }

  private _wrapDirectChatCompletions(client: any): void {
    const instrumentation = this;

    if (isWrapped(client.complete)) {
      logger.debug('[AzureInferenceInstrumentation] complete already wrapped');
      return;
    }

    shimmer.wrap(client, 'complete', (original: Function) => {
      return async function (this: any, params: any, options?: any) {
        // Skip if shutting down
        if (isSDKShuttingDown()) {
          return original.apply(this, [params, options]);
        }

        const tracer = instrumentation.tracer;
        const config = instrumentation._config as AzureInferenceInstrumentationConfig;

        // Extract model from params or client
        let model = params.model;
        if (!model && this.getModelInfo) {
          const modelInfo = await this.getModelInfo();
          model = modelInfo?.model_name || 'unknown';
        }

        const serverAddress = instrumentation._extractEndpoint(this._endpoint || this.endpoint);

        // Get the active context
        const activeContext = context.active();

        // Start span
        const span = tracer.startSpan(
          `azure.ai.inference.chat ${model}`,
          {
            kind: SpanKind.CLIENT,
            attributes: {
              [SEMATTRS_GEN_AI_SYSTEM]: 'azure',
              'server.address': serverAddress,
              [SEMATTRS_GEN_AI_REQUEST_MODEL]: model,
              [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: params.temperature,
              [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: params.max_tokens,
              [SEMATTRS_GEN_AI_REQUEST_TOP_P]: params.top_p,
              [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
              'lilypad.type': 'trace',
            },
          },
          activeContext,
        );

        // Set span in context
        const contextWithSpan = trace.setSpan(context.active(), span);

        return context.with(contextWithSpan, async () => {
          try {
            // Call request hook if provided
            if (config.requestHook) {
              config.requestHook(span, params);
            }

            // Record messages
            if (params.messages) {
              params.messages.forEach((message: any) => {
                span.addEvent(`gen_ai.${message.role}.message`, {
                  'gen_ai.system': 'azure',
                  content:
                    typeof message.content === 'string'
                      ? message.content
                      : JSON.stringify(message.content),
                });
              });
            }

            // Call original method
            const result = await original.apply(this, [params, options]);

            // Handle streaming
            if (params.stream && isAsyncIterable(result)) {
              return instrumentation._wrapStream(
                span,
                result as AsyncIterable<AzureInferenceChatCompletionChunk>,
                config,
                serverAddress,
              );
            }

            // Handle regular response
            instrumentation._recordResponse(span, result, serverAddress);

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
            if (!params.stream) {
              span.end();
            }
          }
        });
      };
    });
  }

  private _wrapStreamResponse(
    span: OtelSpan,
    response: any,
    config: AzureInferenceInstrumentationConfig,
    serverAddress: string,
  ): any {
    // For REST responses, we need to handle the stream differently
    const originalAsNodeStream = response.asNodeStream;
    const originalBodyAsText = response.bodyAsText;

    // Override stream methods to instrument them
    if (originalAsNodeStream) {
      response.asNodeStream = () => {
        const stream = originalAsNodeStream.call(response);
        return this._wrapNodeStream(span, stream, config, serverAddress);
      };
    }

    // Also handle if they read as text and parse manually
    if (originalBodyAsText) {
      response.bodyAsText = async () => {
        const text = await originalBodyAsText.call(response);
        // Parse and record the response
        try {
          const parsed = JSON.parse(text);
          this._recordResponse(span, parsed, serverAddress);
        } catch (e) {
          // Not JSON, ignore
        }
        span.setStatus({ code: SpanStatusCode.OK });
        span.end();
        return text;
      };
    }

    return response;
  }

  private _wrapNodeStream(
    span: OtelSpan,
    stream: any,
    _config: AzureInferenceInstrumentationConfig,
    serverAddress: string,
  ): any {
    let content = '';
    let finishReason: string | null = null;
    let usage: any = null;

    const onChunk = (chunk: AzureInferenceChatCompletionChunk) => {
      if (chunk.choices && chunk.choices.length > 0) {
        const choice = chunk.choices[0];
        if (choice.delta?.content) {
          content += choice.delta.content;
        }
        if (choice.finish_reason) {
          finishReason = choice.finish_reason;
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
        span.addEvent('gen_ai.choice', {
          'gen_ai.system': 'azure',
          index: 0,
          message: JSON.stringify({ role: 'assistant', content: content }),
          finish_reason: finishReason || 'stop',
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

      // Add server address
      span.setAttribute('server.address', serverAddress);

      span.setStatus({ code: SpanStatusCode.OK });
      span.end();
    };

    // Need to parse SSE stream
    // This is a simplified version - real implementation would need proper SSE parsing
    return new StreamWrapper(stream, span, { onChunk, onFinalize });
  }

  private _wrapStream(
    span: OtelSpan,
    stream: AsyncIterable<AzureInferenceChatCompletionChunk>,
    _config: AzureInferenceInstrumentationConfig,
    serverAddress: string,
  ): AsyncIterable<AzureInferenceChatCompletionChunk> {
    let content = '';
    let finishReason: string | null = null;
    let usage: any = null;

    const onChunk = (chunk: AzureInferenceChatCompletionChunk) => {
      if (chunk.choices && chunk.choices.length > 0) {
        const choice = chunk.choices[0];
        if (choice.delta?.content) {
          content += choice.delta.content;
        }
        if (choice.finish_reason) {
          finishReason = choice.finish_reason;
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
        span.addEvent('gen_ai.choice', {
          'gen_ai.system': 'azure',
          index: 0,
          message: JSON.stringify({ role: 'assistant', content: content }),
          finish_reason: finishReason || 'stop',
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

      // Add server address
      span.setAttribute('server.address', serverAddress);

      span.setStatus({ code: SpanStatusCode.OK });
      span.end();
    };

    return new StreamWrapper(stream, span, { onChunk, onFinalize });
  }

  private _recordResponse(span: OtelSpan, response: any, serverAddress: string): void {
    if (!response) return;

    // Record response attributes
    if (response.choices && response.choices.length > 0) {
      response.choices.forEach((choice: any, index: number) => {
        if (choice.message) {
          // Match Python's event format
          span.addEvent('gen_ai.choice', {
            'gen_ai.system': 'azure',
            index: index,
            message: JSON.stringify(choice.message),
            finish_reason: choice.finish_reason || '',
          });
        }
      });

      // Record finish reasons
      const finishReasons = response.choices
        .map((c: any) => c.finish_reason)
        .filter((reason: any): reason is string => Boolean(reason));
      if (finishReasons.length > 0) {
        span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, finishReasons);
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

    // Record model
    if (response.model) {
      span.setAttribute('gen_ai.response.model', response.model);
    }

    // Record ID
    if (response.id) {
      span.setAttribute('gen_ai.response.id', response.id);
    }

    // Add server address
    span.setAttribute('server.address', serverAddress);
  }

  private _extractEndpoint(endpoint: string): string {
    // Extract hostname from endpoint URL
    if (endpoint) {
      const match = endpoint.match(/https?:\/\/([^/]+)/);
      if (match) return match[1];
    }
    // Default to generic Azure domain
    return '*.models.ai.azure.com';
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

    // Remove duplicates
    return [...new Set(detectedInstrumentations)];
  }
}
