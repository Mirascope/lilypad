/**
 * Manual Google Generative AI wrapping for environments where auto-instrumentation doesn't work
 * (e.g., Bun, Deno)
 */

import { trace, context, SpanKind, SpanStatusCode } from '@opentelemetry/api';
import type { Span } from '@opentelemetry/api';
import { logger } from './utils/logger';
import { isAsyncIterable } from './utils/stream-wrapper';
import { ensureError } from './utils/error-handler';
import type {
  GoogleGenerateContentParams,
  GoogleGenerateContentResponse,
  GoogleLike,
  GenerateContentFunction,
  GenerateContentStreamFunction,
  GoogleContentChunk,
  GoogleContent,
  GoogleGenerativeModel,
} from './types/google';

// Type guard for GoogleGenerateContentResponse
function isGenerateContentResponse(value: unknown): value is GoogleGenerateContentResponse {
  return (
    typeof value === 'object' &&
    value !== null &&
    'candidates' in value &&
    Array.isArray((value as GoogleGenerateContentResponse).candidates)
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

// Helper function to normalize input
function normalizeInput(input: GoogleGenerateContentParams | string): GoogleGenerateContentParams {
  if (typeof input === 'string') {
    return {
      contents: [{ role: 'user', parts: [{ text: input }] }],
    };
  }
  return input;
}

// Helper function to record messages
function recordMessages(span: Span, contents: GoogleContent[]): void {
  if (!contents || !Array.isArray(contents)) return;

  contents.forEach((content) => {
    const textParts: string[] = [];
    let hasBinaryData = false;

    if (content.parts && Array.isArray(content.parts)) {
      content.parts.forEach((part) => {
        if ('text' in part && part.text) {
          textParts.push(part.text);
        } else if ('inline_data' in part) {
          hasBinaryData = true;
        }
      });
    }

    const messageContent = hasBinaryData
      ? textParts.concat('[binary data]').join('')
      : textParts.join('');

    // Map Google roles to OpenTelemetry conventions
    const eventRole = content.role === 'model' ? 'assistant' : content.role;
    span.addEvent(`gen_ai.${eventRole}.message`, {
      'gen_ai.system': 'gemini',
      content: messageContent,
    });
  });
}

// Helper function to record response data
function recordResponse(span: Span, response: GoogleGenerateContentResponse): void {
  if (!response) return;

  // Record response attributes
  const finishReasons: string[] = [];
  if (response.candidates) {
    response.candidates.forEach((candidate, index) => {
      if (candidate && candidate.content) {
        const textParts: string[] = [];
        if (candidate.content.parts && Array.isArray(candidate.content.parts)) {
          candidate.content.parts.forEach((part) => {
            if ('text' in part && part.text) {
              textParts.push(part.text);
            }
          });
        }

        const content = textParts.join('');
        if (content) {
          const message: Record<string, unknown> = {
            role: 'model',
            content: content,
          };

          span.addEvent('gen_ai.choice', {
            'gen_ai.system': 'gemini',
            index: index,
            finish_reason: candidate.finish_reason || 'stop',
            message: JSON.stringify(message),
          });
        }
      }

      if (candidate && candidate.finish_reason) {
        finishReasons.push(candidate.finish_reason);
      }
    });
  }

  // Record finish reasons
  if (finishReasons.length > 0) {
    // Filter out empty/falsy values
    const validReasons = finishReasons.filter(Boolean);
    if (validReasons.length > 0) {
      span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, validReasons);
    }
  }

  // Record usage
  if (response.usage_metadata) {
    span.setAttributes({
      [SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS]: response.usage_metadata.prompt_token_count || 0,
      [SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS]: response.usage_metadata.candidates_token_count || 0,
      'gen_ai.usage.total_tokens': response.usage_metadata.total_token_count || 0,
    });
  }

  // Add server.address
  span.setAttribute('server.address', 'generativelanguage.googleapis.com');
}

// Helper function to wrap streaming responses
async function* wrapStream<T extends GoogleContentChunk>(
  span: Span,
  stream: AsyncIterable<T>,
): AsyncIterable<T> {
  let content = '';
  let finishReason: string | null = null;
  let usage: any = null;

  try {
    for await (const chunk of stream) {
      // Skip null/undefined chunks
      if (!chunk) continue;

      // Process chunk
      if (chunk.candidates && chunk.candidates.length > 0) {
        chunk.candidates.forEach((candidate) => {
          if (candidate && candidate.content?.parts) {
            candidate.content.parts.forEach((part) => {
              if ('text' in part && part.text) {
                content += part.text;
              }
            });
          }
          if (candidate && candidate.finish_reason) {
            finishReason = candidate.finish_reason;
          }
        });
      }

      // Capture usage data if present
      if (chunk.usage_metadata) {
        usage = chunk.usage_metadata;
      }

      yield chunk;
    }

    // Record final data
    if (content || finishReason) {
      const message: Record<string, unknown> = {
        role: 'model',
        content: content,
      };

      span.addEvent('gen_ai.choice', {
        'gen_ai.system': 'gemini',
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
        [SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS]: usage.prompt_token_count || 0,
        [SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS]: usage.candidates_token_count || 0,
        'gen_ai.usage.total_tokens': usage.total_token_count || 0,
      });
    }

    span.setAttribute('server.address', 'generativelanguage.googleapis.com');
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

// Helper function to wrap generateContent
function wrapGenerateContent(
  originalGenerateContent: GenerateContentFunction,
  modelName?: string,
): GenerateContentFunction {
  return async function wrappedGenerateContent(
    this: any,
    input: GoogleGenerateContentParams | string,
    ...restArgs: unknown[]
  ) {
    const tracer = trace.getTracer('lilypad-google', '0.1.0');
    const params = normalizeInput(input);

    logger.debug('[wrapGoogle] Creating span for model:', modelName);

    // Start span
    const span = tracer.startSpan(`chat ${modelName || 'unknown'}`, {
      kind: SpanKind.CLIENT,
      attributes: {
        [SEMATTRS_GEN_AI_SYSTEM]: 'gemini',
        'server.address': 'generativelanguage.googleapis.com',
        [SEMATTRS_GEN_AI_REQUEST_MODEL]: modelName,
        [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: params.generation_config?.temperature,
        [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: params.generation_config?.max_output_tokens,
        [SEMATTRS_GEN_AI_REQUEST_TOP_P]: params.generation_config?.top_p,
        'gen_ai.request.top_k': params.generation_config?.top_k,
        [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
      },
    });

    // Set span in context
    const contextWithSpan = trace.setSpan(context.active(), span);

    return context.with(contextWithSpan, async () => {
      try {
        // Record messages
        recordMessages(span, params.contents);

        // Call original
        const result = await originalGenerateContent.call(this, input, ...restArgs);

        // Handle response
        if (isGenerateContentResponse(result)) {
          recordResponse(span, result);
        }

        span.setStatus({ code: SpanStatusCode.OK });
        logger.debug('[wrapGoogle] Span completed successfully');
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

// Helper function to wrap generateContentStream
function wrapGenerateContentStream(
  originalGenerateContentStream: GenerateContentStreamFunction,
  modelName?: string,
): GenerateContentStreamFunction {
  return async function wrappedGenerateContentStream(
    this: any,
    input: GoogleGenerateContentParams | string,
    ...restArgs: unknown[]
  ) {
    const tracer = trace.getTracer('lilypad-google', '0.1.0');
    const params = normalizeInput(input);

    logger.debug('[wrapGoogle] Creating stream span for model:', modelName);

    // Start span
    const span = tracer.startSpan(`chat ${modelName || 'unknown'}`, {
      kind: SpanKind.CLIENT,
      attributes: {
        [SEMATTRS_GEN_AI_SYSTEM]: 'gemini',
        'server.address': 'generativelanguage.googleapis.com',
        [SEMATTRS_GEN_AI_REQUEST_MODEL]: modelName,
        [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: params.generation_config?.temperature,
        [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: params.generation_config?.max_output_tokens,
        [SEMATTRS_GEN_AI_REQUEST_TOP_P]: params.generation_config?.top_p,
        'gen_ai.request.top_k': params.generation_config?.top_k,
        [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
        'gen_ai.request.stream': true,
      },
    });

    // Set span in context
    const contextWithSpan = trace.setSpan(context.active(), span);

    return context.with(contextWithSpan, async () => {
      try {
        // Record messages
        recordMessages(span, params.contents);

        // Call original
        const result = await originalGenerateContentStream.call(this, input, ...restArgs);

        // Handle streaming
        if (isAsyncIterable(result)) {
          return wrapStream(span, result as AsyncIterable<GoogleContentChunk>);
        }

        // If not a stream, just return it
        span.setStatus({ code: SpanStatusCode.OK });
        span.end();
        return result;
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

// Helper function to wrap a GenerativeModel instance
function wrapGenerativeModel(
  model: GoogleGenerativeModel,
  modelName?: string,
): GoogleGenerativeModel {
  if (model.generateContent) {
    const originalGenerateContent = model.generateContent.bind(model);
    model.generateContent = wrapGenerateContent(originalGenerateContent, modelName);
  }

  if (model.generateContentStream) {
    const originalGenerateContentStream = model.generateContentStream.bind(model);
    model.generateContentStream = wrapGenerateContentStream(
      originalGenerateContentStream,
      modelName,
    );
  }

  return model;
}

/**
 * Wraps a Google instance or class to add tracing
 */
export function wrapGoogle<T extends GoogleLike>(instance: T): T;
export function wrapGoogle<T extends new (...args: any[]) => GoogleLike>(constructor: T): T;
export function wrapGoogle<T extends object>(googleInstance: T): T {
  logger.debug('[wrapGoogle] Wrapping Google instance');

  // Check if it's a constructor function (class)
  const isConstructor = typeof googleInstance === 'function';

  // Check if it's an instance (object that's not a function)
  const isInstance = typeof googleInstance === 'object' && googleInstance !== null;

  if (isInstance) {
    // Type assertion to access getGenerativeModel property
    const instance = googleInstance as GoogleLike;
    // Wrap instance methods directly
    if (instance.getGenerativeModel) {
      const originalGetGenerativeModel = instance.getGenerativeModel.bind(instance);
      instance.getGenerativeModel = (config: { model: string }) => {
        const model = originalGetGenerativeModel(config);
        return wrapGenerativeModel(model, config.model);
      };
    }
    return googleInstance; // Modified in-place
  }

  if (!isConstructor) {
    // If it's neither an instance nor a constructor, just return it
    logger.debug('[wrapGoogle] Object is neither an instance nor a constructor, returning as-is');
    return googleInstance;
  }

  // Otherwise, assume it's a class and create a wrapper
  const GoogleClass = googleInstance as new (...args: any[]) => GoogleLike;

  // Create a wrapper class
  class WrappedGoogle extends GoogleClass {
    constructor(...args: unknown[]) {
      super(...args);

      // Wrap getGenerativeModel
      if (this.getGenerativeModel) {
        const originalGetGenerativeModel = this.getGenerativeModel.bind(this);
        this.getGenerativeModel = (config: { model: string }) => {
          const model = originalGetGenerativeModel(config);
          return wrapGenerativeModel(model, config.model);
        };
      }
    }
  }

  return WrappedGoogle as T;
}
