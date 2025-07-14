/**
 * Manual OpenAI wrapping for environments where auto-instrumentation doesn't work
 * (e.g., Bun, Deno)
 */

import { trace, context, SpanKind, SpanStatusCode } from '@opentelemetry/api';
import { logger } from './utils/logger';
import { isAsyncIterable } from './utils/stream-wrapper';

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
} from './constants/gen-ai-semantic-conventions';

export function wrapOpenAI(OpenAIClass: any): any {
  logger.debug('[wrapOpenAI] Wrapping OpenAI class');

  // Create a wrapper class
  class WrappedOpenAI extends OpenAIClass {
    constructor(...args: any[]) {
      super(...args);

      // Wrap chat.completions.create
      if (this.chat?.completions?.create) {
        const originalCreate = this.chat.completions.create.bind(this.chat.completions);
        this.chat.completions.create = this._wrapChatCompletionsCreate(originalCreate);
      }
    }

    private _wrapChatCompletionsCreate(originalCreate: Function) {
      return async (...args: any[]) => {
        const [params] = args;
        const tracer = trace.getTracer('lilypad-openai', '0.1.0');

        logger.debug('[wrapOpenAI] Creating span for model:', params?.model);

        // Start span
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

        // Set span in context
        const contextWithSpan = trace.setSpan(context.active(), span);

        return context.with(contextWithSpan, async () => {
          try {
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
            const result = await originalCreate(...args);

            // Handle streaming
            if (params?.stream && isAsyncIterable(result)) {
              return this._wrapStream(span, result);
            }

            // Handle regular response
            this._recordResponse(span, result);

            span.setStatus({ code: SpanStatusCode.OK });
            logger.debug('[wrapOpenAI] Span completed successfully');
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

    private async *_wrapStream(span: any, stream: AsyncIterable<any>): AsyncIterable<any> {
      let content = '';
      let finishReason: string | null = null;
      let usage: any = null;

      try {
        for await (const chunk of stream) {
          // Process chunk
          if (chunk.choices?.[0]) {
            const choice = chunk.choices[0];
            if (choice.delta?.content) {
              content += choice.delta.content;
            }
            if (choice.finish_reason) {
              finishReason = choice.finish_reason;
            }
          }
          if (chunk.usage) {
            usage = chunk.usage;
          }

          yield chunk;
        }

        // Record final data
        if (content || finishReason) {
          const message: Record<string, unknown> = {
            role: 'assistant',
            content: content,
          };

          span.addEvent('gen_ai.choice', {
            'gen_ai.system': 'openai',
            index: 0,
            finish_reason: finishReason || 'error',
            message: JSON.stringify(message),
          });
        }

        if (finishReason) {
          span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, [finishReason]);
        }

        if (usage) {
          span.setAttributes({
            [SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS]: usage.prompt_tokens,
            [SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS]: usage.completion_tokens,
            'gen_ai.usage.total_tokens': usage.total_tokens,
          });
        }

        span.setStatus({ code: SpanStatusCode.OK });
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
    }

    private _recordResponse(span: any, response: any): void {
      if (!response) return;

      // Record response attributes
      if (response.choices && response.choices.length > 0) {
        response.choices.forEach((choice: any, index: number) => {
          const message: Record<string, unknown> = {
            role: choice.message?.role || 'assistant',
          };

          if (choice.message?.content) {
            message['content'] = choice.message.content;
          }

          span.addEvent('gen_ai.choice', {
            'gen_ai.system': 'openai',
            index: index,
            finish_reason: choice.finish_reason || 'error',
            message: JSON.stringify(message),
          });
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

      // Add server.address
      span.setAttribute('server.address', 'api.openai.com');
    }
  }

  return WrappedOpenAI;
}
