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
  GoogleGenerateContentParams,
  GoogleGenerateContentResponse,
  GoogleContentChunk,
  GoogleContent,
} from '../types/google';

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

const MODULE_NAME = '@google/generative-ai';
const SUPPORTED_VERSIONS = ['>=0.1.0'];

export interface GoogleInstrumentationConfig extends InstrumentationConfig {
  /**
   * Hook called before request is sent
   */
  requestHook?: (span: OtelSpan, params: GoogleGenerateContentParams | string) => void;

  /**
   * Hook called after response is received
   */
  responseHook?: (span: OtelSpan, response: GoogleGenerateContentResponse) => void;

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
const LILYPAD_INSTRUMENTED = Symbol.for('lilypad.google.instrumented');

export class GoogleInstrumentation extends InstrumentationBase {
  constructor(config: GoogleInstrumentationConfig = {}) {
    super('@lilypad/instrumentation-google', '0.1.0', config);
  }

  protected init() {
    logger.info('[GoogleInstrumentation] Initializing Google instrumentation');
    const module = new InstrumentationNodeModuleDefinition(
      MODULE_NAME,
      SUPPORTED_VERSIONS,
      (moduleExports, moduleVersion) => {
        logger.info(
          `[GoogleInstrumentation] Applying patch for @google/generative-ai@${moduleVersion}`,
        );
        return this._applyPatch(moduleExports);
      },
      (moduleExports, moduleVersion) => {
        logger.info(
          `[GoogleInstrumentation] Removing patch for @google/generative-ai@${moduleVersion}`,
        );
        return this._removePatch(moduleExports);
      },
    );

    return [module];
  }

  private _applyPatch(moduleExports: any): any {
    // Check if already instrumented by Lilypad
    if (moduleExports && moduleExports[LILYPAD_INSTRUMENTED]) {
      logger.warn('[GoogleInstrumentation] Module already instrumented by Lilypad, skipping');
      return moduleExports;
    }

    // Check for other instrumentation libraries
    const otherInstrumentations = this._detectOtherInstrumentations(moduleExports);
    if (otherInstrumentations.length > 0) {
      logger.warn(
        '[GoogleInstrumentation] Detected other instrumentations:',
        otherInstrumentations.join(', '),
      );
      if (!(this._config as GoogleInstrumentationConfig).suppressInternalInstrumentation) {
        logger.warn('[GoogleInstrumentation] Proceeding with caution - may cause conflicts');
      }
    }

    logger.info('[GoogleInstrumentation] Patching Google module');
    logger.info('[GoogleInstrumentation] Module exports:', Object.keys(moduleExports || {}));

    // Handle different export patterns
    let GoogleGenerativeAI: any;
    if (moduleExports.GoogleGenerativeAI) {
      GoogleGenerativeAI = moduleExports.GoogleGenerativeAI;
      logger.info('[GoogleInstrumentation] Found GoogleGenerativeAI export');
    } else if (moduleExports.default?.GoogleGenerativeAI) {
      GoogleGenerativeAI = moduleExports.default.GoogleGenerativeAI;
      logger.info('[GoogleInstrumentation] Found GoogleGenerativeAI in default export');
    } else if (moduleExports.default) {
      GoogleGenerativeAI = moduleExports.default;
      logger.info('[GoogleInstrumentation] Using default export');
    } else {
      logger.error('[GoogleInstrumentation] GoogleGenerativeAI class not found');
      if ((this._config as GoogleInstrumentationConfig).fallbackToProxy) {
        return this._applyProxyFallback(moduleExports);
      }
      return moduleExports;
    }

    if (!GoogleGenerativeAI || !GoogleGenerativeAI.prototype) {
      logger.error(
        '[GoogleInstrumentation] GoogleGenerativeAI class not found or has no prototype',
      );
      if ((this._config as GoogleInstrumentationConfig).fallbackToProxy) {
        return this._applyProxyFallback(moduleExports);
      }
      return moduleExports;
    }

    // Apply shimmer to wrap the getGenerativeModel method
    this._wrapGetGenerativeModel(GoogleGenerativeAI.prototype);
    logger.info('[GoogleInstrumentation] Successfully applied patch');

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
    logger.debug('[GoogleInstrumentation] Removing Google patches');

    let GoogleGenerativeAI: any;
    if (moduleExports.GoogleGenerativeAI) {
      GoogleGenerativeAI = moduleExports.GoogleGenerativeAI;
    } else if (moduleExports.default?.GoogleGenerativeAI) {
      GoogleGenerativeAI = moduleExports.default.GoogleGenerativeAI;
    } else if (moduleExports.default) {
      GoogleGenerativeAI = moduleExports.default;
    }

    if (GoogleGenerativeAI?.prototype?.getGenerativeModel) {
      shimmer.unwrap(GoogleGenerativeAI.prototype, 'getGenerativeModel');
    }

    return moduleExports;
  }

