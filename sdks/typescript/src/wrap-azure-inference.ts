/**
 * Manual wrapping for Azure AI Inference SDK
 * Wraps the Azure AI Inference client to add tracing capabilities
 */

import { getTracerProvider } from './configure';
import { SpanKind, SpanStatusCode, context, trace } from '@opentelemetry/api';
import { isConfigured } from './utils/settings';
import { logger } from './utils/logger';
import { StreamWrapper, isAsyncIterable } from './utils/stream-wrapper';
import type {
  AzureInferenceChatCompletionParams,
  AzureInferenceChatCompletionChunk,
  ChatCompletionsClientLike,
} from './types/azure-ai-inference';

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

/**
 * Options for wrapping Azure AI Inference client
 */
export interface WrapAzureInferenceOptions {
  /**
   * Whether to capture request parameters as span attributes
   */
  captureRequestParams?: boolean;

  /**
   * Whether to capture response data as span attributes
   */
  captureResponseData?: boolean;

  /**
   * Custom span name function
   */
  spanNameFn?: (method: string, params: AzureInferenceChatCompletionParams) => string;
}

/**
 * Wraps an Azure AI Inference ChatCompletionsClient or REST client to add tracing
 */
export function wrapAzureInference<T extends object>(
  client: T,
  options: WrapAzureInferenceOptions = {},
): T {
  if (!isConfigured()) {
    logger.warn(
      '[wrapAzureInference] SDK not configured. Call configure() before wrapping Azure AI Inference client',
    );
    return client;
  }

  const provider = getTracerProvider();
  if (!provider) {
    logger.warn('[wrapAzureInference] No tracer provider available');
    return client;
  }

  const tracer = provider.getTracer('@lilypad/typescript-sdk', '0.1.0');

  // Check if this is a REST client (has path method)
  if ('path' in client && typeof (client as any).path === 'function') {
    return wrapRestClient(client, tracer, options);
  }

  // Check if this is a direct ChatCompletionsClient (has complete method)
  if ('complete' in client && typeof (client as any).complete === 'function') {
    return wrapChatCompletionsClient(client as ChatCompletionsClientLike, tracer, options) as T;
  }

  logger.warn('[wrapAzureInference] Client does not appear to be an Azure AI Inference client');
  return client;
}

/**
 * Wraps a REST client pattern
 */
