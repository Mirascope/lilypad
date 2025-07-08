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

// Track original methods
const originalMethods = new WeakMap<any, any>();

export function instrumentOpenAI(): void {
  logger.debug('Starting OpenAI instrumentation');

  try {
    // Hook into require to patch OpenAI when it's loaded
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const Module = require('module');
    const originalRequire = Module.prototype.require;

    logger.debug('Patching Module.prototype.require');

    Module.prototype.require = function (id: string, ...args: any[]) {
      logger.debug(`require called for: ${id}`);
      const module = originalRequire.apply(this, [id, ...args]);

      if (id === 'openai') {
        logger.debug('OpenAI module detected in require, patching it');
        return patchOpenAIModule(module);
      }

      return module;
    };

    // Also try to patch if OpenAI is already loaded
    try {
      const openai = originalRequire('openai');
      if (openai) {
        logger.debug('OpenAI already loaded, patching it now');
        const patched = patchOpenAIModule(openai);
        // Replace the cached module
        require.cache[require.resolve('openai')].exports = patched;
      }
    } catch (e) {
      logger.debug('OpenAI not yet loaded, will patch when imported');
    }

    logger.debug('OpenAI instrumentation setup complete');
  } catch (error) {
    logger.error('Failed to instrument OpenAI:', error);
  }
}

function patchOpenAIModule(openaiModule: any): any {
  // Get the OpenAI class
  const OpenAIClass = openaiModule.default || openaiModule.OpenAI || openaiModule;

  if (!OpenAIClass || typeof OpenAIClass !== 'function') {
    logger.error('Could not find OpenAI class');
    return openaiModule;
  }

  // Create a proxy for the OpenAI constructor
  const ProxiedOpenAI = new Proxy(OpenAIClass, {
    construct(target, args) {
      logger.debug('Creating OpenAI instance');
      const instance = new target(...args);

      // Patch the instance
      patchOpenAIInstance(instance);

      return instance;
    },
  });

  // Copy static properties
  Object.setPrototypeOf(ProxiedOpenAI, OpenAIClass);
  for (const prop in OpenAIClass) {
    if (Object.prototype.hasOwnProperty.call(OpenAIClass, prop)) {
      ProxiedOpenAI[prop] = OpenAIClass[prop];
    }
  }

  // Return the module with the proxied class
  if (openaiModule.default) {
    return { ...openaiModule, default: ProxiedOpenAI, OpenAI: ProxiedOpenAI };
  } else {
    return ProxiedOpenAI;
  }
}

function patchOpenAIInstance(instance: any): void {
  logger.debug('Patching OpenAI instance');

  // Navigate to chat.completions.create
  if (instance.chat?.completions?.create) {
    const original = instance.chat.completions.create;
    originalMethods.set(instance.chat.completions, original);

    instance.chat.completions.create = wrapChatCompletionsCreate(
      original.bind(instance.chat.completions),
    );
    logger.debug('Patched chat.completions.create');
  } else {
    logger.warn('Could not find chat.completions.create on OpenAI instance');
  }
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

    logger.debug(`OpenAI auto-trace: Creating span "${spanName}"`);

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
          logger.debug(`OpenAI auto-trace: Span completed successfully`);
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