  private _wrapGetGenerativeModel(prototype: any): void {
    const instrumentation = this;

    if (!prototype.getGenerativeModel) {
      logger.error('[GoogleInstrumentation] getGenerativeModel not found on prototype');
      return;
    }

    if (isWrapped(prototype.getGenerativeModel)) {
      logger.debug('[GoogleInstrumentation] getGenerativeModel already wrapped');
      return;
    }

    shimmer.wrap(prototype, 'getGenerativeModel', (original: Function) => {
      logger.debug('[GoogleInstrumentation] getGenerativeModel wrapper called');
      return function (this: any, ...args: any[]) {
        logger.debug('[GoogleInstrumentation] getGenerativeModel executing');
        const model = original.apply(this, args);
        const [config] = args;

        if (model && typeof model === 'object') {
          // Store the model name on the instance
          if (config?.model) {
            model._modelName = config.model;
          }

          logger.debug('[GoogleInstrumentation] Model instance:', {
            hasGenerateContent: !!model.generateContent,
            hasGenerateContentStream: !!model.generateContentStream,
            modelName: model._modelName,
            generateContentType: typeof model.generateContent,
            generateContentStreamType: typeof model.generateContentStream,
          });

          // Wrap generateContent
          if (model.generateContent && !isWrapped(model.generateContent)) {
            shimmer.wrap(model, 'generateContent', (originalGenerateContent: Function) => {
              logger.debug('[GoogleInstrumentation] Wrapped generateContent');
              return instrumentation._createWrappedGenerateContent(
                originalGenerateContent,
                model._modelName,
              );
            });
          }

          // Wrap generateContentStream
          if (model.generateContentStream && !isWrapped(model.generateContentStream)) {
            shimmer.wrap(
              model,
              'generateContentStream',
              (originalGenerateContentStream: Function) => {
                return instrumentation._createWrappedGenerateContentStream(
                  originalGenerateContentStream,
                  model._modelName,
                );
              },
            );
          }

          // Wrap startChat to instrument ChatSession
          if (model.startChat && !isWrapped(model.startChat)) {
            shimmer.wrap(model, 'startChat', (originalStartChat: Function) => {
              return function (this: any, ...args: any[]) {
                const chatSession = originalStartChat.apply(this, args);

                if (chatSession && chatSession.sendMessage && !isWrapped(chatSession.sendMessage)) {
                  // Store the model name on the chat session
                  chatSession._modelName = model._modelName;

                  shimmer.wrap(chatSession, 'sendMessage', (originalSendMessage: Function) => {
                    logger.debug('[GoogleInstrumentation] Wrapped chatSession.sendMessage');
                    return instrumentation._createWrappedSendMessage(
                      originalSendMessage,
                      model._modelName,
                    );
                  });
                }

                return chatSession;
              };
            });
          }
        }

        return model;
      };
    });

    logger.debug('[GoogleInstrumentation] Successfully wrapped getGenerativeModel');
  }

