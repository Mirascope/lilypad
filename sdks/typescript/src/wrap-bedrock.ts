/**
 * Manual AWS Bedrock wrapping for environments where auto-instrumentation doesn't work
 * Supports multiple model providers (Anthropic, Amazon Titan, Meta Llama, etc.)
 */

import { trace, context, SpanKind, SpanStatusCode } from '@opentelemetry/api';
import type { Span } from '@opentelemetry/api';
import { logger } from './utils/logger';
import { ensureError } from './utils/error-handler';
import type {
  BedrockInvokeModelParams,
  BedrockRuntimeLike,
  InvokeModelFunction,
  InvokeModelStreamFunction,
  BedrockResponseStreamChunk,
  BedrockAnthropicRequest,
  BedrockAnthropicResponse,
  BedrockTitanRequest,
  BedrockTitanResponse,
  BedrockLlamaRequest,
  BedrockLlamaResponse,
} from './types/bedrock';

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

// Helper to detect model provider from model ID
function detectProvider(modelId: string): string {
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

// Helper to extract region from client config
function extractRegion(client: any): string {
  if (client.config?.region) {
    return client.config.region;
  }
  if (client._config?.region) {
    return client._config.region;
  }
  return 'unknown';
}

// Helper to parse and record request based on provider
function recordRequest(span: Span, modelId: string, body: string | Uint8Array): void {
  const provider = detectProvider(modelId);
  let requestData: any;

  try {
    // Convert body to string if it's Uint8Array
    const bodyStr = body instanceof Uint8Array ? new TextDecoder().decode(body) : body;
    requestData = JSON.parse(bodyStr);
  } catch (error) {
    logger.debug('[wrapBedrock] Failed to parse request body');
    return;
  }

  // Set common attributes
  span.setAttribute('gen_ai.bedrock.provider', provider);

  // Handle different providers
  switch (provider) {
    case 'anthropic': {
      const req = requestData as BedrockAnthropicRequest;
      span.setAttributes({
        [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: req.max_tokens,
        [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: req.temperature,
        [SEMATTRS_GEN_AI_REQUEST_TOP_P]: req.top_p,
        'gen_ai.request.top_k': req.top_k,
      });

      // Record system message
      if (req.system) {
        span.addEvent('gen_ai.system.message', {
          'gen_ai.system': 'bedrock_anthropic',
          content: req.system,
        });
      }

      // Record messages
      if (req.messages) {
        req.messages.forEach((message) => {
          const content =
            typeof message.content === 'string' ? message.content : JSON.stringify(message.content);

          span.addEvent(`gen_ai.${message.role}.message`, {
            'gen_ai.system': 'bedrock_anthropic',
            content: content,
          });
        });
      }
      break;
    }

    case 'amazon': {
      const req = requestData as BedrockTitanRequest;
      const config = req.textGenerationConfig || {};
      span.setAttributes({
        [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: config.temperature,
        [SEMATTRS_GEN_AI_REQUEST_TOP_P]: config.topP,
        [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: config.maxTokenCount,
      });

      // Record input text as user message
      if (req.inputText) {
        span.addEvent('gen_ai.user.message', {
          'gen_ai.system': 'bedrock_titan',
          content: req.inputText,
        });
      }
      break;
    }

    case 'meta': {
      const req = requestData as BedrockLlamaRequest;
      span.setAttributes({
        [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: req.max_gen_len,
        [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: req.temperature,
        [SEMATTRS_GEN_AI_REQUEST_TOP_P]: req.top_p,
      });

      // Record prompt as user message
      if (req.prompt) {
        span.addEvent('gen_ai.user.message', {
          'gen_ai.system': 'bedrock_llama',
          content: req.prompt,
        });
      }
      break;
    }
  }
}

// Helper to parse and record response based on provider
function recordResponse(span: Span, modelId: string, responseBody: Uint8Array): void {
  const provider = detectProvider(modelId);
  let responseData: any;

  try {
    const bodyStr = new TextDecoder().decode(responseBody);
    responseData = JSON.parse(bodyStr);
  } catch (error) {
    logger.debug('[wrapBedrock] Failed to parse response body');
    return;
  }

  // Handle different providers
  switch (provider) {
    case 'anthropic': {
      const resp = responseData as BedrockAnthropicResponse;

      // Record content
      if (resp.content && resp.content.length > 0) {
        resp.content.forEach((content, index) => {
          if (content.type === 'text') {
            span.addEvent('gen_ai.choice', {
              'gen_ai.system': 'bedrock_anthropic',
              index: index,
              finish_reason: resp.stop_reason || 'error',
              message: JSON.stringify({
                role: resp.role,
                content: content.text,
              }),
            });
          }
        });
      }

      // Record finish reason
      if (resp.stop_reason) {
        span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, [resp.stop_reason]);
      }

      // Record usage
      if (resp.usage) {
        span.setAttributes({
          [SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS]: resp.usage.input_tokens,
          [SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS]: resp.usage.output_tokens,
          'gen_ai.usage.total_tokens': resp.usage.input_tokens + resp.usage.output_tokens,
        });
      }

      // Record model
      if (resp.model) {
        span.setAttribute('gen_ai.response.model', resp.model);
      }
      break;
    }

    case 'amazon': {
      const resp = responseData as BedrockTitanResponse;

      // Record results
      if (resp.results && resp.results.length > 0) {
        resp.results.forEach((result, index) => {
          span.addEvent('gen_ai.choice', {
            'gen_ai.system': 'bedrock_titan',
            index: index,
            finish_reason: result.completionReason || 'error',
            message: JSON.stringify({
              role: 'assistant',
              content: result.outputText,
            }),
          });
        });

        // Record finish reasons
        const finishReasons = resp.results.map((r) => r.completionReason).filter(Boolean);
        if (finishReasons.length > 0) {
          span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, finishReasons);
        }
      }

      // Record usage
      if (resp.inputTextTokenCount && resp.results?.[0]) {
        span.setAttributes({
          [SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS]: resp.inputTextTokenCount,
          [SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS]: resp.results[0].tokenCount || 0,
          'gen_ai.usage.total_tokens': resp.inputTextTokenCount + (resp.results[0].tokenCount || 0),
        });
      }
      break;
    }

    case 'meta': {
      const resp = responseData as BedrockLlamaResponse;

      // Record generation
      if (resp.generation) {
        span.addEvent('gen_ai.choice', {
          'gen_ai.system': 'bedrock_llama',
          index: 0,
          finish_reason: resp.stop_reason || 'error',
          message: JSON.stringify({
            role: 'assistant',
            content: resp.generation,
          }),
        });
      }

      // Record finish reason
      if (resp.stop_reason) {
        span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, [resp.stop_reason]);
      }

      // Record usage
      if (resp.prompt_token_count !== undefined && resp.generation_token_count !== undefined) {
        span.setAttributes({
          [SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS]: resp.prompt_token_count,
          [SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS]: resp.generation_token_count,
          'gen_ai.usage.total_tokens': resp.prompt_token_count + resp.generation_token_count,
        });
      }
      break;
    }
  }
}

// Helper function to wrap streaming responses
async function* wrapStream(
  span: Span,
  stream: AsyncIterable<BedrockResponseStreamChunk>,
  modelId: string,
): AsyncIterable<BedrockResponseStreamChunk> {
  const provider = detectProvider(modelId);
  let accumulatedContent = '';
  let stopReason: string | null = null;
  let usage = {
    input_tokens: 0,
    output_tokens: 0,
  };

  try {
    for await (const event of stream) {
      // Check for errors
      if (
        event.internalServerException ||
        event.modelStreamErrorException ||
        event.throttlingException ||
        event.validationException
      ) {
        const errorType = event.internalServerException
          ? 'InternalServerException'
          : event.modelStreamErrorException
            ? 'ModelStreamErrorException'
            : event.throttlingException
              ? 'ThrottlingException'
              : 'ValidationException';
        throw new Error(`Bedrock ${errorType}`);
      }

      // Process chunk based on provider
      if (event.chunk?.bytes) {
        try {
          const chunkStr = new TextDecoder().decode(event.chunk.bytes);
          const chunkData = JSON.parse(chunkStr);

          // Extract content based on provider
          switch (provider) {
            case 'anthropic':
              // Handle Anthropic streaming format
              if (chunkData.type === 'content_block_delta' && chunkData.delta?.text) {
                accumulatedContent += chunkData.delta.text;
              } else if (chunkData.type === 'message_delta' && chunkData.delta?.stop_reason) {
                stopReason = chunkData.delta.stop_reason;
              } else if (chunkData.type === 'message_stop' && chunkData.usage) {
                usage = {
                  input_tokens: chunkData.usage.input_tokens || 0,
                  output_tokens: chunkData.usage.output_tokens || 0,
                };
              }
              break;

            case 'amazon':
              // Handle Titan streaming format
              if (chunkData.outputText) {
                accumulatedContent += chunkData.outputText;
              }
              if (chunkData.completionReason) {
                stopReason = chunkData.completionReason;
              }
              break;

            case 'meta':
              // Handle Llama streaming format
              if (chunkData.generation) {
                accumulatedContent += chunkData.generation;
              }
              if (chunkData.stop_reason) {
                stopReason = chunkData.stop_reason;
              }
              break;
          }
        } catch (parseError) {
          logger.debug('[wrapBedrock] Failed to parse streaming chunk');
        }
      }

      yield event;
    }

    // Record final data
    if (accumulatedContent || stopReason) {
      span.addEvent('gen_ai.choice', {
        'gen_ai.system': `bedrock_${provider}`,
        index: 0,
        finish_reason: stopReason || 'error',
        message: JSON.stringify({
          role: 'assistant',
          content: accumulatedContent,
        }),
      });
    }

    if (stopReason) {
      span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, [stopReason]);
    }

    if (usage.input_tokens > 0 || usage.output_tokens > 0) {
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

// Helper function to wrap invokeModel
function wrapInvokeModel(originalInvoke: InvokeModelFunction, client: any): InvokeModelFunction {
  return async (params: BedrockInvokeModelParams) => {
    const tracer = trace.getTracer('lilypad-bedrock', '0.1.0');
    const region = extractRegion(client);
    const provider = detectProvider(params.modelId);

    logger.debug('[wrapBedrock] Creating span for model:', params.modelId);

    // Start span
    const span = tracer.startSpan(`chat ${params.modelId}`, {
      kind: SpanKind.CLIENT,
      attributes: {
        [SEMATTRS_GEN_AI_SYSTEM]: 'bedrock',
        'server.address': `bedrock-runtime.${region}.amazonaws.com`,
        [SEMATTRS_GEN_AI_REQUEST_MODEL]: params.modelId,
        [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
        'aws.region': region,
        'gen_ai.bedrock.provider': provider,
      },
    });

    // Set span in context
    const contextWithSpan = trace.setSpan(context.active(), span);

    return context.with(contextWithSpan, async () => {
      try {
        // Record request
        recordRequest(span, params.modelId, params.body);

        // Call original
        const result = await originalInvoke(params);

        // Record response
        if (result.body) {
          recordResponse(span, params.modelId, result.body);
        }

        span.setStatus({ code: SpanStatusCode.OK });
        logger.debug('[wrapBedrock] Span completed successfully');
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

// Helper function to wrap invokeModelWithResponseStream
function wrapInvokeModelStream(
  originalInvoke: InvokeModelStreamFunction,
  client: any,
): InvokeModelStreamFunction {
  return async (params: BedrockInvokeModelParams) => {
    const tracer = trace.getTracer('lilypad-bedrock', '0.1.0');
    const region = extractRegion(client);
    const provider = detectProvider(params.modelId);

    logger.debug('[wrapBedrock] Creating streaming span for model:', params.modelId);

    // Start span
    const span = tracer.startSpan(`chat ${params.modelId}`, {
      kind: SpanKind.CLIENT,
      attributes: {
        [SEMATTRS_GEN_AI_SYSTEM]: 'bedrock',
        'server.address': `bedrock-runtime.${region}.amazonaws.com`,
        [SEMATTRS_GEN_AI_REQUEST_MODEL]: params.modelId,
        [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
        'aws.region': region,
        'gen_ai.bedrock.provider': provider,
      },
    });

    // Set span in context
    const contextWithSpan = trace.setSpan(context.active(), span);

    return context.with(contextWithSpan, async () => {
      try {
        // Record request
        recordRequest(span, params.modelId, params.body);

        // Call original
        const stream = await originalInvoke(params);

        // Wrap the stream
        return wrapStream(span, stream, params.modelId);
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
 * Wraps an AWS Bedrock Runtime client instance or class to add tracing
 * Supports multiple model providers through Bedrock
 */
export function wrapBedrock<T extends BedrockRuntimeLike>(instance: T): T;
export function wrapBedrock<T extends new (...args: any[]) => BedrockRuntimeLike>(
  constructor: T,
): T;
export function wrapBedrock<T extends object>(bedrockInstance: T): T {
  logger.debug('[wrapBedrock] Wrapping Bedrock Runtime instance');

  // Check if it's a constructor function (class)
  const isConstructor = typeof bedrockInstance === 'function';

  // Check if it's an instance (object that's not a function)
  const isInstance = typeof bedrockInstance === 'object' && bedrockInstance !== null;

  if (isInstance) {
    // Type assertion to access methods
    const instance = bedrockInstance as BedrockRuntimeLike;

    // Wrap instance methods directly
    if (instance.invokeModel) {
      const originalInvoke = instance.invokeModel.bind(instance);
      instance.invokeModel = wrapInvokeModel(originalInvoke, instance);
    }

    if (instance.invokeModelWithResponseStream) {
      const originalStream = instance.invokeModelWithResponseStream.bind(instance);
      instance.invokeModelWithResponseStream = wrapInvokeModelStream(originalStream, instance);
    }

    return bedrockInstance; // Modified in-place
  }

  if (!isConstructor) {
    // If it's neither an instance nor a constructor, just return it
    logger.debug('[wrapBedrock] Object is neither an instance nor a constructor, returning as-is');
    return bedrockInstance;
  }

  // Otherwise, assume it's a class and create a wrapper
  const BedrockClass = bedrockInstance as new (...args: any[]) => BedrockRuntimeLike;

  // Create a wrapper class
  class WrappedBedrock extends BedrockClass {
    constructor(...args: unknown[]) {
      super(...args);

      // Wrap methods
      if (this.invokeModel) {
        const originalInvoke = this.invokeModel.bind(this);
        this.invokeModel = wrapInvokeModel(originalInvoke, this);
      }

      if (this.invokeModelWithResponseStream) {
        const originalStream = this.invokeModelWithResponseStream.bind(this);
        this.invokeModelWithResponseStream = wrapInvokeModelStream(originalStream, this);
      }
    }
  }

  return WrappedBedrock as T;
}
