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
 * ActiveVersionPublic
 * Active version public model
 */
export interface ActiveVersionPublic {
  /**
   * Created At
   * @format date-time
   */
  created_at?: string;
  /** Version Num */
  version_num: number;
  /** Project Id */
  project_id?: number | null;
  /** Function Id */
  function_id?: number | null;
  /** Prompt Id */
  prompt_id?: number | null;
  /** Function Name */
  function_name: string;
  /** Function Hash */
  function_hash: string;
  /** Prompt Hash */
  prompt_hash?: string | null;
  /**
   * Is Active
   * @default false
   */
  is_active?: boolean;
  /** Id */
  id: number;
  /** Function public model. */
  function: FunctionPublic;
  /** Prompt public model. */
  prompt: PromptPublic;
  /** Spans */
  spans: SpanPublic[];
}

/**
 * AnthropicCallParams
 * Anthropic call args model.
 */
export interface AnthropicCallParams {
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
 * FunctionAndPromptVersionCreate
 * Function version (with prompt) create model.
 */
export interface FunctionAndPromptVersionCreate {
  /** Function create model. */
  function_create: FunctionCreate;
  /** Prompt create model. */
  prompt_create: PromptCreate;
}

/**
 * FunctionCreate
 * Function create model.
 */
export interface FunctionCreate {
  /**
   * Created At
   * @format date-time
   */
  created_at?: string;
  /** Project Id */
  project_id?: number | null;
  /**
   * Name
   * @minLength 1
   */
  name: string;
  /** Arg Types */
  arg_types?: Record<string, string> | null;
  /** Id */
  id?: number | null;
  /** Hash */
  hash?: string | null;
  /** Code */
  code?: string | null;
}

/**
 * FunctionPublic
 * Function public model.
 */
export interface FunctionPublic {
  /**
   * Created At
   * @format date-time
   */
  created_at?: string;
  /** Project Id */
  project_id?: number | null;
  /**
   * Name
   * @minLength 1
   */
  name: string;
  /** Arg Types */
  arg_types?: Record<string, string> | null;
  /** Id */
  id: number;
  /** Hash */
  hash: string;
  /** Code */
  code: string;
}

/**
 * GeminiCallParams
 * Gemini GenerationConfig call args model.
 *
 * https://ai.google.dev/api/generate-content#v1beta.GenerationConfig
 */
export interface GeminiCallParams {
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

/** LoginResponse */
export interface LoginResponse {
  /** Authorization Url */
  authorization_url: string;
  /** Device Code */
  device_code: string | null;
}

/**
 * LoginType
 * Login type enum
 */
export enum LoginType {
  GIT_HUB_O_AUTH = "GitHubOAuth",
  GOOGLE_O_AUTH = "GoogleOAuth",
}

/**
 * MessageParam
 * Message param model agnostic to providers.
 */
export interface MessageParam {
  /** Role */
  role: string;
  /** Content */
  content: (AudioPart | TextPart | ImagePart)[];
}

/**
 * OpenAICallParams
 * OpenAI call args model.
 *
 * https://platform.openai.com/docs/api-reference/chat/create
 */
export interface OpenAICallParams {
  /** Max Tokens */
  max_tokens: number;
  /** Temperature */
  temperature: number;
  /** Top P */
  top_p: number;
  /** Frequency Penalty */
  frequency_penalty?: number | null;
  /** Presence Penalty */
  presence_penalty?: number | null;
  /** Response format model. */
  response_format: ResponseFormat;
  /** Stop */
  stop?: string | string[] | null;
}

/** Organization */
export interface Organization {
  /** Id */
  id: string;
  /** Object */
  object: "organization";
  /** Name */
  name: string;
  /** Domains */
  domains: OrganizationDomain[];
  /** Created At */
  created_at: string;
  /** Updated At */
  updated_at: string;
  /** Allow Profiles Outside Organization */
  allow_profiles_outside_organization: boolean;
  /** Lookup Key */
  lookup_key?: string | null;
}

/** OrganizationDomain */
export interface OrganizationDomain {
  /** Id */
  id: string;
  /** Organization Id */
  organization_id: string;
  /** Object */
  object: "organization_domain";
  /** Domain */
  domain: string;
  /** State */
  state?: "failed" | "pending" | "legacy_verified" | "verified" | null;
  /** Verification Strategy */
  verification_strategy?: "manual" | "dns" | null;
  /** Verification Token */
  verification_token?: string | null;
}

/**
 * ProjectCreate
 * Project Create Model.
 */
export interface ProjectCreate {
  /**
   * Created At
   * @format date-time
   */
  created_at?: string;
  /** Name */
  name: string;
}

/**
 * ProjectPublic
 * Project Public Model.
 */
export interface ProjectPublic {
  /**
   * Created At
   * @format date-time
   */
  created_at?: string;
  /** Name */
  name: string;
  /** Id */
  id: number;
  /**
   * Functions
   * @default []
   */
  functions?: FunctionPublic[];
  /**
   * Prompts
   * @default []
   */
  prompts?: PromptPublic[];
  /**
   * Versions
   * @default []
   */
  versions?: VersionPublic[];
}

/**
 * PromptCreate
 * Prompt create model.
 */
export interface PromptCreate {
  /**
   * Created At
   * @format date-time
   */
  created_at?: string;
  /** Project Id */
  project_id?: number | null;
  /** Hash */
  hash?: string | null;
  /** Template */
  template: string;
  /** Provider name enum */
  provider: Provider;
  /** Model */
  model: string;
  /** Call Params */
  call_params?: OpenAICallParams | AnthropicCallParams | GeminiCallParams | null;
}

/**
 * PromptPublic
 * Prompt public model.
 */
export interface PromptPublic {
  /**
   * Created At
   * @format date-time
   */
  created_at?: string;
  /** Project Id */
  project_id?: number | null;
  /** Hash */
  hash?: string | null;
  /** Template */
  template: string;
  /** Provider name enum */
  provider: Provider;
  /** Model */
  model: string;
  /** Id */
  id: number;
  /** Call Params */
  call_params?: OpenAICallParams | AnthropicCallParams | GeminiCallParams | null;
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
  /** Provider */
  provider: string;
  /** Model */
  model: string;
  /** Input Tokens */
  input_tokens?: number | null;
  /** Output Tokens */
  output_tokens?: number | null;
  /** Duration Ms */
  duration_ms: number;
  /** Code */
  code?: string | null;
  /** Arg Values */
  arg_values?: object | null;
  /** Output */
  output?: string | null;
  /** Messages */
  messages: MessageParam[];
  /** Data */
  data: object;
}

/**
 * SpanPublic
 * Span public model
 */
export interface SpanPublic {
  /**
   * Created At
   * @format date-time
   */
  created_at?: string;
  /** Id */
  id: string;
  /** Project Id */
  project_id?: number | null;
  /** Version Id */
  version_id?: number | null;
  /** Version Num */
  version_num?: number | null;
  /** Instrumentation Scope name of the span */
  scope: Scope;
  /** Data */
  data?: object;
  /** Parent Span Id */
  parent_span_id?: string | null;
  /** Display Name */
  display_name?: string | null;
  version?: VersionPublic | null;
  /** Child Spans */
  child_spans: SpanPublic[];
}

/**
 * UserSession
 * User session model
 */
export interface UserSession {
  /** First Name */
  first_name?: string | null;
  /** Raw Profile */
  raw_profile: object;
  /** Session Id */
  session_id: string;
  /** Expires At */
  expires_at: string;
  /** Access Token */
  access_token?: string | null;
  /** Organization Id */
  organization_id?: string | null;
  /** Organizations */
  organizations?: Organization[] | null;
  /** Id */
  id?: string | null;
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
  /**
   * Created At
   * @format date-time
   */
  created_at?: string;
  /** Version Num */
  version_num: number;
  /** Project Id */
  project_id?: number | null;
  /** Function Id */
  function_id?: number | null;
  /** Prompt Id */
  prompt_id?: number | null;
  /** Function Name */
  function_name: string;
  /** Function Hash */
  function_hash: string;
  /** Prompt Hash */
  prompt_hash?: string | null;
  /**
   * Is Active
   * @default false
   */
  is_active?: boolean;
  /** Id */
  id: number;
  /** Function public model. */
  function: FunctionPublic;
  prompt: PromptPublic | null;
  /** Spans */
  spans: SpanPublic[];
}

/**
 * _AudioPart
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
 * _ImagePart
 * Image part model.
 */
export interface ImagePart {
  /** Type */
  type: "image";
  /** Media Type */
  media_type: string;
  /** Image */
  image: string;
  /** Detail */
  detail: string | null;
}

/**
 * _TextPart
 * Text part model.
 */
export interface TextPart {
  /** Type */
  type: "text";
  /** Text */
  text: string;
}