  private _createWrappedGenerateContent(original: Function, modelName?: string): Function {
    const instrumentation = this;
    return async function (this: any, ...args: any[]) {
      logger.debug('[GoogleInstrumentation] generateContent called with:', {
        modelName,
        inputType: typeof args[0],
      });

      // Skip if shutting down
      if (isSDKShuttingDown()) {
        return original.apply(this, args);
      }

      const [input] = args;
      const params = instrumentation._normalizeInput(input);
      const tracer = instrumentation.tracer;
      const config = instrumentation._config as GoogleInstrumentationConfig;

      // Get the active context to preserve parent-child relationships
      const activeContext = context.active();

      // Start span using the OTel way with active context
      const span = tracer.startSpan(
        `google.generateContent ${modelName || 'unknown'}`,
        {
          kind: SpanKind.CLIENT,
          attributes: {
            [SEMATTRS_GEN_AI_SYSTEM]: 'google_genai',
            [SEMATTRS_GEN_AI_REQUEST_MODEL]: modelName,
            [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: params.generation_config?.temperature,
            [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: params.generation_config?.max_output_tokens,
            [SEMATTRS_GEN_AI_REQUEST_TOP_P]: params.generation_config?.top_p,
            'gen_ai.request.top_k': params.generation_config?.top_k,
            [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
            'lilypad.type': 'trace',
            'server.address': 'generativelanguage.googleapis.com',
          },
        },
        activeContext,
      );

      logger.debug('[GoogleInstrumentation] Created Google span:', {
        spanId: span.spanContext().spanId,
        traceId: span.spanContext().traceId,
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
          instrumentation._recordMessages(span, params.contents);

          // Call original method
          const result = await original.apply(this, args);

          // Record response
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

  private _createWrappedSendMessage(original: Function, modelName?: string): Function {
    const instrumentation = this;
    return async function (this: any, ...args: any[]) {
      logger.debug('[GoogleInstrumentation] chatSession.sendMessage called with:', {
        modelName,
        inputType: typeof args[0],
      });

      // Skip if shutting down
      if (isSDKShuttingDown()) {
        return original.apply(this, args);
      }

      const [message] = args;
      const tracer = instrumentation.tracer;
      const config = instrumentation._config as GoogleInstrumentationConfig;

      // Get the active context to preserve parent-child relationships
      const activeContext = context.active();

      // Start span for chat message
      const span = tracer.startSpan(
        `google.chat.sendMessage ${modelName || 'unknown'}`,
        {
          kind: SpanKind.CLIENT,
          attributes: {
            [SEMATTRS_GEN_AI_SYSTEM]: 'google_genai',
            [SEMATTRS_GEN_AI_REQUEST_MODEL]: modelName,
            [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
            'lilypad.type': 'trace',
            'server.address': 'generativelanguage.googleapis.com',
          },
        },
        activeContext,
      );

      logger.debug('[GoogleInstrumentation] Created Google chat span:', {
        spanId: span.spanContext().spanId,
        traceId: span.spanContext().traceId,
      });

      // Set span in context for proper context propagation
      const contextWithSpan = trace.setSpan(context.active(), span);

      return context.with(contextWithSpan, async () => {
        try {
          // Call request hook if provided
          if (config.requestHook) {
            config.requestHook(span, message);
          }

          // Record the user message as array to match Python implementation
          span.addEvent('gen_ai.user.message', {
            'gen_ai.system': 'google_genai',
            content: JSON.stringify([
              typeof message === 'string' ? message : JSON.stringify(message),
            ]),
          });

          // Call original method
          const result = await original.apply(this, args);

          // Record response
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

  private _createWrappedGenerateContentStream(original: Function, modelName?: string): Function {
    const instrumentation = this;
    return async function (this: any, ...args: any[]) {
      // Skip if shutting down
      if (isSDKShuttingDown()) {
        return original.apply(this, args);
      }

      const [input] = args;
      const params = instrumentation._normalizeInput(input);
      const tracer = instrumentation.tracer;
      const config = instrumentation._config as GoogleInstrumentationConfig;

      // Get the active context to preserve parent-child relationships
      const activeContext = context.active();

      // Start span using the OTel way with active context
      const span = tracer.startSpan(
        `google.generateContentStream ${modelName || 'unknown'}`,
        {
          kind: SpanKind.CLIENT,
          attributes: {
            [SEMATTRS_GEN_AI_SYSTEM]: 'google_genai',
            [SEMATTRS_GEN_AI_REQUEST_MODEL]: modelName,
            [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: params.generation_config?.temperature,
            [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: params.generation_config?.max_output_tokens,
            [SEMATTRS_GEN_AI_REQUEST_TOP_P]: params.generation_config?.top_p,
            'gen_ai.request.top_k': params.generation_config?.top_k,
            [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
            'lilypad.type': 'trace',
            'server.address': 'generativelanguage.googleapis.com',
            'gen_ai.request.stream': true,
          },
        },
        activeContext,
      );

      logger.debug('[GoogleInstrumentation] Created Google stream span:', {
        spanId: span.spanContext().spanId,
        traceId: span.spanContext().traceId,
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
          instrumentation._recordMessages(span, params.contents);

          // Call original method
          const result = await original.apply(this, args);

          // Google's generateContentStream returns an object with a 'stream' property
          // that is the actual async iterable
          if (
            result &&
            typeof result === 'object' &&
            'stream' in result &&
            isAsyncIterable(result.stream)
          ) {
            // Wrap the stream but return the full result object
            const wrappedStream = instrumentation._wrapStream(
              span,
              result.stream as AsyncIterable<GoogleContentChunk>,
              config,
            );

            // Return an object with the same structure as Google's response
            return {
              ...result,
              stream: wrappedStream,
            };
          }

          // If not a stream response, just return it
          span.setStatus({ code: SpanStatusCode.OK });
          span.end();
          return result;
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

  private _normalizeInput(
    input: GoogleGenerateContentParams | GoogleContent[] | string,
  ): GoogleGenerateContentParams {
    if (typeof input === 'string') {
      return {
        contents: [{ role: 'user', parts: [{ text: input }] }],
      };
    }
    if (Array.isArray(input)) {
      return {
        contents: input,
      };
    }
    return input;
  }

  private _recordMessages(span: OtelSpan, contents: GoogleContent[]): void {
    if (!contents || !Array.isArray(contents)) return;

    contents.forEach((content) => {
      const contentParts: any[] = [];

      if (content.parts && Array.isArray(content.parts)) {
        content.parts.forEach((part) => {
          if ('text' in part && part.text) {
            contentParts.push(part.text);
          } else if ('inline_data' in part) {
            // Handle binary data similar to Python
            contentParts.push({
              mime_type: part.inline_data.mime_type,
              data: part.inline_data.data, // Already base64 encoded
            });
          }
        });
      }

      // Use same event structure as Python
      const eventRole = content.role === 'model' ? 'model' : content.role;
      span.addEvent(`gen_ai.${eventRole}.message`, {
        'gen_ai.system': 'google_genai',
        content: JSON.stringify(contentParts),
      });
    });
  }

  private _wrapStream(
    span: OtelSpan,
    stream: AsyncIterable<GoogleContentChunk>,
    _config: GoogleInstrumentationConfig,
  ): AsyncIterable<GoogleContentChunk> {
    let content = '';
    let finishReason: string | null = null;
    let usage: any = null;

    const onChunk = (chunk: GoogleContentChunk) => {
      if (chunk.candidates && chunk.candidates.length > 0) {
        chunk.candidates.forEach((candidate) => {
          if (candidate.content?.parts) {
            candidate.content.parts.forEach((part) => {
              if ('text' in part && part.text) {
                content += part.text;
              }
            });
          }
          if (candidate.finishReason || candidate.finish_reason) {
            finishReason = candidate.finishReason || candidate.finish_reason || null;
          }
        });
      }

      // Capture usage data if present
      if (chunk.usageMetadata || chunk.usage_metadata) {
        usage = chunk.usageMetadata || chunk.usage_metadata;
      }

      // Add chunk event
      span.addEvent('gen_ai.chunk', {
        size: content.length,
      });
    };

    const onFinalize = () => {
      // Record the completed stream
      if (content || finishReason) {
        // Match Python implementation: content as array
        const messageDict = {
          role: 'model',
          content: [content], // Array of content parts
        };

        span.addEvent('gen_ai.choice', {
          'gen_ai.system': 'google_genai',
          index: 0,
          message: JSON.stringify(messageDict),
          finish_reason: finishReason || 'stop',
        });
      }

      if (finishReason) {
        span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, [finishReason]);
      }

      // Record usage if available - handle both camelCase and snake_case
      if (usage) {
        span.setAttributes({
          [SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS]:
            usage.promptTokenCount || usage.prompt_token_count || 0,
          [SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS]:
            usage.candidatesTokenCount || usage.candidates_token_count || 0,
          'gen_ai.usage.total_tokens': usage.totalTokenCount || usage.total_token_count || 0,
        });
      }

      span.setAttribute('server.address', 'generativelanguage.googleapis.com');
      span.setStatus({ code: SpanStatusCode.OK });
      span.end();
    };

    return new StreamWrapper(stream, span, { onChunk, onFinalize });
  }

  private _recordResponse(span: OtelSpan, result: any): void {
    if (!result) return;

    // Google returns result.response, not direct response
    const response = result.response || result;

    // Type guard for GoogleGenerateContentResponse
    if (!response.candidates || !Array.isArray(response.candidates)) {
      logger.debug('[GoogleInstrumentation] No candidates found in response');
      return;
    }

    // Record response attributes
    const finishReasons: string[] = [];
    response.candidates.forEach((candidate: any, index: number) => {
      if (candidate.content) {
        const contentParts: string[] = [];
        if (candidate.content.parts && Array.isArray(candidate.content.parts)) {
          candidate.content.parts.forEach((part: any) => {
            if ('text' in part && part.text) {
              contentParts.push(part.text);
            }
          });
        }

        // Match Python implementation: content as array of parts
        const messageDict = {
          role: candidate.content.role || 'model',
          content: contentParts,
        };

        span.addEvent('gen_ai.choice', {
          'gen_ai.system': 'google_genai',
          index: index,
          message: JSON.stringify(messageDict),
          finish_reason: candidate.finishReason || candidate.finish_reason || 'stop',
        });
      }

      // Google uses finishReason (camelCase)
      const finishReason = candidate.finishReason || candidate.finish_reason;
      if (finishReason) {
        finishReasons.push(finishReason);
      }
    });

    // Record finish reasons
    if (finishReasons.length > 0) {
      span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, finishReasons);
    }

    // Record usage - Google uses camelCase (usageMetadata) not snake_case
    const usageMetadata = response.usageMetadata || response.usage_metadata;
    if (usageMetadata) {
      span.setAttributes({
        [SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS]:
          usageMetadata.promptTokenCount || usageMetadata.prompt_token_count || 0,
        [SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS]:
          usageMetadata.candidatesTokenCount || usageMetadata.candidates_token_count || 0,
        'gen_ai.usage.total_tokens':
          usageMetadata.totalTokenCount || usageMetadata.total_token_count || 0,
      });
    }

    span.setAttribute('server.address', 'generativelanguage.googleapis.com');
  }

  private _applyProxyFallback(moduleExports: any): any {
    logger.debug('[GoogleInstrumentation] Applying Proxy fallback');

    const instrumentation = this;
    const handler = {
      construct(target: any, args: any[]) {
        const instance = new target(...args);
        return instrumentation._proxyInstance(instance);
      },
    };

    if (moduleExports.GoogleGenerativeAI) {
      moduleExports.GoogleGenerativeAI = new Proxy(moduleExports.GoogleGenerativeAI, handler);
    } else if (moduleExports.default?.GoogleGenerativeAI) {
      moduleExports.default.GoogleGenerativeAI = new Proxy(
        moduleExports.default.GoogleGenerativeAI,
        handler,
      );
    } else if (moduleExports.default && typeof moduleExports.default === 'function') {
      moduleExports.default = new Proxy(moduleExports.default, handler);
    }

    return moduleExports;
  }

  private _proxyInstance(instance: any): any {
    const instrumentation = this;

    // Deep proxy to intercept getGenerativeModel calls
    const handler: ProxyHandler<any> = {
      get(target, prop, receiver) {
        const value = Reflect.get(target, prop, receiver);

        // Intercept getGenerativeModel
        if (prop === 'getGenerativeModel' && typeof value === 'function') {
          return function (...args: any[]) {
            const model = value.apply(target, args);
            const [config] = args;

            if (model && typeof model === 'object') {
              // Store the model name
              if (config?.model) {
                model._modelName = config.model;
              }

              // Wrap generateContent
              if (model.generateContent) {
                const originalGenerateContent = model.generateContent.bind(model);
                model.generateContent = instrumentation._createWrappedGenerateContent(
                  originalGenerateContent,
                  model._modelName,
                );
              }

              // Wrap generateContentStream
              if (model.generateContentStream) {
                const originalGenerateContentStream = model.generateContentStream.bind(model);
                model.generateContentStream = instrumentation._createWrappedGenerateContentStream(
                  originalGenerateContentStream,
                  model._modelName,
                );
              }
            }

            return model;
          };
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

    // Check Google specific paths
    const googlePaths = [
      ['GoogleGenerativeAI', 'prototype', 'getGenerativeModel'],
      ['default', 'GoogleGenerativeAI', 'prototype', 'getGenerativeModel'],
      ['prototype', 'getGenerativeModel'],
    ];

    for (const path of googlePaths) {
      if (checkWrapped(moduleExports, path)) {
        detectedInstrumentations.push('Unknown (wrapped method detected)');
        break;
      }
    }

    // Remove duplicates
    return [...new Set(detectedInstrumentations)];
  }
}
