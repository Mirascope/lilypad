/**
 * Basic type definitions for AWS Bedrock Runtime integration
 * These types provide minimal typing for the AWS Bedrock SDK integration
 */

// Common Bedrock types
export interface BedrockInvokeModelParams {
  modelId: string;
  contentType?: string;
  accept?: string;
  body: string | Uint8Array;
}

export interface BedrockInvokeModelResponse {
  body: Uint8Array;
  contentType?: string;
  modelId?: string;
}

export interface BedrockInvokeModelStreamParams extends BedrockInvokeModelParams {}

export interface BedrockResponseStreamChunk {
  chunk?: {
    bytes?: Uint8Array;
  };
  internalServerException?: any;
  modelStreamErrorException?: any;
  throttlingException?: any;
  validationException?: any;
}

// Model-specific request/response types

// Anthropic Claude on Bedrock
export interface BedrockAnthropicRequest {
  anthropic_version: string;
  max_tokens: number;
  messages: Array<{
    role: 'user' | 'assistant';
    content:
      | string
      | Array<{
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
  temperature?: number;
  top_p?: number;
  top_k?: number;
}

export interface BedrockAnthropicResponse {
  id: string;
  type: 'message';
  role: 'assistant';
  content: Array<{
    type: 'text';
    text: string;
  }>;
  model: string;
  stop_reason: 'end_turn' | 'max_tokens' | 'stop_sequence';
  stop_sequence: string | null;
  usage: {
    input_tokens: number;
    output_tokens: number;
  };
}

// Amazon Titan
export interface BedrockTitanRequest {
  inputText: string;
  textGenerationConfig?: {
    temperature?: number;
    topP?: number;
    maxTokenCount?: number;
    stopSequences?: string[];
  };
}

export interface BedrockTitanResponse {
  inputTextTokenCount: number;
  results: Array<{
    tokenCount: number;
    outputText: string;
    completionReason: string;
  }>;
}

// Meta Llama on Bedrock
export interface BedrockLlamaRequest {
  prompt: string;
  max_gen_len?: number;
  temperature?: number;
  top_p?: number;
}

export interface BedrockLlamaResponse {
  generation: string;
  prompt_token_count: number;
  generation_token_count: number;
  stop_reason: string;
}

// Type for invokeModel function
export type InvokeModelFunction = (
  params: BedrockInvokeModelParams,
) => Promise<BedrockInvokeModelResponse>;

// Type for invokeModelWithResponseStream function
export type InvokeModelStreamFunction = (
  params: BedrockInvokeModelStreamParams,
) => Promise<AsyncIterable<BedrockResponseStreamChunk>>;

// Interface for Bedrock Runtime Client
export interface BedrockRuntimeLike {
  invokeModel?: InvokeModelFunction;
  invokeModelWithResponseStream?: InvokeModelStreamFunction;
  config?: {
    region?: string;
    credentials?: any;
  };
}

export type BedrockModule =
  | BedrockClass
  | {
      default?: BedrockClass;
      BedrockRuntimeClient?: BedrockClass;
    };

export interface BedrockClass {
  prototype: BedrockRuntimeLike;
}
