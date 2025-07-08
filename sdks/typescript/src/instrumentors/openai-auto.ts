// @ts-nocheck eslint-disable-line @typescript-eslint/ban-ts-comment
import {
  InstrumentationBase,
  InstrumentationNodeModuleDefinition,
} from '@opentelemetry/instrumentation';
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

export class OpenAIAutoInstrumentation extends InstrumentationBase {
  constructor() {
    super('openai', TRACER_VERSION, {});
  }

  protected init() {
    logger.debug('OpenAIAutoInstrumentation.init() called');

    return [
      new InstrumentationNodeModuleDefinition(
        'openai',
        ['>=4.0.0'],
        (moduleExports: any) => {
          logger.debug('OpenAI module loaded, patching it');
          return this.patchOpenAIModule(moduleExports);
        },
        (moduleExports: any) => {
          logger.debug('OpenAI module unpatched');
          return moduleExports;
        },
      ),
    ];
  }

  private patchOpenAIModule(moduleExports: any): any {
    logger.debug('Patching OpenAI module exports');

    // Get the OpenAI class
    const OpenAIClass = moduleExports.default || moduleExports.OpenAI || moduleExports;

    if (!OpenAIClass) {
      logger.error('Could not find OpenAI class in module exports');
      return moduleExports;
    }

    // Save reference to this for use in wrapped class
    const instrumentation = this;

    // Create wrapped class
    class WrappedOpenAI extends OpenAIClass {
      constructor(config: any) {
        super(config);
        logger.debug('WrappedOpenAI instance created');

        // Wrap chat.completions.create
        if (this.chat?.completions?.create) {
          const originalCreate = this.chat.completions.create.bind(this.chat.completions);
          this.chat.completions.create = instrumentation.wrapChatCompletionsCreate(originalCreate);
          logger.debug('Wrapped chat.completions.create method');
        } else {
          logger.warn('chat.completions.create not found on OpenAI instance');
        }
      }
    }

    // Copy static properties and prototype
    Object.setPrototypeOf(WrappedOpenAI, OpenAIClass);
    Object.setPrototypeOf(WrappedOpenAI.prototype, OpenAIClass.prototype);

    // Copy static properties
    for (const prop in OpenAIClass) {
      if (Object.prototype.hasOwnProperty.call(OpenAIClass, prop)) {
        (WrappedOpenAI as any)[prop] = OpenAIClass[prop];
      }
    }

    // Create wrapped module exports
    const wrappedExports: any = {};

    // Copy all properties from original module
    for (const key in moduleExports) {
      if (key === 'default' || key === 'OpenAI') {
        wrappedExports[key] = WrappedOpenAI;
      } else {
        wrappedExports[key] = moduleExports[key];
      }
    }

    // If it was a default export
    if (moduleExports.default) {
      wrappedExports.default = WrappedOpenAI;
    }

    // Add OpenAI as named export too
    wrappedExports.OpenAI = WrappedOpenAI;

    logger.debug('OpenAI module patching completed');
    return wrappedExports;
  }

  private wrapChatCompletionsCreate(original: Function): Function {
    const instrumentation = this;

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

      logger.debug(`OpenAI auto-instrumentor: Creating span "${spanName}"`);
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
              return instrumentation.handleStreamingResponse(
                result as AsyncIterable<ChatCompletionChunk>,
                span,
              );
            }

            // Handle regular response
            instrumentation.recordCompletionResponse(span, result);

            span.setStatus({ code: SpanStatusCode.OK });
            logger.debug(`OpenAI auto-instrumentor: Span completed successfully for ${spanName}`);
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

  private recordCompletionResponse(span: OtelSpan, response: any): void {
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

  private async handleStreamingResponse(
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
}
