/**
 * Manual Anthropic wrapping for environments where auto-instrumentation doesn't work
 * (e.g., Bun, Deno)
 */

import { trace, context, SpanKind, SpanStatusCode } from '@opentelemetry/api';
import type { Span } from '@opentelemetry/api';
import { logger } from './utils/logger';
import { isAsyncIterable } from './utils/stream-wrapper';
import { ensureError } from './utils/error-handler';
import type {
  AnthropicMessageParams,
  AnthropicMessageResponse,
  AnthropicLike,
  MessagesCreateFunction,
  AnthropicMessageChunk,
} from './types/anthropic';

// Type guard for AnthropicMessageResponse
function isMessageResponse(value: unknown): value is AnthropicMessageResponse {
  return (
    typeof value === 'object' &&
    value !== null &&
    'type' in value &&
    (value as AnthropicMessageResponse).type === 'message' &&
    'content' in value &&
    Array.isArray((value as AnthropicMessageResponse).content)
  );
}

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

// Helper function to record response data
function recordResponse(span: Span, response: AnthropicMessageResponse): void {
  if (!response) return;

  // Record response attributes
  if (response.content && response.content.length > 0) {
    response.content.forEach((content, index) => {
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

  // Record model
  if (response.model) {
    span.setAttribute('gen_ai.response.model', response.model);
  }

  // Record ID
  if (response.id) {
    span.setAttribute('gen_ai.response.id', response.id);
  }

  // Add server.address
  span.setAttribute('server.address', 'api.anthropic.com');
}

// Helper function to wrap streaming responses
async function* wrapStream<T extends AnthropicMessageChunk>(
  span: Span,
  stream: AsyncIterable<T>,
): AsyncIterable<T> {
  let content = '';
  let stopReason: string | null = null;
  const usage: { input_tokens: number; output_tokens: number } = {
    input_tokens: 0,
    output_tokens: 0,
  };

  try {
    for await (const chunk of stream) {
      // Skip null/undefined chunks
      if (!chunk) continue;

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

      yield chunk;
    }

    // Record final data
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

    if (usage) {
      span.setAttributes({
        [SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS]: usage.input_tokens,
        [SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS]: usage.output_tokens,
        'gen_ai.usage.total_tokens': usage.input_tokens + usage.output_tokens,
      });
    }

    span.setStatus({ code: SpanStatusCode.OK });
  } catch (error) {
    const err = ensureError(error);
    span.recordException(err);
    span.setStatus({
      code: SpanStatusCode.ERROR,
      message: err.message,
    });
    throw err;
  } finally {
    span.end();
  }
}

// Helper function to wrap messages.create
function wrapMessagesCreate(originalCreate: MessagesCreateFunction): MessagesCreateFunction {
  return async (params: AnthropicMessageParams, ...restArgs: unknown[]) => {
    const tracer = trace.getTracer('lilypad-anthropic', '0.1.0');

    logger.debug('[wrapAnthropic] Creating span for model:', params?.model);

    // Start span
    const span = tracer.startSpan(`chat ${params?.model || 'unknown'}`, {
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
    });

    // Set span in context
    const contextWithSpan = trace.setSpan(context.active(), span);

    return context.with(contextWithSpan, async () => {
      try {
        // Record system message if present
        if (params?.system) {
          span.addEvent('gen_ai.system.message', {
            'gen_ai.system': 'anthropic',
            content: params.system,
          });
        }

        // Record messages
        if (params?.messages) {
          params.messages.forEach((message) => {
            const content =
              typeof message.content === 'string'
                ? message.content
                : JSON.stringify(message.content);

            span.addEvent(`gen_ai.${message.role}.message`, {
              'gen_ai.system': 'anthropic',
              content: content,
            });
          });
        }

        // Call original
        const result = await originalCreate(params, ...restArgs);

        // Handle streaming
        if (params?.stream && isAsyncIterable(result)) {
          // Type guard ensures result is AsyncIterable
          return wrapStream(span, result as AsyncIterable<AnthropicMessageChunk>);
        }

        // Handle regular response
        if (isMessageResponse(result)) {
          recordResponse(span, result);
        }

        span.setStatus({ code: SpanStatusCode.OK });
        logger.debug('[wrapAnthropic] Span completed successfully');
        return result;
      } catch (error) {
        const err = ensureError(error);
        span.recordException(err);
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: err.message,
        });
        throw err;
      } finally {
        if (!params?.stream) {
          span.end();
        }
      }
    });
  };
}

/**
 * Wraps an Anthropic instance or class to add tracing
 */
export function wrapAnthropic<T extends AnthropicLike>(instance: T): T;
export function wrapAnthropic<T extends new (...args: any[]) => AnthropicLike>(constructor: T): T;
export function wrapAnthropic<T extends object>(anthropicInstance: T): T {
  logger.debug('[wrapAnthropic] Wrapping Anthropic instance');

  // Check if it's a constructor function (class)
  const isConstructor = typeof anthropicInstance === 'function';

  // Check if it's an instance (object that's not a function)
  const isInstance = typeof anthropicInstance === 'object' && anthropicInstance !== null;

  if (isInstance) {
    // Type assertion to access messages property
    const instance = anthropicInstance as AnthropicLike;
    // Wrap instance methods directly
    if (instance.messages?.create) {
      const originalCreate = instance.messages.create.bind(instance.messages);
      instance.messages.create = wrapMessagesCreate(originalCreate);
    }
    return anthropicInstance; // Modified in-place
  }

  if (!isConstructor) {
    // If it's neither an instance nor a constructor, just return it
    logger.debug(
      '[wrapAnthropic] Object is neither an instance nor a constructor, returning as-is',
    );
    return anthropicInstance;
  }

  // Otherwise, assume it's a class and create a wrapper
  const AnthropicClass = anthropicInstance as new (...args: any[]) => AnthropicLike;

  // Create a wrapper class
  class WrappedAnthropic extends AnthropicClass {
    constructor(...args: unknown[]) {
      super(...args);

      // Wrap messages.create
      if (this.messages?.create) {
        const originalCreate = this.messages.create.bind(this.messages);
        this.messages.create = wrapMessagesCreate(originalCreate);
      }
    }
  }

  return WrappedAnthropic as T;
}
