/* eslint-disable */
/* tslint:disable */
/*
 * ---------------------------------------------------------------
 * ## THIS FILE WAS GENERATED VIA SWAGGER-TYPESCRIPT-API        ##
 * ##                                                           ##
 * ## AUTHOR: acacode                                           ##
 * ## SOURCE: https://github.com/acacode/swagger-typescript-api ##
 * ---------------------------------------------------------------
 */

/**
 * AnthropicCallArgsCreate
 * Anthropic call args model.
 */
export interface AnthropicCallArgsCreate {
  /** Max Tokens */
  max_tokens: number;
  /** Temperature */
  temperature: number;
  /** Stop Sequences */
  stop_sequences?: string[] | null;
  /** Top K */
  top_k?: number | null;
  /** Top P */
  top_p?: number | null;
}

/**
 * AudioPart
 * Image part model.
 */
export interface AudioPart {
  /** Type */
  type: "audio";
  /** Media Type */
  media_type: string;
  /** Audio */
  audio: string;
}

/**
 * CallArgsCreate
 * Call args create model.
 */
export interface CallArgsCreate {
  /** Model */
  model: string;
  /** Provider name enum */
  provider: Provider;
  /** Prompt Template */
  prompt_template: string;
  /** Call Params */
  call_params?: OpenAICallArgsCreate | AnthropicCallArgsCreate | GeminiCallArgsCreate | null;
}

/**
 * CallArgsPublic
 * Call args public model.
 */
export interface CallArgsPublic {
  /** Id */
  id: number | null;
  /** Model */
  model: string;
  /** Provider name enum */
  provider: Provider;
  /** Prompt Template */
  prompt_template?: string | null;
  /** Hash */
  hash?: string | null;
  /** Call Params */
  call_params?: OpenAICallArgsCreate | AnthropicCallArgsCreate | GeminiCallArgsCreate | null;
}

/**
 * FnParamsPublic
 * Fn params public model
 */
export interface FnParamsPublic {
  /** Provider name enum */
  provider: Provider;
  /** Hash */
  hash: string;
  /** Model */
  model: string;
  /** Prompt Template */
  prompt_template: string;
  /** Id */
  id: number;
  /** Llm Function Id */
  llm_function_id: number;
  /** Call Params */
  call_params?: OpenAICallArgsCreate | AnthropicCallArgsCreate | GeminiCallArgsCreate | null;
}

/**
 * FnParamsTable
 * Provider call params table
 */
export interface FnParamsTable {
  /** Provider name enum */
  provider: Provider;
  /** Hash */
  hash: string;
  /** Model */
  model: string;
  /** Prompt Template */
  prompt_template: string;
  /** Id */
  id?: number | null;
  /** Llm Function Id */
  llm_function_id: number | null;
  /** Call Params */
  call_params?: object | null;
}

/**
 * GeminiCallArgsCreate
 * Gemini GenerationConfig call args model.
 * https://ai.google.dev/api/generate-content#v1beta.GenerationConfig
 */
export interface GeminiCallArgsCreate {
  /** Response Mime Type */
  response_mime_type: string;
  /** Max Output Tokens */
  max_output_tokens?: number | null;
  /** Temperature */
  temperature?: number | null;
  /** Top K */
  top_k?: number | null;
  /** Top P */
  top_p?: number | null;
  /** Frequency Penalty */
  frequency_penalty?: number | null;
  /** Presence Penalty */
  presence_penalty?: number | null;
  /** Response Schema */
  response_schema?: object | null;
  /** Stop Sequences */
  stop_sequences?: string[] | null;
}

/** HTTPValidationError */
export interface HTTPValidationError {
  /** Detail */
  detail?: ValidationError[];
}

/**
 * ImagePart
 * Image part model.
 */
export interface ImagePart {
  /** Type */
  type: "image";
  /** Media Type */
  media_type: string;
  /** Image */
  image: string;
}

/**
 * LLMFunctionCreate
 * LLM function create model.
 */
export interface LLMFunctionCreate {
  /** Function Name */
  function_name: string;
  /** Version Hash */
  version_hash: string;
  /** Code */
  code: string;
  /** Arg Types */
  arg_types?: Record<string, string> | null;
}

/**
 * LLMFunctionPublic
 * LLM function base public model
 */
export interface LLMFunctionPublic {
  /** Function Name */
  function_name: string;
  /** Version Hash */
  version_hash: string;
  /** Code */
  code: string;
  /** Arg Types */
  arg_types?: Record<string, string> | null;
  /** Id */
  id: number;
  /** Fn Params */
  fn_params: FnParamsTable[] | null;
}

/**
 * LLMFunctionTable
 * LLM function table
 */
