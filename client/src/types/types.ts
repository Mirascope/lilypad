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
 * Call args model.
 */
export interface CallArgsCreate {
  /** Model */
  model: string;
  /** Provider name enum */
  provider: Provider;
  /** Prompt Template */
  prompt_template: string;
  /** Editor State */
  editor_state: string;
  /** Call Params */
  call_params: object | null;
}

/**
 * CallArgsPublic
 * Call args model.
 */
export interface CallArgsPublic {
  /** Id */
  id: number | null;
  /** Model */
  model: string;
  /** Provider name enum */
  provider: Provider;
  /** Prompt Template */
  prompt_template: string;
  /** Editor State */
  editor_state: string;
  /** Call Params */
  call_params: object | null;
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
  /** Model */
  model: string;
  /** Prompt Template */
  prompt_template: string;
  /** Editor State */
  editor_state: string;
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
  version_hash?: string | null;
  /** Code */
  code: string;
  /** Input Arguments */
  input_arguments?: string | null;
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
  /** Input Arguments */
  input_arguments?: string | null;
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
  version_hash?: string | null;
  /** Code */
  code: string;
  /** Input Arguments */
  input_arguments?: string | null;
  /** Id */
  id?: number | null;
  /**
   * Created At
   * @format date-time
   * @default "2024-10-09T04:29:25.380066Z"
   */
  created_at?: string;
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
   * @default "2024-10-09T04:29:25.383832Z"
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
