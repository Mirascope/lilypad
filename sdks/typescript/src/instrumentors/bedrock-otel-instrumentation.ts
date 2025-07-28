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
import type {
  BedrockInvokeModelParams,
  BedrockAnthropicResponse,
  BedrockTitanResponse,
  BedrockLlamaResponse,
  BedrockResponseStreamChunk,
} from '../types/bedrock';

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

const MODULE_NAME = '@aws-sdk/client-bedrock-runtime';
const SUPPORTED_VERSIONS = ['>=3.0.0'];

export interface BedrockInstrumentationConfig extends InstrumentationConfig {
  /**
   * Hook called before request is sent
   */
  requestHook?: (span: OtelSpan, params: BedrockInvokeModelParams) => void;

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
const LILYPAD_INSTRUMENTED = Symbol.for('lilypad.bedrock.instrumented');

export class BedrockInstrumentation extends InstrumentationBase {
  constructor(config: BedrockInstrumentationConfig = {}) {
    super('@lilypad/instrumentation-bedrock', '0.1.0', config);
  }

  protected init() {
    logger.info('[BedrockInstrumentation] Initializing Bedrock instrumentation');
    const module = new InstrumentationNodeModuleDefinition(
      MODULE_NAME,
      SUPPORTED_VERSIONS,
      (moduleExports, moduleVersion) => {
        logger.info(
          `[BedrockInstrumentation] Applying patch for @aws-sdk/client-bedrock-runtime@${moduleVersion}`,
        );
        return this._applyPatch(moduleExports);
      },
      (moduleExports, moduleVersion) => {
        logger.info(
          `[BedrockInstrumentation] Removing patch for @aws-sdk/client-bedrock-runtime@${moduleVersion}`,
        );
        return this._removePatch(moduleExports);
      },
    );

    return [module];
  }

  private _applyPatch(moduleExports: any): any {
    // Check if already instrumented by Lilypad
    if (moduleExports && moduleExports[LILYPAD_INSTRUMENTED]) {
      logger.warn('[BedrockInstrumentation] Module already instrumented by Lilypad, skipping');
      return moduleExports;
    }

    // Check for other instrumentation libraries
    const otherInstrumentations = this._detectOtherInstrumentations(moduleExports);
    if (otherInstrumentations.length > 0) {
      logger.warn(
        '[BedrockInstrumentation] Detected other instrumentations:',
        otherInstrumentations.join(', '),
      );
      if (!(this._config as BedrockInstrumentationConfig).suppressInternalInstrumentation) {
        logger.warn('[BedrockInstrumentation] Proceeding with caution - may cause conflicts');
      }
    }

    logger.debug('[BedrockInstrumentation] Module exports type:', typeof moduleExports);
    logger.debug('[BedrockInstrumentation] Module exports keys:', Object.keys(moduleExports || {}));

    // Check for BedrockRuntimeClient
    const BedrockRuntimeClient = moduleExports?.BedrockRuntimeClient;
    if (!BedrockRuntimeClient) {
      logger.error('[BedrockInstrumentation] BedrockRuntimeClient not found in module exports');
      return moduleExports;
    }

    logger.debug('[BedrockInstrumentation] Found BedrockRuntimeClient');

    // Patch the BedrockRuntimeClient prototype
    if (BedrockRuntimeClient.prototype) {
      this._patchBedrockClient(BedrockRuntimeClient.prototype);
    } else {
      logger.error('[BedrockInstrumentation] BedrockRuntimeClient.prototype not found');
    }

    // Mark module as instrumented
    if (moduleExports) {
      moduleExports[LILYPAD_INSTRUMENTED] = true;
    }

    return moduleExports;
  }

  private _removePatch(moduleExports: any): any {
    // Remove instrumentation marker
    if (moduleExports && moduleExports[LILYPAD_INSTRUMENTED]) {
      delete moduleExports[LILYPAD_INSTRUMENTED];
    }

    const BedrockRuntimeClient = moduleExports?.BedrockRuntimeClient;
    if (BedrockRuntimeClient?.prototype) {
      // Unwrap send method
      if (isWrapped(BedrockRuntimeClient.prototype.send)) {
        shimmer.unwrap(BedrockRuntimeClient.prototype, 'send');
        logger.debug('[BedrockInstrumentation] Unwrapped BedrockRuntimeClient.prototype.send');
      }
    }

    return moduleExports;
  }

