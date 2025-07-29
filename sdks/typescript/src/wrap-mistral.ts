/**
 * Manual Mistral AI wrapping for environments where auto-instrumentation doesn't work
 * (e.g., Bun, Deno)
 */

import { trace, context, SpanKind, SpanStatusCode } from '@opentelemetry/api';
import type { Span } from '@opentelemetry/api';
import { logger } from './utils/logger';
import { ensureError } from './utils/error-handler';
import type {
  MistralChatParams,
  MistralChatResponse,
  MistralLike,
  ChatFunction,
  ChatStreamFunction,
} from './types/mistral';

// Type guard for MistralChatResponse
function isChatResponse(value: unknown): value is MistralChatResponse {
  return (
    typeof value === 'object' &&
    value !== null &&
    'choices' in value &&
    Array.isArray((value as MistralChatResponse).choices)
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
function recordResponse(span: Span, response: MistralChatResponse): void {
  if (!response) return;

  // Record response attributes
  if (response.choices && response.choices.length > 0) {
    response.choices.forEach((choice, index) => {
      const message: Record<string, unknown> = {
        role: choice.message?.role || 'assistant',
        content: choice.message?.content || '',
      };

      span.addEvent('gen_ai.choice', {
        'gen_ai.system': 'mistral',
        index: index,
        finish_reason: choice.finish_reason || 'error',
        message: JSON.stringify(message),
      });
    });

    // Record finish reasons
    const finishReasons = response.choices
      .map((c) => c.finish_reason)
      .filter((reason) => Boolean(reason)) as string[];
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
  span.setAttribute('server.address', 'api.mistral.ai');
}

// Helper function to wrap streaming responses
async function* wrapStream(span: Span, stream: AsyncIterable<any>): AsyncIterable<any> {
  let content = '';
  let finishReason: string | null = null;
  let role: string | null = null;

  try {
    for await (const rawChunk of stream) {
      // Handle wrapped format from Mistral SDK
      const chunk = rawChunk?.data || rawChunk;

      // Process chunk
      if (
        chunk &&
        typeof chunk === 'object' &&
        'choices' in chunk &&
        Array.isArray(chunk.choices) &&
        chunk.choices[0]
      ) {
        const choice = chunk.choices[0];

        // Extract role from first chunk
        if (choice.delta?.role && !role) {
          role = choice.delta.role;
        }

        // Accumulate content
        if (choice.delta?.content) {
          content += choice.delta.content;
        }

        // Extract finish reason (handle both snake_case and camelCase)
        if (choice.finish_reason || choice.finishReason) {
          finishReason = choice.finish_reason || choice.finishReason;
        }
      }

      yield rawChunk; // Yield the original chunk format
    }

    // Record final data
    if (content || finishReason) {
      const message: Record<string, unknown> = {
        role: role || 'assistant',
        content: content,
      };

      span.addEvent('gen_ai.choice', {
        'gen_ai.system': 'mistral',
        index: 0,
        finish_reason: finishReason || 'error',
        message: JSON.stringify(message),
      });
    }

    if (finishReason) {
      span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, [finishReason]);
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

// Helper function to wrap chat
function wrapChat(originalChat: ChatFunction): ChatFunction {
  return async (params: MistralChatParams) => {
    const tracer = trace.getTracer('lilypad-mistral', '0.1.0');

    logger.debug('[wrapMistral] Creating span for model:', params?.model);

    // Start span
    const span = tracer.startSpan(`chat ${params?.model || 'unknown'}`, {
      kind: SpanKind.CLIENT,
      attributes: {
        [SEMATTRS_GEN_AI_SYSTEM]: 'mistral',
        'server.address': 'api.mistral.ai',
        [SEMATTRS_GEN_AI_REQUEST_MODEL]: params?.model,
        [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: params?.temperature,
        [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: params?.maxTokens,
        [SEMATTRS_GEN_AI_REQUEST_TOP_P]: params?.top_p,
        [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
        'lilypad.type': 'llm',
        'gen_ai.request.safe_prompt': params?.safe_prompt,
        'gen_ai.request.random_seed': params?.random_seed,
      },
    });

    // Set span in context
    const contextWithSpan = trace.setSpan(context.active(), span);

    return context.with(contextWithSpan, async () => {
      try {
        // Record messages
        if (params?.messages) {
          params.messages.forEach((message) => {
            span.addEvent(`gen_ai.${message.role}.message`, {
              'gen_ai.system': 'mistral',
              content: message.content,
            });
          });
        }

        // Call original
        const result = await originalChat(params);

        // Handle regular response
        if (isChatResponse(result)) {
          recordResponse(span, result);
        }

        span.setStatus({ code: SpanStatusCode.OK });
        logger.debug('[wrapMistral] Span completed successfully');
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
        span.end();
      }
    });
  };
}

// Helper function to wrap chatStream
function wrapChatStream(originalChatStream: ChatStreamFunction): ChatStreamFunction {
  return async function* (params: MistralChatParams) {
    const tracer = trace.getTracer('lilypad-mistral', '0.1.0');

    logger.debug('[wrapMistral] Creating streaming span for model:', params?.model);

    // Start span
    const span = tracer.startSpan(`chat ${params?.model || 'unknown'}`, {
      kind: SpanKind.CLIENT,
      attributes: {
        [SEMATTRS_GEN_AI_SYSTEM]: 'mistral',
        'server.address': 'api.mistral.ai',
        [SEMATTRS_GEN_AI_REQUEST_MODEL]: params?.model,
        [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: params?.temperature,
        [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: params?.maxTokens,
        [SEMATTRS_GEN_AI_REQUEST_TOP_P]: params?.top_p,
        [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
        'lilypad.type': 'llm',
        'gen_ai.request.safe_prompt': params?.safe_prompt,
        'gen_ai.request.random_seed': params?.random_seed,
      },
    });

    // Set span in context
    const contextWithSpan = trace.setSpan(context.active(), span);

    // Use yield* to properly handle the async generator within context
    yield* await context.with(contextWithSpan, async () => {
      try {
        // Record messages
        if (params?.messages) {
          params.messages.forEach((message) => {
            span.addEvent(`gen_ai.${message.role}.message`, {
              'gen_ai.system': 'mistral',
              content: message.content,
            });
          });
        }

        // Call original
        const stream = originalChatStream(params);

        // Wrap the stream
        return wrapStream(span, stream);
      } catch (error) {
        const err = ensureError(error);
        span.recordException(err);
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: err.message,
        });
        span.end();
        throw err;
      }
    });
  };
}

/**
 * Wraps a Mistral AI instance or class to add tracing
 */
export function wrapMistral<T extends MistralLike>(instance: T): T;
export function wrapMistral<T extends new (...args: any[]) => MistralLike>(constructor: T): T;
export function wrapMistral<T extends object>(mistralInstance: T): T {
  logger.debug('[wrapMistral] Wrapping Mistral instance');

  // Check if it's a constructor function (class)
  const isConstructor = typeof mistralInstance === 'function';

  // Check if it's an instance (object that's not a function)
  const isInstance = typeof mistralInstance === 'object' && mistralInstance !== null;

  if (isInstance) {
    // Type assertion to access chat methods
    const instance = mistralInstance as MistralLike;

    // Handle new SDK structure (chat.complete, chat.stream)
    if (instance.chat && typeof instance.chat === 'object') {
      logger.debug('[wrapMistral] Found chat object with nested methods');

      if (instance.chat.complete) {
        const originalComplete = instance.chat.complete.bind(instance.chat);
        instance.chat.complete = wrapChat(originalComplete);
        logger.debug('[wrapMistral] Wrapped chat.complete');
      }

      if (instance.chat.stream) {
        const originalStream = instance.chat.stream.bind(instance.chat);
        instance.chat.stream = wrapChatStream(originalStream);
        logger.debug('[wrapMistral] Wrapped chat.stream');
      }
    }

    // Legacy method names (for older SDK versions)
    if (instance.chatComplete && typeof instance.chatComplete === 'function') {
      const originalChat = instance.chatComplete.bind(instance);
      instance.chatComplete = wrapChat(originalChat);
    }

    if (instance.chatStream) {
      const originalChatStream = instance.chatStream.bind(instance);
      instance.chatStream = wrapChatStream(originalChatStream);
    }

    return mistralInstance; // Modified in-place
  }

  if (!isConstructor) {
    // If it's neither an instance nor a constructor, just return it
    logger.debug('[wrapMistral] Object is neither an instance nor a constructor, returning as-is');
    return mistralInstance;
  }

  // Otherwise, assume it's a class and create a wrapper
  const MistralClass = mistralInstance as new (...args: any[]) => MistralLike;

  // Create a wrapper class
  class WrappedMistral extends MistralClass {
    constructor(...args: unknown[]) {
      super(...args);

      // Handle new SDK structure (chat.complete, chat.stream)
      if (this.chat && typeof this.chat === 'object') {
        if (this.chat.complete) {
          const originalComplete = this.chat.complete.bind(this.chat);
          this.chat.complete = wrapChat(originalComplete);
        }

        if (this.chat.stream) {
          const originalStream = this.chat.stream.bind(this.chat);
          this.chat.stream = wrapChatStream(originalStream);
        }
      }

      // Legacy method names (for older SDK versions)
      if (this.chatComplete && typeof this.chatComplete === 'function') {
        const originalChat = this.chatComplete.bind(this);
        this.chatComplete = wrapChat(originalChat);
      }

      // Wrap chatStream method
      if (this.chatStream) {
        const originalChatStream = this.chatStream.bind(this);
        this.chatStream = wrapChatStream(originalChatStream);
      }
    }
  }

  return WrappedMistral as T;
}
