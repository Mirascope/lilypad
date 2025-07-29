/**
 * Basic type definitions for Mistral AI integration
 * These types provide minimal typing for the Mistral SDK integration
 */

export interface MistralChatParams {
  model: string;
  messages: Array<{
    role: 'system' | 'user' | 'assistant';
    content: string;
  }>;
  temperature?: number;
  top_p?: number;
  maxTokens?: number; // Changed from max_tokens to match new SDK
  stream?: boolean;
  safe_prompt?: boolean;
  random_seed?: number;
}

export interface MistralChatResponse {
  id: string;
  object: 'chat.completion';
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: {
      role: 'assistant';
      content: string;
    };
    finish_reason: 'stop' | 'length' | 'model_length';
  }>;
  usage: {
    prompt_tokens: number;
    total_tokens: number;
    completion_tokens: number;
  };
}

export interface MistralChatStreamChunk {
  id: string;
  object: 'chat.completion.chunk';
  created: number;
  model: string;
  choices: Array<{
    index: number;
    delta: {
      role?: 'assistant';
      content?: string;
    };
    finish_reason?: 'stop' | 'length' | 'model_length' | null;
    finishReason?: 'stop' | 'length' | 'model_length' | null; // SDK uses camelCase
  }>;
  usage?: {
    prompt_tokens: number;
    promptTokens?: number;
    total_tokens: number;
    totalTokens?: number;
    completion_tokens: number;
    completionTokens?: number;
  };
}

// Wrapped stream chunk from Mistral SDK
export interface MistralStreamEvent {
  data: MistralChatStreamChunk;
}

// Type for chat function
export type ChatFunction = (params: MistralChatParams) => Promise<MistralChatResponse>;

// Type for chatStream function - SDK returns wrapped chunks
export type ChatStreamFunction = (
  params: MistralChatParams,
) => AsyncIterable<MistralStreamEvent | MistralChatStreamChunk>;

// Interface for Mistral client - updated for new SDK structure
export interface MistralLike {
  chat?: {
    complete?: ChatFunction;
    stream?: ChatStreamFunction;
  };
  // Legacy methods for backward compatibility
  chatComplete?: ChatFunction;
  chatStream?: ChatStreamFunction;
}

export type MistralModule =
  | MistralClass
  | {
      default?: MistralClass;
      MistralClient?: MistralClass;
      Mistral?: MistralClass;
    };

export interface MistralClass {
  prototype: MistralLike;
}