  private _patchBedrockClient(prototype: any): void {
    const instrumentation = this;

    // Check if send method is already wrapped
    if (isWrapped(prototype.send)) {
      logger.debug('[BedrockInstrumentation] send already wrapped');
      return;
    }

    shimmer.wrap(prototype, 'send', (original: Function) => {
      logger.debug('[BedrockInstrumentation] Wrapped send method');
      return async function (this: any, command: any, ...args: any[]) {
        logger.debug('[BedrockInstrumentation] send method called with command:', {
          commandType: command?.constructor?.name,
          commandName: command?.constructor?.name,
          hasInput: !!command?.input,
          inputKeys: command?.input ? Object.keys(command.input) : [],
          modelId: command?.input?.modelId,
          hasRequestHandler: !!this.config?.requestHandler,
        });

        // Warn about custom request handler limitations
        if (this.config?.requestHandler) {
          logger.debug(
            '[BedrockInstrumentation] Custom requestHandler detected - response data may be limited',
          );
        }

        // Skip if shutting down
        if (isSDKShuttingDown()) {
          return original.apply(this, [command, ...args]);
        }

        // Check if this is an InvokeModelCommand or InvokeModelWithResponseStreamCommand
        const isModelCommand =
          command?.constructor?.name === 'InvokeModelCommand' ||
          command?.constructor?.name === 'InvokeModelWithResponseStreamCommand';

        if (!isModelCommand || !command?.input?.modelId) {
          logger.debug('[BedrockInstrumentation] Not a model invocation command, passing through');
          // Not a model invocation, pass through
          return original.apply(this, [command, ...args]);
        }

        const params = command.input as BedrockInvokeModelParams;
        const tracer = instrumentation.tracer;
        const config = instrumentation._config as BedrockInstrumentationConfig;

        // Get model provider from modelId
        const provider = instrumentation._detectProvider(params.modelId);

        // Get the active context to preserve parent-child relationships
        const activeContext = context.active();
        const parentSpan = trace.getSpan(activeContext);

        if (parentSpan) {
          logger.debug('[BedrockInstrumentation] Found parent span:', {
            parentSpanId: parentSpan.spanContext().spanId,
            parentTraceId: parentSpan.spanContext().traceId,
            parentSpanName: (parentSpan as any).name || 'unknown',
          });
        } else {
          logger.debug('[BedrockInstrumentation] No parent span found in context');
        }

        // Parse request body to extract parameters
        const bodyStr =
          typeof params.body === 'string' ? params.body : new TextDecoder().decode(params.body);
        const requestBody = bodyStr ? JSON.parse(bodyStr) : {};

        const { temperature, max_tokens, top_p } = instrumentation._extractParameters(
          requestBody,
          provider,
        );

        // Start span using the OTel way with active context
        const span = tracer.startSpan(
          `bedrock.invoke ${params.modelId}`,
          {
            kind: SpanKind.CLIENT,
            attributes: {
              'lilypad.type': 'trace',
              [SEMATTRS_GEN_AI_SYSTEM]: 'bedrock',
              [SEMATTRS_GEN_AI_REQUEST_MODEL]: params.modelId,
              [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: temperature,
              [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: max_tokens,
              [SEMATTRS_GEN_AI_REQUEST_TOP_P]: top_p,
              [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
              'bedrock.provider': provider,
              'bedrock.region': this.config?.region,
            },
          },
          activeContext,
        );

        logger.info('[BedrockInstrumentation] Created Bedrock span:', {
          spanId: span.spanContext().spanId,
          traceId: span.spanContext().traceId,
          parentSpanId: parentSpan?.spanContext().spanId || 'none',
          spanName: `bedrock.invoke ${params.modelId}`,
          attributes: {
            'gen_ai.system': 'bedrock',
            'gen_ai.request.model': params.modelId,
          },
        });

        // Set span in context for proper context propagation
        const contextWithSpan = trace.setSpan(context.active(), span);

        return context.with(contextWithSpan, async () => {
          let isStreaming = false;
          let result: any;

          try {
            // Call request hook if provided
            if (config.requestHook) {
              config.requestHook(span, params);
            }

            // Record messages based on provider
            instrumentation._recordRequestMessages(span, requestBody, provider);

            // Call original method
            result = await original.apply(this, [command, ...args]);

            // Check if this is a streaming response
            isStreaming = result?.body && Symbol.asyncIterator in result.body;

            // Handle streaming response
            if (isStreaming) {
              return {
                ...result,
                body: instrumentation._wrapStream(span, result.body, provider, config),
              };
            }

            // Handle regular response
            if (result?.body) {
              try {
                const responseBody = JSON.parse(new TextDecoder().decode(result.body));
                instrumentation._recordResponse(span, responseBody, provider);
              } catch (error) {
                logger.debug('[BedrockInstrumentation] Failed to parse response body:', error);
                // If we can't parse the response, at least mark it as successful
                span.setAttribute('bedrock.response.has_body', true);
              }
            }

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
            // End span for non-streaming responses
            if (!isStreaming) {
              logger.info('[BedrockInstrumentation] Ending span (non-streaming):', {
                spanId: span.spanContext().spanId,
                traceId: span.spanContext().traceId,
                spanName: `bedrock.invoke ${params.modelId}`,
              });
              span.end();
            } else {
              logger.info('[BedrockInstrumentation] Not ending span yet (streaming response)');
            }
          }
        });
      } as typeof original;
    });

    logger.debug('[BedrockInstrumentation] Successfully wrapped BedrockRuntimeClient.send');
  }

  private _detectProvider(modelId: string): string {
    if (modelId.includes('anthropic') || modelId.includes('claude')) {
      return 'anthropic';
    } else if (modelId.includes('titan')) {
      return 'amazon';
    } else if (modelId.includes('llama')) {
      return 'meta';
    } else if (modelId.includes('cohere')) {
      return 'cohere';
    } else if (modelId.includes('ai21')) {
      return 'ai21';
    } else if (modelId.includes('mistral')) {
      return 'mistral';
    }
    return 'unknown';
  }

  private _extractParameters(
    body: any,
    provider: string,
  ): {
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
  } {
    switch (provider) {
      case 'anthropic':
        return {
          temperature: body.temperature,
          max_tokens: body.max_tokens,
          top_p: body.top_p,
        };
      case 'amazon':
        return {
          temperature: body.textGenerationConfig?.temperature,
          max_tokens: body.textGenerationConfig?.maxTokenCount,
          top_p: body.textGenerationConfig?.topP,
        };
      case 'meta':
        return {
          temperature: body.temperature,
          max_tokens: body.max_gen_len,
          top_p: body.top_p,
        };
      default:
        return {
          temperature: body.temperature,
          max_tokens: body.max_tokens || body.maxTokens,
          top_p: body.top_p || body.topP,
        };
    }
  }

  private _recordRequestMessages(span: OtelSpan, body: any, provider: string): void {
    switch (provider) {
      case 'anthropic':
        if (body.messages) {
          body.messages.forEach((message: any) => {
            const eventName = `gen_ai.${message.role}.message`;
            const eventAttributes = {
              'gen_ai.system': 'bedrock',
              content:
                typeof message.content === 'string'
                  ? message.content
                  : JSON.stringify(message.content),
            };
            span.addEvent(eventName, eventAttributes);
          });
        }
        break;
      case 'amazon':
        if (body.inputText) {
          const eventName = 'gen_ai.user.message';
          const eventAttributes = {
            'gen_ai.system': 'bedrock',
            content: body.inputText,
          };
          span.addEvent(eventName, eventAttributes);
        }
        break;
      case 'meta':
        if (body.prompt) {
          const eventName = 'gen_ai.user.message';
          const eventAttributes = {
            'gen_ai.system': 'bedrock',
            content: body.prompt,
          };
          span.addEvent(eventName, eventAttributes);
        }
        break;
      default:
        if (body.prompt) {
          span.addEvent('gen_ai.user.message', {
            'gen_ai.system': 'bedrock',
            content: body.prompt,
          });
        }
        break;
    }
  }

  private _recordResponse(span: OtelSpan, response: any, provider: string): void {
    switch (provider) {
      case 'anthropic': {
        const anthropicResponse = response as BedrockAnthropicResponse;
        if (anthropicResponse.content) {
          anthropicResponse.content.forEach((content, index) => {
            if (content.type === 'text') {
              span.addEvent('gen_ai.choice', {
                'gen_ai.system': 'bedrock',
                index: index,
                message: JSON.stringify({ role: 'assistant', content: content.text }),
                finish_reason: anthropicResponse.stop_reason || '',
              });
            }
          });
        }
        if (anthropicResponse.stop_reason) {
          span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, [
            anthropicResponse.stop_reason,
          ]);
        }
        if (anthropicResponse.usage) {
          span.setAttributes({
            [SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS]: anthropicResponse.usage.input_tokens,
            [SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS]: anthropicResponse.usage.output_tokens,
          });
        }
        break;
      }

      case 'amazon': {
        const titanResponse = response as BedrockTitanResponse;
        if (titanResponse.results) {
          titanResponse.results.forEach((result, index) => {
            span.addEvent('gen_ai.choice', {
              'gen_ai.system': 'bedrock',
              index: index,
              message: JSON.stringify({ role: 'assistant', content: result.outputText }),
              finish_reason: result.completionReason || '',
            });
          });
          const finishReasons = titanResponse.results
            .map((r) => r.completionReason)
            .filter(Boolean);
          if (finishReasons.length > 0) {
            span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, finishReasons);
          }
        }
        if (titanResponse.inputTextTokenCount) {
          span.setAttribute(SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS, titanResponse.inputTextTokenCount);
        }
        break;
      }

      case 'meta': {
        const llamaResponse = response as BedrockLlamaResponse;
        if (llamaResponse.generation) {
          span.addEvent('gen_ai.choice', {
            'gen_ai.system': 'bedrock',
            index: 0,
            message: JSON.stringify({ role: 'assistant', content: llamaResponse.generation }),
            finish_reason: llamaResponse.stop_reason || '',
          });
        }
        if (llamaResponse.stop_reason) {
          span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, [llamaResponse.stop_reason]);
        }
        if (llamaResponse.prompt_token_count) {
          span.setAttribute(SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS, llamaResponse.prompt_token_count);
        }
        if (llamaResponse.generation_token_count) {
          span.setAttribute(
            SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS,
            llamaResponse.generation_token_count,
          );
        }
        break;
      }
    }
  }

