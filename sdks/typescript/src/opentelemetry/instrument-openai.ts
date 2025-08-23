import type { Attributes, Span } from '@opentelemetry/api';
import { SpanKind, SpanStatusCode } from '@opentelemetry/api';
import OpenAI from 'openai';
import { getTracer } from '../configure';
import {
  ERROR_ATTRIBUTES,
  GEN_AI_ATTRIBUTES,
  SERVER_ATTRIBUTES,
} from '../utils/attributes';
import type { StreamChunk } from '../utils/stream-wrapper';
import { StreamWrapper } from '../utils/stream-wrapper';

interface ChatCompletionParams {
  model: string;
  messages: Array<{ role: string; content: string }>;
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  presence_penalty?: number;
  frequency_penalty?: number;
  response_format?:
    | { type: string }
    | { name: string }
    | Record<string, unknown>;
  seed?: number;
  service_tier?: string;
  stream?: boolean;
}

interface ChatCompletionResponse {
  id: string;
  model: string;
  choices: Array<{
    message: { role: string; content: string };
    finish_reason: string;
  }>;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

function getRequestAttributes(
  params: ChatCompletionParams,
  client: OpenAI
): Attributes {
  const attributes: Attributes = {
    [GEN_AI_ATTRIBUTES.GEN_AI_OPERATION_NAME]: 'chat',
    [GEN_AI_ATTRIBUTES.GEN_AI_REQUEST_MODEL]: params.model,
    [GEN_AI_ATTRIBUTES.GEN_AI_SYSTEM]: 'openai',
    [SERVER_ATTRIBUTES.SERVER_ADDRESS]: 'api.openai.com',
  };

  if (params.temperature !== undefined) {
    attributes[GEN_AI_ATTRIBUTES.GEN_AI_REQUEST_TEMPERATURE] =
      params.temperature;
  }
  if (params.max_tokens !== undefined) {
    attributes[GEN_AI_ATTRIBUTES.GEN_AI_REQUEST_MAX_TOKENS] = params.max_tokens;
  }
  if (params.top_p !== undefined) {
    attributes[GEN_AI_ATTRIBUTES.GEN_AI_REQUEST_TOP_P] = params.top_p;
  }
  if (params.presence_penalty !== undefined) {
    attributes[GEN_AI_ATTRIBUTES.GEN_AI_REQUEST_PRESENCE_PENALTY] =
      params.presence_penalty;
  }
  if (params.frequency_penalty !== undefined) {
    attributes[GEN_AI_ATTRIBUTES.GEN_AI_REQUEST_FREQUENCY_PENALTY] =
      params.frequency_penalty;
  }

  const responseFormat = params.response_format;
  if (responseFormat) {
    if (
      typeof responseFormat === 'object' &&
      'type' in responseFormat &&
      responseFormat.type
    ) {
      attributes[GEN_AI_ATTRIBUTES.GEN_AI_OPENAI_REQUEST_RESPONSE_FORMAT] = (
        responseFormat as { type: string }
      ).type;
    } else if (typeof responseFormat === 'function') {
      const funcName = (responseFormat as { name: string }).name;
      if (funcName) {
        attributes[GEN_AI_ATTRIBUTES.GEN_AI_OPENAI_REQUEST_RESPONSE_FORMAT] =
          funcName;
      }
    }
  }

  if (params.seed !== undefined) {
    attributes[GEN_AI_ATTRIBUTES.GEN_AI_OPENAI_REQUEST_SEED] = params.seed;
  }

  if (params.service_tier && params.service_tier !== 'auto') {
    attributes[GEN_AI_ATTRIBUTES.GEN_AI_OPENAI_RESPONSE_SERVICE_TIER] =
      params.service_tier;
  }

  if (client.baseURL && client.baseURL.includes('openrouter')) {
    attributes[GEN_AI_ATTRIBUTES.GEN_AI_SYSTEM] = 'openrouter';
    attributes[SERVER_ATTRIBUTES.SERVER_ADDRESS] = 'openrouter.ai';
  }

  return attributes;
}

function setResponseAttributes(span: Span, response: ChatCompletionResponse) {
  if (!response) return;

  if (response.choices && response.choices.length > 0) {
    response.choices.forEach((choice, index) => {
      span.addEvent('gen_ai.choice', {
        'gen_ai.system': 'openai',
        index: index,
        finish_reason: choice.finish_reason || 'error',
        message: JSON.stringify({
          role: choice.message?.role || 'assistant',
          content: choice.message?.content || '',
        }),
      });
    });

    const finishReasons = response.choices
      .map((c) => c.finish_reason)
      .filter(Boolean);
    if (finishReasons.length > 0) {
      span.setAttribute(
        GEN_AI_ATTRIBUTES.GEN_AI_RESPONSE_FINISH_REASONS,
        finishReasons
      );
    }
  }

  if (response.usage) {
    span.setAttributes({
      [GEN_AI_ATTRIBUTES.GEN_AI_USAGE_INPUT_TOKENS]:
        response.usage.prompt_tokens,
      [GEN_AI_ATTRIBUTES.GEN_AI_USAGE_OUTPUT_TOKENS]:
        response.usage.completion_tokens,
      'gen_ai.usage.total_tokens': response.usage.total_tokens,
    });
  }

  if (response.model) {
    span.setAttribute('gen_ai.response.model', response.model);
  }

  if (response.id) {
    span.setAttribute('gen_ai.response.id', response.id);
  }
}

export function instrument_openai(client: OpenAI): void {
  if (!client || typeof client !== 'object') {
    throw new Error('Invalid client: must be an OpenAI client instance');
  }

  if (!client.chat || typeof client.chat !== 'object') {
    throw new Error('Invalid client structure: missing chat property');
  }

  if (!client.chat.completions || typeof client.chat.completions !== 'object') {
    throw new Error(
      'Invalid client structure: missing chat.completions property'
    );
  }

  if (typeof client.chat.completions.create !== 'function') {
    throw new Error(
      'Invalid client structure: chat.completions.create must be a function'
    );
  }

  const originalCreate = client.chat.completions.create;

  if ('_lilypad_instrumented' in originalCreate) {
    console.warn(
      'OpenAI client is already instrumented, skipping re-instrumentation'
    );
    return;
  }

  const instrumentedCreate = async function (
    this: unknown,
    params: ChatCompletionParams
  ) {
    if (!params || typeof params !== 'object') {
      throw new Error('Invalid parameters: must be an object');
    }

    if (!params.model || typeof params.model !== 'string') {
      throw new Error(
        'Invalid parameters: model is required and must be a string'
      );
    }

    if (!params.messages || !Array.isArray(params.messages)) {
      throw new Error('Invalid parameters: messages must be an array');
    }

    if (params.messages.length === 0) {
      throw new Error('Invalid parameters: messages array cannot be empty');
    }

    for (let i = 0; i < params.messages.length; i++) {
      const message = params.messages[i];
      if (!message || typeof message !== 'object') {
        throw new Error(`Invalid message at index ${i}: must be an object`);
      }
      if (!message.role || typeof message.role !== 'string') {
        throw new Error(
          `Invalid message at index ${i}: role is required and must be a string`
        );
      }
      if (!['system', 'user', 'assistant', 'function'].includes(message.role)) {
        throw new Error(
          `Invalid message at index ${i}: role must be one of: system, user, assistant, function`
        );
      }
      if (message.content === undefined || message.content === null) {
        throw new Error(`Invalid message at index ${i}: content is required`);
      }
    }

    const tracer = getTracer();
    const attributes = getRequestAttributes(params, client);
    const spanName = `${attributes[GEN_AI_ATTRIBUTES.GEN_AI_OPERATION_NAME]} ${attributes[GEN_AI_ATTRIBUTES.GEN_AI_REQUEST_MODEL]}`;

    return tracer.startActiveSpan(
      spanName,
      {
        kind: SpanKind.CLIENT,
        attributes,
      },
      async (span) => {
        try {
          for (const message of params.messages || []) {
            span.addEvent('gen_ai.content.prompt', {
              'gen_ai.prompt': JSON.stringify(message),
            });
          }

          const result = await originalCreate.call(this, params as any); // we should not use any, this is just for the split

          if (params.stream) {
            return new StreamWrapper(
              span,
              result as AsyncIterable<StreamChunk>
            );
          } else {
            setResponseAttributes(span, result as ChatCompletionResponse);
            span.setStatus({ code: SpanStatusCode.OK });
            span.end();
          }

          return result;
        } catch (error) {
          const errorMessage =
            error instanceof Error ? error.message : String(error);
          const errorName =
            error instanceof Error ? error.constructor.name : 'UnknownError';

          span.setStatus({
            code: SpanStatusCode.ERROR,
            message: errorMessage,
          });
          span.setAttribute(ERROR_ATTRIBUTES.ERROR_TYPE, errorName);

          span.addEvent('error', {
            'error.type': errorName,
            'error.message': errorMessage,
            'error.stack':
              error instanceof Error && error.stack
                ? error.stack
                : 'No stack trace available',
          });

          span.end();
          throw error;
        }
      }
    );
  };

  Object.defineProperty(instrumentedCreate, '_lilypad_instrumented', {
    value: true,
    writable: false,
    enumerable: false,
    configurable: false,
  });

  Object.setPrototypeOf(instrumentedCreate, originalCreate);
  for (const prop in originalCreate) {
    if (Object.prototype.hasOwnProperty.call(originalCreate, prop)) {
      (instrumentedCreate as unknown as Record<string, unknown>)[prop] = (
        originalCreate as unknown as Record<string, unknown>
      )[prop];
    }
  }

  client.chat.completions.create = instrumentedCreate as typeof originalCreate;
}