function wrapRestClient<T extends object>(
  client: T,
  tracer: any,
  options: WrapAzureInferenceOptions,
): T {
  const originalPath = (client as any).path.bind(client);

  (client as any).path = (...args: any[]) => {
    const pathClient = originalPath(...args);

    if (pathClient.post) {
      const originalPost = pathClient.post.bind(pathClient);

      pathClient.post = async (postOptions?: any) => {
        const body = postOptions?.body;
        if (!body || !body.messages) {
          // Not a chat completion request
          return originalPost(postOptions);
        }

        const model = body.model || 'unknown';
        const spanName = options.spanNameFn
          ? options.spanNameFn('chat.completions', body)
          : `azure.ai.inference.chat ${model}`;

        const span = tracer.startSpan(spanName, {
          kind: SpanKind.CLIENT,
          attributes: {
            [SEMATTRS_GEN_AI_SYSTEM]: 'az_ai_inference',
            [SEMATTRS_GEN_AI_REQUEST_MODEL]: model,
            [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
            'lilypad.type': 'llm',
            ...(options.captureRequestParams && {
              [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: body.temperature,
              [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: body.max_tokens,
              [SEMATTRS_GEN_AI_REQUEST_TOP_P]: body.top_p,
            }),
          },
        });

        const contextWithSpan = trace.setSpan(context.active(), span);

        return context.with(contextWithSpan, async () => {
          try {
            // Record messages
            if (body.messages) {
              body.messages.forEach((message: any) => {
                span.addEvent(`gen_ai.${message.role}.message`, {
                  'gen_ai.system': 'az_ai_inference',
                  content:
                    typeof message.content === 'string'
                      ? message.content
                      : JSON.stringify(message.content),
                });
              });
            }

            const result = await originalPost(postOptions);

            // Handle streaming
            if (body.stream && result.asNodeStream) {
              return wrapStreamResponse(span, result, options);
            }

            // Handle regular response
            if (result.body && options.captureResponseData) {
              recordResponse(span, result.body);
            }

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

    return pathClient;
  };

  return client;
}

/**
 * Wraps a direct ChatCompletionsClient
 */
function wrapChatCompletionsClient(
  client: ChatCompletionsClientLike,
  tracer: any,
  options: WrapAzureInferenceOptions,
): ChatCompletionsClientLike {
  const wrappedClient = { ...client };

  // Wrap complete method
  if (client.complete) {
    const originalComplete = client.complete.bind(client);

    wrappedClient.complete = async (params: any, requestOptions?: any): Promise<any> => {
      let model = params.model;
      if (!model && client.getModelInfo) {
        const modelInfo = await client.getModelInfo();
        model = modelInfo?.model_name || 'unknown';
      }

      const spanName = options.spanNameFn
        ? options.spanNameFn('complete', params)
        : `azure.ai.inference.chat ${model}`;

      const span = tracer.startSpan(spanName, {
        kind: SpanKind.CLIENT,
        attributes: {
          [SEMATTRS_GEN_AI_SYSTEM]: 'az_ai_inference',
          [SEMATTRS_GEN_AI_REQUEST_MODEL]: model,
          [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
          'lilypad.type': 'llm',
          ...(options.captureRequestParams && {
            [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: params.temperature,
            [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: params.max_tokens,
            [SEMATTRS_GEN_AI_REQUEST_TOP_P]: params.top_p,
          }),
        },
      });

      const contextWithSpan = trace.setSpan(context.active(), span);

      return context.with(contextWithSpan, async () => {
        try {
          // Record messages
          if (params.messages) {
            params.messages.forEach((message: any) => {
              span.addEvent(`gen_ai.${message.role}.message`, {
                'gen_ai.system': 'az_ai_inference',
                content:
                  typeof message.content === 'string'
                    ? message.content
                    : JSON.stringify(message.content),
              });
            });
          }

          const result = await originalComplete(params, requestOptions);

          // Handle streaming
          if (params.stream && isAsyncIterable(result)) {
            return wrapStream(
              span,
              result as AsyncIterable<AzureInferenceChatCompletionChunk>,
              options,
            );
          }

          // Handle regular response
          if (options.captureResponseData) {
            recordResponse(span, result);
          }

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

  // Wrap streamComplete method if it exists
  if (client.streamComplete) {
    const originalStreamComplete = client.streamComplete.bind(client);

    (wrappedClient as any).streamComplete = async (params: any, requestOptions?: any) => {
      let model = params.model;
      if (!model && client.getModelInfo) {
        const modelInfo = await client.getModelInfo();
        model = modelInfo?.model_name || 'unknown';
      }

      const spanName = options.spanNameFn
        ? options.spanNameFn('streamComplete', params)
        : `azure.ai.inference.chat ${model}`;

      const span = tracer.startSpan(spanName, {
        kind: SpanKind.CLIENT,
        attributes: {
          [SEMATTRS_GEN_AI_SYSTEM]: 'az_ai_inference',
          [SEMATTRS_GEN_AI_REQUEST_MODEL]: model,
          [SEMATTRS_GEN_AI_OPERATION_NAME]: 'chat',
          'lilypad.type': 'llm',
          'azure.stream': true,
          ...(options.captureRequestParams && {
            [SEMATTRS_GEN_AI_REQUEST_TEMPERATURE]: params.temperature,
            [SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS]: params.max_tokens,
            [SEMATTRS_GEN_AI_REQUEST_TOP_P]: params.top_p,
          }),
        },
      });

      const contextWithSpan = trace.setSpan(context.active(), span);

      return context.with(contextWithSpan, async () => {
        try {
          // Record messages
          if (params.messages) {
            params.messages.forEach((message: any) => {
              span.addEvent(`gen_ai.${message.role}.message`, {
                'gen_ai.system': 'az_ai_inference',
                content:
                  typeof message.content === 'string'
                    ? message.content
                    : JSON.stringify(message.content),
              });
            });
          }

          const stream = await originalStreamComplete(params, requestOptions);
          return wrapStream(span, stream, options);
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

  return wrappedClient;
}

/**
 * Wraps a streaming response from REST client
 */
function wrapStreamResponse(span: any, response: any, options: WrapAzureInferenceOptions): any {
  const originalAsNodeStream = response.asNodeStream;
  const originalBodyAsText = response.bodyAsText;

  // Override stream methods to instrument them
  response.asNodeStream = () => {
    const stream = originalAsNodeStream.call(response);
    return wrapNodeStream(span, stream, options);
  };

  // Also handle if they read as text and parse manually
  if (originalBodyAsText) {
    response.bodyAsText = async () => {
      const text = await originalBodyAsText.call(response);
      // Parse and record the response
      try {
        const parsed = JSON.parse(text);
        if (options.captureResponseData) {
          recordResponse(span, parsed);
        }
      } catch (e) {
        // Not JSON, ignore
      }
      span.setStatus({ code: SpanStatusCode.OK });
      span.end();
      return text;
    };
  }

  return response;
}

/**
 * Wraps a Node.js stream
 */
function wrapNodeStream(span: any, stream: any, options: WrapAzureInferenceOptions): any {
  let content = '';
  let finishReason: string | null = null;
  let usage: any = null;

  const onChunk = (chunk: AzureInferenceChatCompletionChunk) => {
    if (chunk.choices && chunk.choices.length > 0) {
      const choice = chunk.choices[0];
      if (choice.delta?.content) {
        content += choice.delta.content;
      }
      if (choice.finish_reason) {
        finishReason = choice.finish_reason;
      }
    }
    // Capture usage data if present
    if (chunk.usage) {
      usage = chunk.usage;
    }

    // Add chunk event
    span.addEvent('gen_ai.chunk', {
      size: chunk.choices?.[0]?.delta?.content?.length || 0,
    });
  };

  const onFinalize = () => {
    // Record the completed stream
    if (content && options.captureResponseData) {
      span.addEvent('gen_ai.choice', {
        'gen_ai.system': 'az_ai_inference',
        index: 0,
        message: JSON.stringify({ role: 'assistant', content: content }),
        finish_reason: finishReason || 'stop',
      });
    }

    if (finishReason && options.captureResponseData) {
      span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, [finishReason]);
    }

    // Record usage if available
    if (usage && options.captureResponseData) {
      span.setAttributes({
        [SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS]: usage.prompt_tokens,
        [SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS]: usage.completion_tokens,
        'gen_ai.usage.total_tokens': usage.total_tokens,
      });
    }

    span.setStatus({ code: SpanStatusCode.OK });
    span.end();
  };

  return new StreamWrapper(stream, span, { onChunk, onFinalize });
}

/**
 * Wraps an async iterable stream
 */
function wrapStream(
  span: any,
  stream: AsyncIterable<AzureInferenceChatCompletionChunk>,
  options: WrapAzureInferenceOptions,
): AsyncIterable<AzureInferenceChatCompletionChunk> {
  let content = '';
  let finishReason: string | null = null;
  let usage: any = null;

  const onChunk = (chunk: AzureInferenceChatCompletionChunk) => {
    if (chunk.choices && chunk.choices.length > 0) {
      const choice = chunk.choices[0];
      if (choice.delta?.content) {
        content += choice.delta.content;
      }
      if (choice.finish_reason) {
        finishReason = choice.finish_reason;
      }
    }
    // Capture usage data if present
    if (chunk.usage) {
      usage = chunk.usage;
    }

    // Add chunk event
    span.addEvent('gen_ai.chunk', {
      size: chunk.choices?.[0]?.delta?.content?.length || 0,
    });
  };

  const onFinalize = () => {
    // Record the completed stream
    if (content && options.captureResponseData) {
      span.addEvent('gen_ai.choice', {
        'gen_ai.system': 'az_ai_inference',
        index: 0,
        message: JSON.stringify({ role: 'assistant', content: content }),
        finish_reason: finishReason || 'stop',
      });
    }

    if (finishReason && options.captureResponseData) {
      span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, [finishReason]);
    }

    // Record usage if available
    if (usage && options.captureResponseData) {
      span.setAttributes({
        [SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS]: usage.prompt_tokens,
        [SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS]: usage.completion_tokens,
        'gen_ai.usage.total_tokens': usage.total_tokens,
      });
    }

    span.setStatus({ code: SpanStatusCode.OK });
    span.end();
  };

  return new StreamWrapper(stream, span, { onChunk, onFinalize });
}

/**
 * Records response attributes
 */
function recordResponse(span: any, response: any): void {
  if (!response) return;

  // Record response attributes
  if (response.choices && response.choices.length > 0) {
    response.choices.forEach((choice: any, index: number) => {
      if (choice.message) {
        // Match Python's event format
        span.addEvent('gen_ai.choice', {
          'gen_ai.system': 'az_ai_inference',
          index: index,
          message: JSON.stringify(choice.message),
          finish_reason: choice.finish_reason || '',
        });
      }
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
}
