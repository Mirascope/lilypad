import { trace, SpanStatusCode, SpanKind, Span as OtelSpan } from '@opentelemetry/api';

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
      // Try to require OpenAI module
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      this.openaiModule = require('openai') as OpenAIModule;

      // Patch the chat completions methods
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
      // Restore original methods
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
    } else if ('OpenAI' in this.openaiModule && this.openaiModule.OpenAI) {
      OpenAI = this.openaiModule.OpenAI;
    } else {
      OpenAI = this.openaiModule as OpenAIClass;
    }

    // Store original methods
    const originalCreate = OpenAI.prototype.chat?.completions?.create;
    if (originalCreate) {
      this.storeOriginal('chat.completions.create', originalCreate);

      // Patch the create method
      if (OpenAI.prototype.chat && this.isCompletionsAPI(OpenAI.prototype.chat.completions)) {
        OpenAI.prototype.chat.completions.create = this.wrapChatCompletionsCreate(
          originalCreate,
        ) as typeof OpenAI.prototype.chat.completions.create;
      }
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

      return tracer.startActiveSpan(
        spanName,
        {
          kind: SpanKind.CLIENT,
          attributes: {
            [SEMATTRS_GEN_AI_SYSTEM]: 'openai',
            [SEMATTRS_GEN_AI_REQUEST_MODEL]: model,
            [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: params?.temperature,
            [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: params?.max_tokens,
            [SEMATTRS_GEN_AI_REQUEST_TOP_P]: params?.top_p,
            'gen_ai.request.presence_penalty': params?.presence_penalty,
            'gen_ai.request.frequency_penalty': params?.frequency_penalty,
            'gen_ai.openai.request.response_format': params?.response_format?.type,
            'gen_ai.openai.request.seed': params?.seed,
            [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
            'lilypad.type': 'llm',
          },
        },
        async (span) => {
          try {
            // Record messages
            if (params?.messages) {
              params.messages.forEach((message, index) => {
                span.addEvent(`gen_ai.content.prompt`, {
                  'gen_ai.prompt.role': String(message.role),
                  'gen_ai.prompt.content': safeStringify(message.content),
                  'gen_ai.prompt.index': String(index),
                });
              });
            }

            // Call original method
            const result = await original.apply(this, [params, options]);

            // Handle streaming response
            if (params?.stream && isAsyncIterable(result)) {
              return self.handleStreamingResponse(
                result as AsyncIterable<ChatCompletionChunk>,
                span,
              );
            }

            // Handle regular response
            self.recordCompletionResponse(span, result);

            span.setStatus({ code: SpanStatusCode.OK });
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

        // Record the completed response
        span.addEvent('gen_ai.content.completion', {
          'gen_ai.completion.content': fullContent,
          'gen_ai.completion.finish_reason': finishReason || '',
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

    // Record choices
    if (response.choices) {
      response.choices.forEach((choice, index) => {
        span.addEvent('gen_ai.content.completion', {
          'gen_ai.completion.index': String(index),
          'gen_ai.completion.role': choice.message?.role || '',
          'gen_ai.completion.content': choice.message?.content || '',
          'gen_ai.completion.finish_reason': choice.finish_reason || '',
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
