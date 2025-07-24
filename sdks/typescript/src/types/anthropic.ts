/**
 * Basic type definitions for Anthropic integration
 * These types provide minimal typing for the Anthropic SDK integration
 */

export interface AnthropicMessageParams {
  model: string;
  messages: Array<{
    role: 'user' | 'assistant';
    content: string | Array<{
      type: 'text' | 'image';
      text?: string;
      source?: {
        type: 'base64';
        media_type: string;
        data: string;
      };
    }>;
  }>;
  system?: string;
  max_tokens: number;
  temperature?: number;
  top_p?: number;
  top_k?: number;
  stream?: boolean;
  metadata?: {
    user_id?: string;
  };
}

export interface AnthropicMessageResponse {
  id: string;
  type: 'message';
  role: 'assistant';
  content: Array<{
    type: 'text';
    text: string;
  }>;
  model: string;
  stop_reason: 'end_turn' | 'max_tokens' | 'stop_sequence' | 'tool_use';
  stop_sequence: string | null;
  usage: {
    input_tokens: number;
    output_tokens: number;
  };
}

export interface AnthropicMessageChunk {
  type: 'message_start' | 'content_block_start' | 'content_block_delta' | 'content_block_stop' | 'message_delta' | 'message_stop';
  message?: {
    id: string;
    type: 'message';
    role: 'assistant';
    content: Array<any>;
    model: string;
    stop_reason: null;
    stop_sequence: null;
    usage: {
      input_tokens: number;
      output_tokens: number;
    };
  };
  index?: number;
  content_block?: {
    type: 'text';
    text: string;
  };
  delta?: {
    type: 'text_delta';
    text: string;
    stop_reason?: 'end_turn' | 'max_tokens' | 'stop_sequence' | 'tool_use';
    stop_sequence?: string | null;
  };
  usage?: {
    output_tokens: number;
  };
}

// Type for messages.create function
export type MessagesCreateFunction = (
  params: AnthropicMessageParams,
  options?: unknown,
) => Promise<AnthropicMessageResponse | AsyncIterable<AnthropicMessageChunk>>;

// Interface for Anthropic-like instances
export interface AnthropicLike {
  messages?: {
    create?: MessagesCreateFunction;
  };
}

export type AnthropicModule =
  | AnthropicClass
  | {
      default?: AnthropicClass;
      Anthropic?: AnthropicClass;
    };

export interface AnthropicClass {
  prototype: AnthropicLike;
}