  private _wrapStream(
    span: OtelSpan,
    stream: AsyncIterable<BedrockResponseStreamChunk>,
    provider: string,
    _config: BedrockInstrumentationConfig,
  ): AsyncIterable<BedrockResponseStreamChunk> {
    let content = '';
    let finishReason: string | null = null;
    let inputTokens = 0;
    let outputTokens = 0;

    const onChunk = (chunk: BedrockResponseStreamChunk) => {
      // Process chunk based on provider
      if (chunk.chunk?.bytes) {
        try {
          const data = JSON.parse(new TextDecoder().decode(chunk.chunk.bytes));

          switch (provider) {
            case 'anthropic':
              if (data.type === 'content_block_delta' && data.delta?.text) {
                content += data.delta.text;
              } else if (data.type === 'message_stop') {
                finishReason = data.stop_reason || 'stop';
                if (data.usage) {
                  inputTokens = data.usage.input_tokens;
                  outputTokens = data.usage.output_tokens;
                }
              }
              break;
            // Add other provider stream handling as needed
          }
        } catch (e) {
          logger.debug('[BedrockInstrumentation] Failed to parse stream chunk:', e);
        }
      }
    };

    const onFinalize = () => {
      // Record final data
      if (content || finishReason) {
        span.addEvent('gen_ai.choice', {
          'gen_ai.system': 'bedrock',
          index: 0,
          message: JSON.stringify({ role: 'assistant', content }),
          finish_reason: finishReason || 'error',
        });
      }

      if (finishReason) {
        span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, [finishReason]);
      }

      if (inputTokens || outputTokens) {
        span.setAttributes({
          [SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS]: inputTokens,
          [SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS]: outputTokens,
        });
      }

      span.setStatus({ code: SpanStatusCode.OK });
      span.end();
    };

    return new StreamWrapper(stream, span, { onChunk, onFinalize });
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
