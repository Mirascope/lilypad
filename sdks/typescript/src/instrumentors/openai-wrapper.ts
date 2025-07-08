// @ts-nocheck eslint-disable-line @typescript-eslint/ban-ts-comment
import { trace, SpanStatusCode, SpanKind, Span as OtelSpan } from '@opentelemetry/api';

import { logger } from '../utils/logger';
import { StreamWrapper, isAsyncIterable } from '../utils/stream-wrapper';
import { safeStringify } from '../utils/json';
import { isSDKShuttingDown } from '../shutdown';
import type {
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

// Store the original functions
let isPatched = false;

export function patchOpenAIRequire(): void {
  if (isPatched) {
    logger.debug('OpenAI require already patched');
    return;
  }

  logger.debug('Patching module system to intercept OpenAI');

  try {
    // Patch require
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const Module = require('module');
    const originalRequire = Module.prototype.require;

    Module.prototype.require = function (id: string, ...args: any[]) {
      const result = originalRequire.apply(this, [id, ...args]);

      if (id === 'openai') {
        logger.debug('OpenAI module loaded via require, wrapping it');
        return wrapOpenAIModule(result);
      }

      return result;
    };

    // Patch Module._load for both require and import
    const originalLoad = Module._load;
    Module._load = function (request: string, _parent: any, _isMain: boolean) {
      const result = originalLoad.apply(this, [request, _parent, _isMain]);

      if (request === 'openai') {
        logger.debug('OpenAI module loaded via Module._load, wrapping it');
        return wrapOpenAIModule(result);
      }

      return result;
    };

    // Try to patch dynamic import if available
    const originalDynamicImport = (globalThis as any).import;
    if (originalDynamicImport) {
      (globalThis as any).import = async function (specifier: string) {
        const result = await originalDynamicImport.call(this, specifier);

        if (specifier === 'openai' || specifier.endsWith('/openai')) {
          logger.debug('OpenAI module loaded via dynamic import, wrapping it');
          return wrapOpenAIModule(result);
        }

        return result;
      };
    }

    isPatched = true;
    logger.debug('Module patching completed');
  } catch (error) {
    logger.error('Failed to patch module system:', error);
  }
}

function wrapOpenAIModule(openaiModule: any): any {
  logger.debug('Wrapping OpenAI module');

  // Get the OpenAI class
  const OpenAIClass = openaiModule.default || openaiModule.OpenAI || openaiModule;

  // Create wrapped class
  class WrappedOpenAI extends OpenAIClass {
    constructor(config: any) {
      super(config);
      logger.debug('WrappedOpenAI instance created');

      // Wrap chat.completions.create
      if (this.chat?.completions?.create) {
        const originalCreate = this.chat.completions.create.bind(this.chat.completions);
        this.chat.completions.create = wrapChatCompletionsCreate(originalCreate);
        logger.debug('Wrapped chat.completions.create method');
      }
    }
  }

  // Create a new module object that mimics the original
  const wrappedModule: any = {};

  // Copy all properties from original module
  for (const key in openaiModule) {
    if (key === 'default' || key === 'OpenAI') {
      wrappedModule[key] = WrappedOpenAI;
    } else {
      wrappedModule[key] = openaiModule[key];
    }
  }

  // If it was a default export
  if (openaiModule.default) {
    wrappedModule.default = WrappedOpenAI;
  }

  // Add OpenAI as named export too
  wrappedModule.OpenAI = WrappedOpenAI;

  logger.debug('OpenAI module wrapping completed');
  return wrappedModule;
}

function wrapChatCompletionsCreate(original: Function): Function {
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

    logger.debug(`OpenAI wrapper: Creating span "${spanName}"`);
    logger.debug(
      `Parameters: ${JSON.stringify({ model, temperature: params?.temperature, max_tokens: params?.max_tokens })}`,
    );

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
          logger.debug('Calling original OpenAI method');
          const result = await original.apply(this, [params, options]);

          // Handle streaming response
          if (params?.stream && isAsyncIterable(result)) {
            return handleStreamingResponse(result as AsyncIterable<ChatCompletionChunk>, span);
          }

          // Handle regular response
          recordCompletionResponse(span, result);

          span.setStatus({ code: SpanStatusCode.OK });
          logger.debug(`OpenAI wrapper: Span completed successfully for ${spanName}`);
          span.end();
          return result;
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : String(error);
          span.recordException(error as Error);
          span.setAttributes({
            'gen_ai.error.type': error instanceof Error ? error.name : 'Error',
            'gen_ai.error.message': errorMessage,
          });
          span.setStatus({ code: SpanStatusCode.ERROR, message: errorMessage });
          span.end();
          throw error;
        }
      },
    );
  };
}

function recordCompletionResponse(span: OtelSpan, response: any): void {
  if (!response) return;

  // Record response attributes
  if (response.choices && response.choices.length > 0) {
    const choice = response.choices[0];

    // Record completion
    span.addEvent('gen_ai.content.completion', {
      'gen_ai.completion.role': String(choice.message?.role || 'assistant'),
      'gen_ai.completion.content': safeStringify(choice.message?.content),
      'gen_ai.completion.index': '0',
    });

    // Record finish reason
    if (choice.finish_reason) {
      span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, [choice.finish_reason]);
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
}

async function handleStreamingResponse(
  stream: AsyncIterable<ChatCompletionChunk>,
  span: OtelSpan,
): Promise<AsyncIterable<ChatCompletionChunk>> {
  const wrappedStream = new StreamWrapper(stream);
  const chunks: ChatCompletionChunk[] = [];

  wrappedStream.on('data', (chunk: ChatCompletionChunk) => {
    chunks.push(chunk);
  });

  wrappedStream.on('end', () => {
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

    // Record the completed stream
    if (content) {
      span.addEvent('gen_ai.content.completion', {
        'gen_ai.completion.role': 'assistant',
        'gen_ai.completion.content': content,
        'gen_ai.completion.index': '0',
      });
    }

    if (finishReason) {
      span.setAttribute(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS, [finishReason]);
    }

    span.setStatus({ code: SpanStatusCode.OK });
    span.end();
  });

  wrappedStream.on('error', (error: Error) => {
    span.recordException(error);
    span.setStatus({
      code: SpanStatusCode.ERROR,
      message: error.message,
    });
    span.end();
  });

  return wrappedStream;
}
