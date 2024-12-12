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
 * CommonCallParams
 * Common parameters shared across LLM providers.
 *
 * Note: Each provider may handle these parameters differently or not support them at all.
 * Please check provider-specific documentation for parameter support and behavior.
 *
 * Attributes:
 *     temperature: Controls randomness in the output (0.0 to 1.0).
 *     max_tokens: Maximum number of tokens to generate.
 *     top_p: Nucleus sampling parameter (0.0 to 1.0).
 *     frequency_penalty: Penalizes frequent tokens (-2.0 to 2.0).
 *     presence_penalty: Penalizes tokens based on presence (-2.0 to 2.0).
 *     seed: Random seed for reproducibility.
 *     stop: Stop sequence(s) to end generation.
 */
export interface CommonCallParams {
  /** Temperature */
  temperature?: number | null;
  /** Max Tokens */
  max_tokens?: number | null;
  /** Top P */
  top_p?: number | null;
  /** Frequency Penalty */
  frequency_penalty?: number | null;
  /** Presence Penalty */
  presence_penalty?: number | null;
  /** Seed */
  seed?: number | null;
  /** Stop */
  stop?: string | string[] | null;
}

/** DependencyInfo */
export interface DependencyInfo {
  /** Version */
  version: string;
  /** Extras */
  extras: string[] | null;
}

export type DeviceCodeTable = object;

/**
 * GenerationCreate
 * Generation create model.
 */
export interface GenerationCreate {
  /** Project Uuid */
  project_uuid?: string | null;
  /** Prompt Uuid */
  prompt_uuid?: string | null;
  /**
   * Name
   * @minLength 1
   */
  name: string;
  /** Signature */
  signature: string;
  /** Code */
  code: string;
  /** Hash */
  hash: string;
  /** Dependencies */
  dependencies?: Record<string, DependencyInfo>;
  /** Arg Types */
  arg_types?: Record<string, string>;
}

/**
 * GenerationPublic
 * Generation public model.
 */
export interface GenerationPublic {
  /** Project Uuid */
  project_uuid?: string | null;
  /** Prompt Uuid */
  prompt_uuid?: string | null;
  /**
   * Name
   * @minLength 1
   */
  name: string;
  /** Signature */
  signature: string;
  /** Code */
  code: string;
  /** Hash */
  hash: string;
  /** Dependencies */
  dependencies?: Record<string, DependencyInfo>;
  /** Arg Types */
  arg_types?: Record<string, string>;
  /**
   * Uuid
   * @format uuid
   */
  uuid: string;
  prompt?: PromptPublic | null;
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
   * Generations
   * @default []
   */
  generations?: GenerationPublic[];
  /**
   * Prompts
   * @default []
   */
  prompts?: PromptPublic[];
}

/**
 * PromptPublic
 * Prompt public model.
 */
export interface PromptPublic {
  /** Project Uuid */
  project_uuid?: string | null;
  /**
   * Name
   * @minLength 1
   */
  name: string;
  /** Signature */
  signature: string;
  /** Code */
  code: string;
  /** Hash */
  hash: string;
  /** Dependencies */
  dependencies?: Record<string, string>;
  /** Template */
  template: string;
  /**
   * Is Active
   * @default false
   */
  is_active?: boolean;
  /**
   * Common parameters shared across LLM providers.
   *
   * Note: Each provider may handle these parameters differently or not support them at all.
   * Please check provider-specific documentation for parameter support and behavior.
   *
   * Attributes:
   *     temperature: Controls randomness in the output (0.0 to 1.0).
   *     max_tokens: Maximum number of tokens to generate.
   *     top_p: Nucleus sampling parameter (0.0 to 1.0).
   *     frequency_penalty: Penalizes frequent tokens (-2.0 to 2.0).
   *     presence_penalty: Penalizes tokens based on presence (-2.0 to 2.0).
   *     seed: Random seed for reproducibility.
   *     stop: Stop sequence(s) to end generation.
   */
  call_params?: CommonCallParams;
  /**
   * Uuid
   * @format uuid
   */
  uuid: string;
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
  /** Signature */
  signature?: string | null;
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
  /** Generation Uuid */
  generation_uuid?: string | null;
  /** Prompt Uuid */
  prompt_uuid?: string | null;
  type?: SpanType | null;
  /** Cost */
  cost?: number | null;
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
  generation?: GenerationPublic | null;
  prompt?: PromptPublic | null;
  /** Child Spans */
  child_spans: SpanPublic[];
  /**
   * Created At
   * @format date-time
   */
  created_at: string;
}

/**
 * SpanType
 * Span type
 */
export enum SpanType {
  GENERATION = "generation",
  PROMPT = "prompt",
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
