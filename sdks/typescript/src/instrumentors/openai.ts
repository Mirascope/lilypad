import {
  trace,
  SpanStatusCode,
  SpanKind,
  Span as OtelSpan,
  Attributes,
  AttributeValue,
} from '@opentelemetry/api';

import { BaseInstrumentor } from './base';
import { logger } from '../utils/logger';
import { StreamWrapper, isAsyncIterable } from '../utils/stream-wrapper';
import { safeStringify } from '../utils/json';
import { isSDKShuttingDown } from '../shutdown';
import type {
  OpenAIModule,
  OpenAIClass,
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

const TRACER_NAME = 'lilypad-openai';
const TRACER_VERSION = '0.1.0';

// Helper function to filter out null/undefined attributes
function filterAttributes(attrs: Record<string, unknown>): Attributes {
  const result: Attributes = {};
  for (const [key, value] of Object.entries(attrs)) {
    if (value !== null && value !== undefined) {
      result[key] = value as AttributeValue;
    }
  }
  return result;
}

interface CompletionsAPI {
  create: Function;
}

export class OpenAIInstrumentor extends BaseInstrumentor {
  private openaiModule: OpenAIModule | null = null;

  getName(): string {
    return 'OpenAI';
  }

  instrument(): void {
    if (this.isInstrumented()) {
      logger.warn('OpenAI already instrumented');
      return;
    }

    try {
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      this.openaiModule = require('openai') as OpenAIModule;

      this.patchChatCompletions();

      this.isInstrumentedFlag = true;
      logger.info('OpenAI instrumentation enabled');
    } catch (error) {
      logger.error('Failed to instrument OpenAI:', error);
      this.isInstrumentedFlag = false;
      throw new Error(
        `OpenAI instrumentation failed: ${error instanceof Error ? error.message : String(error)}. ` +
          'Please ensure OpenAI is properly installed.',
      );
    }
  }

  uninstrument(): void {
    if (!this.isInstrumented()) {
      return;
    }

    try {
      this.restoreChatCompletions();

      this.isInstrumentedFlag = false;
      this.clearOriginals();
      logger.info('OpenAI instrumentation disabled');
    } catch (error) {
      logger.error('Failed to uninstrument OpenAI:', error);
    }
  }

  private patchChatCompletions(): void {
    if (!this.openaiModule) return;

    let OpenAI: OpenAIClass;
    if ('default' in this.openaiModule && this.openaiModule.default) {
      OpenAI = this.openaiModule.default;
      logger.debug('Using OpenAI from default export');
    } else if ('OpenAI' in this.openaiModule && this.openaiModule.OpenAI) {
      OpenAI = this.openaiModule.OpenAI;
      logger.debug('Using OpenAI from named export');
    } else {
      OpenAI = this.openaiModule as OpenAIClass;
      logger.debug('Using OpenAI module directly');
    }

    if (!OpenAI.prototype) {
      logger.error('OpenAI.prototype is undefined');
      return;
    }

    if (!OpenAI.prototype.chat) {
      logger.error('OpenAI.prototype.chat is undefined');
      return;
    }

    const originalCreate = OpenAI.prototype.chat?.completions?.create;
    if (originalCreate) {
      logger.debug('Found original chat.completions.create method');
      this.storeOriginal('chat.completions.create', originalCreate);

      if (OpenAI.prototype.chat && this.isCompletionsAPI(OpenAI.prototype.chat.completions)) {
        OpenAI.prototype.chat.completions.create = this.wrapChatCompletionsCreate(
          originalCreate,
        ) as typeof OpenAI.prototype.chat.completions.create;
        logger.debug('Successfully patched chat.completions.create');
      }
    } else {
      logger.error('Could not find chat.completions.create method');
    }
  }

  private restoreChatCompletions(): void {
    if (!this.openaiModule) return;

    let OpenAI: OpenAIClass;
    if ('default' in this.openaiModule && this.openaiModule.default) {
      OpenAI = this.openaiModule.default;
    } else if ('OpenAI' in this.openaiModule && this.openaiModule.OpenAI) {
      OpenAI = this.openaiModule.OpenAI;
    } else {
      OpenAI = this.openaiModule as OpenAIClass;
    }

    const originalCreate = this.getOriginal('chat.completions.create');
    if (
      originalCreate &&
      OpenAI.prototype.chat &&
      this.isCompletionsAPI(OpenAI.prototype.chat.completions)
    ) {
      OpenAI.prototype.chat.completions.create =
        originalCreate as typeof OpenAI.prototype.chat.completions.create;
    }
  }

  private wrapChatCompletionsCreate(original: Function): Function {
    const self = this;

    return async function (
      this: unknown,
      params: ChatCompletionParams,
      options?: unknown,
    ): Promise<ChatCompletionResponse | AsyncIterable<ChatCompletionChunk>> {
      // Skip instrumentation if SDK is shutting down
      if (isSDKShuttingDown()) {
        return original.apply(this, [params, options]);
      }

      const tracer = trace.getTracer(TRACER_NAME, TRACER_VERSION);
      const model = params?.model || 'unknown';
      const spanName = `openai.chat.completions ${model}`;

      logger.debug(`OpenAI instrumentor: Creating span "${spanName}"`);
      logger.debug(
        `Parameters: ${JSON.stringify({ model, temperature: params?.temperature, max_tokens: params?.max_tokens })}`,
      );

      return tracer.startActiveSpan(
        spanName,
        {
          kind: SpanKind.CLIENT,
          attributes: filterAttributes({
            [SEMATTRS_GEN_AI_SYSTEM]: 'openai',
            [SEMATTRS_GEN_AI_REQUEST_MODEL]: model,
            [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: params?.temperature,
            [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: params?.max_tokens,
            [SEMATTRS_GEN_AI_REQUEST_TOP_P]: params?.top_p || (params as any)?.p,
            'gen_ai.request.presence_penalty': params?.presence_penalty,
            'gen_ai.request.frequency_penalty': params?.frequency_penalty,
            'gen_ai.openai.request.response_format': params?.response_format?.type,
            'gen_ai.openai.request.seed': params?.seed,
            'gen_ai.openai.request.service_tier':
              params?.service_tier !== 'auto' ? params?.service_tier : undefined,
            [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
            'lilypad.type': 'llm',
          }),
        },
        async (span) => {
          try {
            // Record messages - match Python SDK format
            if (params?.messages) {
              params.messages.forEach((message) => {
                const eventName = `gen_ai.${message.role}.message`;
                const attributes: Attributes = {
                  [SEMATTRS_GEN_AI_SYSTEM]: 'openai',
                };

                if (message.content) {
                  attributes['content'] =
                    typeof message.content === 'string'
                      ? message.content
                      : safeStringify(message.content);
                }

                span.addEvent(eventName, attributes);
              });
            }

            const result = await original.apply(this, [params, options]);

            if (params?.stream && isAsyncIterable(result)) {
              return self.handleStreamingResponse(
                result as AsyncIterable<ChatCompletionChunk>,
                span,
              );
            }

            self.recordCompletionResponse(span, result);

            span.setStatus({ code: SpanStatusCode.OK });
            logger.debug(`OpenAI instrumentor: Span completed successfully for ${spanName}`);
            return result;
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            span.recordException(error as Error);
            span.setAttributes({
              error: true,
              'error.type': error?.constructor?.name || 'Error',
              'error.message': errorMessage,
            });
            span.setStatus({ code: SpanStatusCode.ERROR, message: errorMessage });
            throw error;
          } finally {
            span.end();
          }
        },
      );
    };
  }

  private handleStreamingResponse(
    stream: AsyncIterable<ChatCompletionChunk>,
    span: OtelSpan,
  ): AsyncIterable<ChatCompletionChunk> {
    const chunks: ChatCompletionChunk[] = [];

    return new StreamWrapper(stream, span, {
      onChunk: (chunk) => {
        chunks.push(chunk);
      },
      onFinalize: () => {
        // Reconstruct the full response from chunks
        const fullContent = chunks
          .map((chunk) => chunk.choices?.[0]?.delta?.content || '')
          .join('');

        const lastChunk = chunks[chunks.length - 1];
        const finishReason = lastChunk?.choices?.[0]?.finish_reason;

        // Record the completed response - match Python SDK format
        const message: Record<string, unknown> = {
          role: 'assistant',
          content: fullContent,
        };

        span.addEvent('gen_ai.choice', {
          [SEMATTRS_GEN_AI_SYSTEM]: 'openai',
          index: 0,
          finish_reason: finishReason || 'error',
          message: safeStringify(message),
        });

        // Try to get usage from the last chunk
        if (lastChunk?.usage) {
          span.setAttributes({
            [SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS]: lastChunk.usage.prompt_tokens,
            [SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS]: lastChunk.usage.completion_tokens,
            'gen_ai.usage.total_tokens': lastChunk.usage.total_tokens,
          });
        }

        if (finishReason) {
          span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, [finishReason]);
        }
      },
    });
  }

  private recordCompletionResponse(span: OtelSpan, response: ChatCompletionResponse): void {
    if (!response) return;

    // Record choices - match Python SDK format
    if (response.choices) {
      response.choices.forEach((choice, index) => {
        const message: Record<string, unknown> = {
          role: choice.message?.role || 'assistant',
        };

        if (choice.message?.content) {
          message['content'] = choice.message.content;
        }

        span.addEvent('gen_ai.choice', {
          [SEMATTRS_GEN_AI_SYSTEM]: 'openai',
          index: index,
          finish_reason: choice.finish_reason || 'error',
          message: safeStringify(message),
        });
      });

      // Record finish reasons
      const finishReasons = response.choices
        .map((c) => c.finish_reason)
        .filter((reason): reason is string => Boolean(reason));
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

    // Record model (might be different from requested)
    if (response.model) {
      span.setAttribute('gen_ai.response.model', response.model);
    }

    // Record ID
    if (response.id) {
      span.setAttribute('gen_ai.response.id', response.id);
    }

    // Record service tier if different from 'auto'
    if (response.service_tier && response.service_tier !== 'auto') {
      span.setAttribute('gen_ai.openai.response.service_tier', response.service_tier);
    }
  }

  private isCompletionsAPI(obj: unknown): obj is CompletionsAPI {
    return (
      obj !== null &&
      typeof obj === 'object' &&
      'create' in obj &&
      typeof (obj as CompletionsAPI).create === 'function'
    );
  }
}
