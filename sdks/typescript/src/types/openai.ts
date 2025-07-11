/**
 * Basic type definitions for OpenAI integration
 * These types provide minimal typing for the OpenAI SDK integration
 */

export interface ChatCompletionParams {
  model: string;
  messages: Array<{
    role: 'system' | 'user' | 'assistant';
    content: string;
  }>;
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  presence_penalty?: number;
  frequency_penalty?: number;
  response_format?: {
    type: string;
  };
  seed?: number;
  stream?: boolean;
  service_tier?: string;
}

export interface ChatCompletionResponse {
  id: string;
  model: string;
  choices: Array<{
    index: number;
    message?: {
      role: string;
      content: string;
    };
    finish_reason: string;
  }>;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  service_tier?: string;
}

export interface ChatCompletionChunk {
  id: string;
  model: string;
  choices: Array<{
    index: number;
    delta?: {
      role?: string;
      content?: string;
    };
    finish_reason: string | null;
  }>;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

// Type for chat.completions.create function
export type ChatCompletionsCreateFunction = (
  params: ChatCompletionParams,
  options?: unknown
) => Promise<ChatCompletionResponse | AsyncIterable<ChatCompletionChunk>>;

// Interface for OpenAI-like instances
export interface OpenAILike {
  chat?: {
    completions?: {
      create?: ChatCompletionsCreateFunction;
    };
  };
}

export type OpenAIModule =
  | OpenAIClass
  | {
      default?: OpenAIClass;
      OpenAI?: OpenAIClass;
    };

export interface OpenAIClass {
  prototype: OpenAILike;
}
