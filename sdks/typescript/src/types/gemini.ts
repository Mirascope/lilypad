/**
 * Basic type definitions for Google Gemini integration
 * These types provide minimal typing for the Google AI SDK integration
 */

export interface GeminiContent {
  role: 'user' | 'model' | 'system';
  parts: Array<{
    text?: string;
    inline_data?: {
      mime_type: string;
      data: string;
    };
  }>;
}

export interface GeminiGenerateContentParams {
  model?: string;
  contents: GeminiContent[];
  safety_settings?: Array<{
    category: string;
    threshold: string;
  }>;
  generation_config?: {
    temperature?: number;
    top_p?: number;
    top_k?: number;
    candidate_count?: number;
    max_output_tokens?: number;
    stop_sequences?: string[];
  };
}

export interface GeminiGenerateContentResponse {
  candidates: Array<{
    content: {
      parts: Array<{
        text: string;
      }>;
      role: string;
    };
    finish_reason: 'STOP' | 'MAX_TOKENS' | 'SAFETY' | 'RECITATION' | 'OTHER';
    index: number;
    safety_ratings?: Array<{
      category: string;
      probability: string;
    }>;
  }>;
  prompt_feedback?: {
    block_reason?: string;
    safety_ratings?: Array<{
      category: string;
      probability: string;
    }>;
  };
  usage_metadata?: {
    prompt_token_count: number;
    candidates_token_count: number;
    total_token_count: number;
  };
}

export interface GeminiGenerateContentStreamChunk {
  candidates?: Array<{
    content: {
      parts: Array<{
        text: string;
      }>;
      role?: string;
    };
    finish_reason?: 'STOP' | 'MAX_TOKENS' | 'SAFETY' | 'RECITATION' | 'OTHER';
    index: number;
    safety_ratings?: Array<{
      category: string;
      probability: string;
    }>;
  }>;
  usage_metadata?: {
    prompt_token_count: number;
    candidates_token_count: number;
    total_token_count: number;
  };
}

// Type for generateContent and generateContentStream functions
export type GenerateContentFunction = (
  params: GeminiGenerateContentParams | string,
  options?: unknown,
) => Promise<GeminiGenerateContentResponse>;

export type GenerateContentStreamFunction = (
  params: GeminiGenerateContentParams | string,
  options?: unknown,
) => Promise<AsyncIterable<GeminiGenerateContentStreamChunk>>;

// Interface for GenerativeModel
export interface GenerativeModel {
  generateContent?: GenerateContentFunction;
  generateContentStream?: GenerateContentStreamFunction;
  model?: string;
}

// Interface for Gemini-like instances
export interface GeminiLike {
  getGenerativeModel?: (config: { model: string }) => GenerativeModel;
}

export type GeminiModule =
  | GeminiClass
  | {
      default?: GeminiClass;
      GoogleGenerativeAI?: GeminiClass;
    };

export interface GeminiClass {
  prototype: GeminiLike;
}