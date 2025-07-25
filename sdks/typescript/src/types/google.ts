/**
 * Type definitions for Google Google/Generative AI
 */

// Content types
export interface GoogleTextPart {
  text: string;
}

export interface GoogleInlineDataPart {
  inline_data: {
    mime_type: string;
    data: string;
  };
}

export type GooglePart = GoogleTextPart | GoogleInlineDataPart;

export interface GoogleContent {
  role: 'user' | 'model' | 'system';
  parts: GooglePart[];
}

// Generation config
export interface GoogleGenerationConfig {
  temperature?: number;
  top_p?: number;
  top_k?: number;
  max_output_tokens?: number;
  stop_sequences?: string[];
}

// Safety settings
export interface GoogleSafetyRating {
  category: string;
  probability: string;
}

// Request types
export interface GoogleGenerateContentParams {
  contents: GoogleContent[];
  generation_config?: GoogleGenerationConfig;
  safety_settings?: any[];
}

// Response types
export interface GoogleCandidate {
  content?: GoogleContent;
  finishReason?: string;
  finish_reason?: string; // Backwards compatibility
  index?: number;
  safetyRatings?: GoogleSafetyRating[];
  safety_ratings?: GoogleSafetyRating[]; // Backwards compatibility
}

export interface GoogleUsageMetadata {
  promptTokenCount?: number;
  candidatesTokenCount?: number;
  totalTokenCount?: number;
  // Backwards compatibility
  prompt_token_count?: number;
  candidates_token_count?: number;
  total_token_count?: number;
}

export interface GoogleGenerateContentResponse {
  candidates?: GoogleCandidate[];
  usageMetadata?: GoogleUsageMetadata;
  usage_metadata?: GoogleUsageMetadata; // Backwards compatibility
  modelVersion?: string;
  responseId?: string;
}

// The actual response structure from generateContent
export interface GoogleGenerateContentResult {
  response: GoogleGenerateContentResponse;
}

// Streaming types
export interface GoogleContentChunk {
  candidates?: GoogleCandidate[];
  usageMetadata?: GoogleUsageMetadata;
  usage_metadata?: GoogleUsageMetadata; // Backwards compatibility
}

// Model interface
export interface GoogleGenerativeModel {
  generateContent(
    params: GoogleGenerateContentParams | string,
  ): Promise<GoogleGenerateContentResponse>;
  generateContentStream(
    params: GoogleGenerateContentParams | string,
  ): Promise<AsyncIterable<GoogleContentChunk>>;
  model?: string;
}

// Main Google class interface
export interface GoogleLike {
  getGenerativeModel(config: { model: string }): GoogleGenerativeModel;
}

// Function types
export type GenerateContentFunction = (
  params: GoogleGenerateContentParams | string,
  ...args: any[]
) => Promise<GoogleGenerateContentResponse>;

export type GenerateContentStreamFunction = (
  params: GoogleGenerateContentParams | string,
  ...args: any[]
) => Promise<AsyncIterable<GoogleContentChunk>>;
