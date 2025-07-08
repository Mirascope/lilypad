import {
  trace,
  SpanStatusCode,
  SpanKind,
  Span as OtelSpan,
  Attributes,
  AttributeValue,
} from '@opentelemetry/api';
import { logger } from '../utils/logger';
import { StreamWrapper, isAsyncIterable } from '../utils/stream-wrapper';
import { safeStringify } from '../utils/json';
import { isSDKShuttingDown } from '../shutdown';
import type { ChatCompletionChunk } from '../types/openai';

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

export async function instrumentOpenAICall(original: Function, args: any[]): Promise<any> {
  // Skip instrumentation if SDK is shutting down
  if (isSDKShuttingDown()) {
    return original(...args);
  }

  const [params, _options] = args;

  // Get tracer - this will return a no-op tracer if SDK is not configured
  const tracer = trace.getTracer(TRACER_NAME, TRACER_VERSION);
  const model = params?.model || 'unknown';
  const spanName = `openai.chat.completions ${model}`;

  logger.debug(`[OpenAI Instrumentation] Creating span "${spanName}"`);

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
        'lilypad.type': 'function',
      }),
    },
    async (span) => {
      try {
        // Record messages - match Python SDK format
        if (params?.messages) {
          params.messages.forEach((message: any) => {
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

        // Call original method
        logger.debug('[OpenAI Instrumentation] Calling original OpenAI method');
        const result = await original(...args);

        // Handle streaming response
        if (params?.stream && isAsyncIterable(result)) {
          return handleStreamingResponse(result as AsyncIterable<ChatCompletionChunk>, span);
        }

        // Handle regular response
        recordCompletionResponse(span, result);

        span.setStatus({ code: SpanStatusCode.OK });
        logger.debug(`[OpenAI Instrumentation] Span completed successfully`);
        return result;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        span.recordException(error as Error);
        span.setAttributes({
          'gen_ai.error.type': error instanceof Error ? error.name : 'Error',
          'gen_ai.error.message': errorMessage,
        });
        span.setStatus({ code: SpanStatusCode.ERROR, message: errorMessage });
        throw error;
      } finally {
        span.end();
      }
    },
  );
}

function recordCompletionResponse(span: OtelSpan, response: any): void {
  if (!response) return;

  // Record response attributes - match Python SDK format
  if (response.choices && response.choices.length > 0) {
    response.choices.forEach((choice: any, index: number) => {
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

async function handleStreamingResponse(
  stream: AsyncIterable<ChatCompletionChunk>,
  span: OtelSpan,
): Promise<AsyncIterable<ChatCompletionChunk>> {
  const chunks: ChatCompletionChunk[] = [];

  return new StreamWrapper(stream, span, {
    onChunk: (chunk) => {
      chunks.push(chunk);
    },
    onFinalize: () => {
      // Reconstruct the full response from chunks
      let content = '';
      let finishReason: string | null = null;

      for (const chunk of chunks) {
        if (chunk.choices && chunk.choices.length > 0) {
          const delta = chunk.choices[0].delta;
          if (delta?.content) {
            content += delta.content;
          }
          if (chunk.choices[0].finish_reason) {
            finishReason = chunk.choices[0].finish_reason;
          }
        }
      }

      // Record the completed stream - match Python SDK format
      if (content || finishReason) {
        const message: Record<string, unknown> = {
          role: 'assistant',
          content: content,
        };

        span.addEvent('gen_ai.choice', {
          [SEMATTRS_GEN_AI_SYSTEM]: 'openai',
          index: 0,
          finish_reason: finishReason || 'error',
          message: safeStringify(message),
        });
      }

      if (finishReason) {
        span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, [finishReason]);
      }

      span.setStatus({ code: SpanStatusCode.OK });
      span.end();
    },
  });
}
