/**
 * Manual Google Gemini wrapping for environments where auto-instrumentation doesn't work
 * (e.g., Bun, Deno)
 */

import { trace, context, SpanKind, SpanStatusCode } from '@opentelemetry/api';
import type { Span } from '@opentelemetry/api';
import { logger } from './utils/logger';
import { ensureError } from './utils/error-handler';
import type {
  GeminiGenerateContentParams,
  GeminiGenerateContentResponse,
  GeminiLike,
  GenerativeModel,
  GenerateContentFunction,
  GenerateContentStreamFunction,
  GeminiGenerateContentStreamChunk,
} from './types/gemini';

// Type guard for GeminiGenerateContentResponse
function isGenerateContentResponse(value: unknown): value is GeminiGenerateContentResponse {
  return (
    typeof value === 'object' &&
    value !== null &&
    'candidates' in value &&
    Array.isArray((value as GeminiGenerateContentResponse).candidates)
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

// Helper function to normalize params
function normalizeParams(
  params: GeminiGenerateContentParams | string,
): GeminiGenerateContentParams {
  if (typeof params === 'string') {
    return {
      contents: [
        {
          role: 'user',
          parts: [{ text: params }],
        },
      ],
    };
  }
  return params;
}

// Helper function to record response data
function recordResponse(span: Span, response: GeminiGenerateContentResponse): void {
  if (!response) return;

  // Record response attributes
  if (response.candidates && response.candidates.length > 0) {
    response.candidates.forEach((candidate, index) => {
      const content = candidate.content.parts.map((part) => part.text).join('');

      const message: Record<string, unknown> = {
        role: candidate.content.role || 'model',
        content: content,
      };

      span.addEvent('gen_ai.choice', {
        'gen_ai.system': 'gemini',
        index: index,
        finish_reason: candidate.finish_reason || 'error',
        message: JSON.stringify(message),
      });
    });

    // Record finish reasons
    const finishReasons = response.candidates
      .map((c) => c.finish_reason)
      .filter((reason): reason is NonNullable<typeof reason> => Boolean(reason));
    if (finishReasons.length > 0) {
      span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, finishReasons);
    }
  }

  // Record usage
  if (response.usage_metadata) {
    span.setAttributes({
      [SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS]: response.usage_metadata.prompt_token_count,
      [SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS]: response.usage_metadata.candidates_token_count,
      'gen_ai.usage.total_tokens': response.usage_metadata.total_token_count,
    });
  }

  // Add server.address
  span.setAttribute('server.address', 'generativelanguage.googleapis.com');
}

// Helper function to wrap streaming responses
async function* wrapStream(
  span: Span,
  streamPromise: Promise<AsyncIterable<GeminiGenerateContentStreamChunk>>,
): AsyncIterable<GeminiGenerateContentStreamChunk> {
  let content = '';
  let finishReason: string | null = null;
  let usage:
    | {
        prompt_token_count: number;
        candidates_token_count: number;
        total_token_count: number;
      }
    | undefined;

  try {
    const stream = await streamPromise;

    for await (const chunk of stream) {
      // Process chunk
      if (chunk.candidates && chunk.candidates.length > 0) {
        const candidate = chunk.candidates[0];
        if (candidate.content?.parts) {
          const chunkContent = candidate.content.parts.map((part) => part.text).join('');
          content += chunkContent;
        }
        if (candidate.finish_reason) {
          finishReason = candidate.finish_reason;
        }
      }

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
        [SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS]: usage.prompt_token_count,
        [SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS]: usage.candidates_token_count,
        'gen_ai.usage.total_tokens': usage.total_token_count,
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

// Helper function to wrap generateContent
function wrapGenerateContent(
  originalGenerate: GenerateContentFunction,
  model: string,
): GenerateContentFunction {
  return async (params: GeminiGenerateContentParams | string, ...restArgs: unknown[]) => {
    const tracer = trace.getTracer('lilypad-gemini', '0.1.0');
    const normalizedParams = normalizeParams(params);

    logger.debug('[wrapGemini] Creating span for model:', model);

    // Extract generation config
    const genConfig = normalizedParams.generation_config || {};

    // Start span
    const span = tracer.startSpan(`chat ${model}`, {
      kind: SpanKind.CLIENT,
      attributes: {
        [SEMATTRS_GEN_AI_SYSTEM]: 'gemini',
        'server.address': 'generativelanguage.googleapis.com',
        [SEMATTRS_GEN_AI_REQUEST_MODEL]: model,
        [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: genConfig.temperature,
        [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: genConfig.max_output_tokens,
        [SEMATTRS_GEN_AI_REQUEST_TOP_P]: genConfig.top_p,
        'gen_ai.request.top_k': genConfig.top_k,
        [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
      },
    });

    // Set span in context
    const contextWithSpan = trace.setSpan(context.active(), span);

    return context.with(contextWithSpan, async () => {
      try {
        // Record messages
        if (normalizedParams.contents) {
          normalizedParams.contents.forEach((content) => {
            const text = content.parts.map((part) => part.text || '[binary data]').join('');

            span.addEvent(`gen_ai.${content.role}.message`, {
              'gen_ai.system': 'gemini',
              content: text,
            });
          });
        }

        // Call original
        const result = await originalGenerate(params, ...restArgs);

        // Handle regular response
        if (isGenerateContentResponse(result)) {
          recordResponse(span, result);
        }

        span.setStatus({ code: SpanStatusCode.OK });
        logger.debug('[wrapGemini] Span completed successfully');
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
  originalGenerate: GenerateContentStreamFunction,
  model: string,
): GenerateContentStreamFunction {
  return async (params: GeminiGenerateContentParams | string, ...restArgs: unknown[]) => {
    const tracer = trace.getTracer('lilypad-gemini', '0.1.0');
    const normalizedParams = normalizeParams(params);

    logger.debug('[wrapGemini] Creating streaming span for model:', model);

    // Extract generation config
    const genConfig = normalizedParams.generation_config || {};

    // Start span
    const span = tracer.startSpan(`chat ${model}`, {
      kind: SpanKind.CLIENT,
      attributes: {
        [SEMATTRS_GEN_AI_SYSTEM]: 'gemini',
        'server.address': 'generativelanguage.googleapis.com',
        [SEMATTRS_GEN_AI_REQUEST_MODEL]: model,
        [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: genConfig.temperature,
        [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: genConfig.max_output_tokens,
        [SEMATTRS_GEN_AI_REQUEST_TOP_P]: genConfig.top_p,
        'gen_ai.request.top_k': genConfig.top_k,
        [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
      },
    });

    // Set span in context
    const contextWithSpan = trace.setSpan(context.active(), span);

    return context.with(contextWithSpan, async () => {
      try {
        // Record messages
        if (normalizedParams.contents) {
          normalizedParams.contents.forEach((content) => {
            const text = content.parts.map((part) => part.text || '[binary data]').join('');

            span.addEvent(`gen_ai.${content.role}.message`, {
              'gen_ai.system': 'gemini',
              content: text,
            });
          });
        }

        // Call original - it returns a promise
        const streamPromise = originalGenerate(params, ...restArgs);

        // Wrap the stream
        return wrapStream(span, streamPromise);
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

// Helper function to wrap GenerativeModel
function wrapGenerativeModel(model: GenerativeModel): GenerativeModel {
  const wrappedModel = Object.create(model);
  const modelName = model.model || 'unknown';

  if (model.generateContent) {
    const originalGenerate = model.generateContent.bind(model);
    wrappedModel.generateContent = wrapGenerateContent(originalGenerate, modelName);
  }

  if (model.generateContentStream) {
    const originalStream = model.generateContentStream.bind(model);
    wrappedModel.generateContentStream = wrapGenerateContentStream(originalStream, modelName);
  }

  return wrappedModel;
}

/**
 * Wraps a Google Gemini instance or class to add tracing
 */
export function wrapGemini<T extends GeminiLike>(instance: T): T;
export function wrapGemini<T extends new (...args: any[]) => GeminiLike>(constructor: T): T;
export function wrapGemini<T extends object>(geminiInstance: T): T {
  logger.debug('[wrapGemini] Wrapping Gemini instance');

  // Check if it's a constructor function (class)
  const isConstructor = typeof geminiInstance === 'function';

  // Check if it's an instance (object that's not a function)
  const isInstance = typeof geminiInstance === 'object' && geminiInstance !== null;

  if (isInstance) {
    // Type assertion to access getGenerativeModel property
    const instance = geminiInstance as GeminiLike;

    // Wrap getGenerativeModel to intercept model creation
    if (instance.getGenerativeModel) {
      const originalGetModel = instance.getGenerativeModel.bind(instance);
      instance.getGenerativeModel = (config: { model: string }) => {
        const model = originalGetModel(config);
        return wrapGenerativeModel(model);
      };
    }
    return geminiInstance; // Modified in-place
  }

  if (!isConstructor) {
    // If it's neither an instance nor a constructor, just return it
    logger.debug('[wrapGemini] Object is neither an instance nor a constructor, returning as-is');
    return geminiInstance;
  }

  // Otherwise, assume it's a class and create a wrapper
  const GeminiClass = geminiInstance as new (...args: any[]) => GeminiLike;

  // Create a wrapper class
  class WrappedGemini extends GeminiClass {
    constructor(...args: unknown[]) {
      super(...args);

      // Wrap getGenerativeModel
      if (this.getGenerativeModel) {
        const originalGetModel = this.getGenerativeModel.bind(this);
        this.getGenerativeModel = (config: { model: string }) => {
          const model = originalGetModel(config);
          return wrapGenerativeModel(model);
        };
      }
    }
  }

  return WrappedGemini as T;
}
