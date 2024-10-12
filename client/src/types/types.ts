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
  call_params?: OpenAICallArgsCreate | null;
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
  call_params?: OpenAICallArgsCreate | null;
}

/**
 * FnParamsTable
 * Provider call params table
 */
export interface FnParamsTable {
  /** Llm Function Id */
  llm_function_id: number | null;
  /** Provider name enum */
  provider: Provider;
  /** Hash */
  hash: string;
  /** Model */
  model: string;
  /** Prompt Template */
  prompt_template: string;
  /** Call Params */
  call_params?: string | null;
  /** Id */
  id?: number | null;
}

/** HTTPValidationError */
export interface HTTPValidationError {
  /** Detail */
  detail?: ValidationError[];
}

/**
 * LLMFunctionBasePublic
 * LLM function base public model
 */
export interface LLMFunctionBasePublic {
  /** Project Id */
  project_id?: number;
  /** Function Name */
  function_name: string;
  /** Version Hash */
  version_hash: string;
  /** Code */
  code: string;
  /** Arg Types */
  arg_types?: string | null;
  /** Id */
  id: number;
  /** Fn Params */
  fn_params: FnParamsTable[] | null;
}

/**
 * LLMFunctionCreate
 * LLM function create model.
 */
export interface LLMFunctionCreate {
  /** Function Name */
  function_name: string;
  /** Code */
  code: string;
  /** Version Hash */
  version_hash: string;
  /** Arg Types */
  arg_types?: string | null;
}

/**
 * LLMFunctionTable
 * LLM function table
 */
export interface LLMFunctionTable {
  /** Project Id */
  project_id?: number;
  /** Function Name */
  function_name: string;
  /** Version Hash */
  version_hash: string;
  /** Code */
  code: string;
  /** Arg Types */
  arg_types?: string | null;
  /** Id */
  id?: number | null;
  /**
   * Created At
   * @format date-time
   * @default "2024-10-11T17:12:17.660788Z"
   */
  created_at?: string;
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
}

/**
 * ProjectTable
 * Project model
 */
export interface ProjectTable {
  /** Name */
  name: string;
  /** Id */
  id?: number | null;
  /**
   * Created At
   * @format date-time
   */
  created_at?: string;
}

/**
 * Provider
 * Provider name enum
 */
export enum Provider {
  OPENAI = "openai",
  ANTHROPIC = "anthropic",
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
 * SpanPublic
 * Call public model with prompt version.
 */
export interface SpanPublic {
  /** Llm Function Id */
  llm_function_id?: number | null;
  /** Instrumentation Scope name of the span */
  scope: Scope;
  /** Version */
  version?: number | null;
  /** Data */
  data: string;
  /**
   * Created At
   * @format date-time
   * @default "2024-10-11T17:12:17.666073Z"
   */
  created_at?: string;
  /** Parent Span Id */
  parent_span_id?: string | null;
  /** Id */
  id: string;
  /** Display Name */
  display_name?: string | null;
  llm_function?: LLMFunctionTable | null;
  /** Child Spans */
  child_spans: SpanPublic[];
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
  fn_params?: CallArgsPublic | null;
  /** LLM function base public model */
  llm_fn: LLMFunctionBasePublic;
}
