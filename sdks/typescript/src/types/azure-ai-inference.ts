/**
 * Type definitions for Azure AI Inference SDK
 * Based on @azure-rest/ai-inference package structure
 */

// Message types
export interface AzureInferenceMessage {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string | null;
  name?: string;
  tool_calls?: Array<{
    id: string;
    type: 'function';
    function: {
      name: string;
      arguments: string;
    };
  }>;
  tool_call_id?: string;
}

// Request parameters
export interface AzureInferenceChatCompletionParams {
  messages: AzureInferenceMessage[];
  model?: string; // Model name (e.g., "Mistral-large", "Llama-2-70b")
  temperature?: number;
  top_p?: number;
  n?: number;
  stream?: boolean;
  stop?: string | string[];
  max_tokens?: number;
  presence_penalty?: number;
  frequency_penalty?: number;
  logit_bias?: Record<string, number>;
  user?: string;
  response_format?: { type: 'text' | 'json_object' };
  seed?: number;
  tools?: Array<{
    type: 'function';
    function: {
      name: string;
      description?: string;
      parameters?: any;
    };
  }>;
  tool_choice?: 'none' | 'auto' | { type: 'function'; function: { name: string } };
}

// Response types
export interface AzureInferenceChatCompletionChoice {
  index: number;
  message: AzureInferenceMessage;
  finish_reason: 'stop' | 'length' | 'content_filter' | 'tool_calls' | null;
  logprobs?: any;
}

export interface AzureInferenceChatCompletionResponse {
  id: string;
  object: 'chat.completion';
  created: number;
  model: string; // Model name
  choices: AzureInferenceChatCompletionChoice[];
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  system_fingerprint?: string;
}

// Streaming types
export interface AzureInferenceChatCompletionChunk {
  id: string;
  object: 'chat.completion.chunk';
  created: number;
  model: string;
  choices: Array<{
    index: number;
    delta: {
      role?: 'assistant';
      content?: string | null;
      tool_calls?: Array<{
        index: number;
        id?: string;
        type?: 'function';
        function?: {
          name?: string;
          arguments?: string;
        };
      }>;
    };
    finish_reason: 'stop' | 'length' | 'content_filter' | 'tool_calls' | null;
  }>;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

// Azure AI Inference Client structure
export interface AzureInferenceClientOptions {
  endpoint: string;
  key?: string;
  apiVersion?: string;
  defaultHeaders?: Record<string, string>;
}

// ChatCompletionsClient interface
export interface ChatCompletionsClientLike {
  complete(
    params: AzureInferenceChatCompletionParams,
    options?: { abortSignal?: AbortSignal },
  ): Promise<AzureInferenceChatCompletionResponse>;

  // Some clients may have a separate method for streaming
  streamComplete?(
    params: AzureInferenceChatCompletionParams,
    options?: { abortSignal?: AbortSignal },
  ): AsyncIterable<AzureInferenceChatCompletionChunk>;

  // Get model info (used in Python SDK)
  getModelInfo?(): Promise<{ model_name?: string }> | { model_name?: string };
}

// Type guards
export function isAzureInferenceCompletionResponse(
  value: unknown,
): value is AzureInferenceChatCompletionResponse {
  return (
    typeof value === 'object' &&
    value !== null &&
    'choices' in value &&
    Array.isArray((value as AzureInferenceChatCompletionResponse).choices)
  );
}

export function isAzureInferenceCompletionChunk(
  value: unknown,
): value is AzureInferenceChatCompletionChunk {
  return (
    typeof value === 'object' &&
    value !== null &&
    'object' in value &&
    (value as AzureInferenceChatCompletionChunk).object === 'chat.completion.chunk'
  );
}
