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
  /** Version Num */
  version_num: number;
  /** Project Uuid */
  project_uuid?: string | null;
  /** Function Uuid */
  function_uuid?: string | null;
  /** Prompt Uuid */
  prompt_uuid?: string | null;
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
  /**
   * Uuid
   * @format uuid
   */
  uuid: string;
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

export type DeviceCodeTable = object;

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
  /** Name */
  name: string;
  /** Arg Types */
  arg_types?: Record<string, string> | null;
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
  /** Project Uuid */
  project_uuid?: string | null;
  /**
   * Name
   * @minLength 1
   */
  name: string;
  /** Arg Types */
  arg_types?: Record<string, string> | null;
  /** Hash */
  hash: string;
  /** Code */
  code: string;
  /**
   * Uuid
   * @format uuid
   */
  uuid: string;
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

/**
 * MessageParam
 * Message param model agnostic to providers.
 */
export interface MessageParam {
  /** Role */
  role: string;
  /** Content */
  content: (AudioPart | TextPart | ImagePart | ToolCall)[];
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

/**
 * OrganizationPublic
 * Organization public model
 */
export interface OrganizationPublic {
  /**
   * Name
   * @minLength 1
   */
  name: string;
  /**
   * Uuid
   * @format uuid
   */
  uuid: string;
}

/**
 * ProjectCreate
 * Project Create Model.
 */
export interface ProjectCreate {
  /** Name */
  name: string;
}

/**
 * ProjectPublic
 * Project Public Model.
 */
export interface ProjectPublic {
  /** Name */
  name: string;
  /**
   * Uuid
   * @format uuid
   */
  uuid: string;
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
  /** Project Uuid */
  project_uuid?: string | null;
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
  /** Project Uuid */
  project_uuid?: string | null;
  /** Hash */
  hash?: string | null;
  /** Template */
  template: string;
  /** Provider name enum */
  provider: Provider;
  /** Model */
  model: string;
  /**
   * Uuid
   * @format uuid
   */
  uuid: string;
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

/** SettingsPublic */
export interface SettingsPublic {
  /** Remote Base Url */
  remote_base_url: string;
  /** Github Client Id */
  github_client_id: string;
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
  /** Cost */
  cost?: number | null;
}

/**
 * SpanPublic
 * Span public model
 */
export interface SpanPublic {
  /** Span Id */
  span_id: string;
  /** Project Uuid */
  project_uuid?: string | null;
  /** Version Uuid */
  version_uuid?: string | null;
  /** Cost */
  cost?: number | null;
  /** Version Num */
  version_num?: number | null;
  /** Instrumentation Scope name of the span */
  scope: Scope;
  /** Data */
  data?: object;
  /** Parent Span Id */
  parent_span_id?: string | null;
  /**
   * Uuid
   * @format uuid
   */
  uuid: string;
  /** Display Name */
  display_name?: string | null;
  version?: VersionPublic | null;
  /** Child Spans */
  child_spans: SpanPublic[];
  /**
   * Created At
   * @format date-time
   */
  created_at: string;
}

/**
 * UserOrganizationPublic
 * UserOrganization public model
 */
export interface UserOrganizationPublic {
  /** User role enum. */
  role: UserRole;
  /**
   * User Uuid
   * @format uuid
   */
  user_uuid: string;
  /**
   * Uuid
   * @format uuid
   */
  uuid: string;
  /**
   * Organization Uuid
   * @format uuid
   */
  organization_uuid: string;
  /** Organization public model */
  organization: OrganizationPublic;
}

/**
 * UserPublic
 * User public model
 */
export interface UserPublic {
  /**
   * First Name
   * @minLength 1
   */
  first_name: string;
  /** Last Name */
  last_name?: string | null;
  /**
   * Email
   * @minLength 1
   */
  email: string;
  /** Active Organization Uuid */
  active_organization_uuid?: string | null;
  /**
   * Uuid
   * @format uuid
   */
  uuid: string;
  /** Access Token */
  access_token?: string | null;
  /** User Organizations */
  user_organizations?: UserOrganizationPublic[] | null;
}

/**
 * UserRole
 * User role enum.
 */
export enum UserRole {
  ADMIN = "admin",
  MEMBER = "member",
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
  /** Version Num */
  version_num: number;
  /** Project Uuid */
  project_uuid?: string | null;
  /** Function Uuid */
  function_uuid?: string | null;
  /** Prompt Uuid */
  prompt_uuid?: string | null;
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
  /**
   * Uuid
   * @format uuid
   */
  uuid: string;
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

/**
 * _ToolCall
 * Image part model.
 */
export interface ToolCall {
  /** Type */
  type: "tool_call";
  /** Name */
  name: string;
  /** Arguments */
  arguments: object;
}