export interface LLMFunctionTable {
  /** Function Name */
  function_name: string;
  /** Version Hash */
  version_hash: string;
  /** Code */
  code: string;
  /** Arg Types */
  arg_types?: Record<string, string> | null;
  /** Id */
  id?: number | null;
  /** Project Id */
  project_id?: number;
  /**
   * Created At
   * @format date-time
   * @default "2024-11-09T02:06:38.010491Z"
   */
  created_at?: string;
}

/**
 * MessageParam
 * Message param model.
 */
export interface MessageParam {
  /** Content */
  content: (TextPart | ImagePart | AudioPart | ToolPart)[];
  /** Role */
  role: string;
}

/**
 * NonSyncedVersionCreate
 * Non-synced LLM function version create model.
 */
export interface NonSyncedVersionCreate {
  /** Llm Function Id */
  llm_function_id: number;
}

/**
 * OpenAICallArgsCreate
 * OpenAI call args model.
 */
export interface OpenAICallArgsCreate {
  /** Max Tokens */
  max_tokens: number;
  /** Temperature */
  temperature: number;
  /** Top P */
  top_p: number;
  /** Frequency Penalty */
  frequency_penalty: number;
  /** Presence Penalty */
  presence_penalty: number;
  /** Response format model. */
  response_format: ResponseFormat;
  /** Stop */
  stop?: string | string[] | null;
}

/**
 * ProjectCreate
 * Project create model
 */
export interface ProjectCreate {
  /** Name */
  name: string;
}

/**
 * ProjectPublic
 * Project public model
 */
export interface ProjectPublic {
  /** Name */
  name: string;
  /** Id */
  id: number;
  /**
   * Llm Fns
   * @default []
   */
  llm_fns?: LLMFunctionPublic[];
}

/**
 * Provider
 * Provider name enum
 */
export enum Provider {
  OPENAI = "openai",
  ANTHROPIC = "anthropic",
  OPENROUTER = "openrouter",
  GEMINI = "gemini",
}

/**
 * ResponseFormat
 * Response format model.
 */
export interface ResponseFormat {
  /** Type */
  type: "text" | "json_object" | "json_schema";
}

/**
 * Scope
 * Instrumentation Scope name of the span
 */
export enum Scope {
  LILYPAD = "lilypad",
  LLM = "llm",
}

/**
 * SpanMoreDetails
 * Span more details model.
 */
export interface SpanMoreDetails {
  /** Display Name */
  display_name: string;
  /** Model */
  model: string;
  /** Provider */
  provider: string;
  /** Prompt Tokens */
  prompt_tokens?: number | null;
  /** Completion Tokens */
  completion_tokens?: number | null;
  /** Duration Ms */
  duration_ms: number;
  /** Code */
  code?: string | null;
  /** Function Arguments */
  function_arguments?: object | null;
  /** Output */
  output?: string | null;
  /** Messages */
  messages: MessageParam[];
  /** Data */
  data: object;
}

/**
 * SpanPublic
 * Call public model with prompt version.
 */
export interface SpanPublic {
  /** Id */
  id: string;
  /** Project Id */
  project_id?: number | null;
  /** Version Id */
  version_id?: number | null;
  /** Instrumentation Scope name of the span */
  scope: Scope;
  /** Version */
  version?: number | null;
  /** Data */
  data?: object;
  /**
   * Created At
   * @format date-time
   * @default "2024-11-09T02:06:38.014038Z"
   */
  created_at?: string;
  /** Parent Span Id */
  parent_span_id?: string | null;
  /** Display Name */
  display_name?: string | null;
  llm_function?: LLMFunctionTable | null;
  /** Child Spans */
  child_spans: SpanPublic[];
}

/**
 * TextPart
 * Text part model.
 */
export interface TextPart {
  /** Type */
  type: "text";
  /** Text */
  text: string;
}

/**
 * ToolPart
 * Tool part model.
 */
export interface ToolPart {
  /** Type */
  type: "tool_call";
  /** Name */
  name: string;
  /** Arguments */
  arguments: object;
}

/** ValidationError */
export interface ValidationError {
  /** Location */
  loc: (string | number)[];
  /** Message */
  msg: string;
  /** Error Type */
  type: string;
}

/**
 * VersionPublic
 * Version public model
 */
export interface VersionPublic {
  /** Project Id */
  project_id?: number | null;
  /** Llm Function Id */
  llm_function_id: number;
  /** Fn Params Id */
  fn_params_id: number | null;
  /** Version */
  version: number;
  /** Function Name */
  function_name: string;
  /** Llm Function Hash */
  llm_function_hash: string;
  /** Fn Params Hash */
  fn_params_hash?: string | null;
  /**
   * Is Active
   * @default false
   */
  is_active?: boolean;
  /** Id */
  id: number;
  fn_params?: FnParamsPublic | null;
  /** LLM function base public model */
  llm_fn: LLMFunctionPublic;
  /** Spans */
  spans: SpanPublic[];
}
