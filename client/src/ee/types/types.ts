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
 * AnnotationCreate
 * Annotation create model.
 */
export interface AnnotationCreate {
  label?: Label | null;
  /** Reasoning */
  reasoning?: string | null;
  /** @default "manual" */
  type?: EvaluationType | null;
  /** Data */
  data?: object | null;
  /** Span Uuid */
  span_uuid?: string | null;
  /** Project Uuid */
  project_uuid?: string | null;
  /** Generation Uuid */
  generation_uuid?: string | null;
  /** Assigned To */
  assigned_to?: string[] | null;
}

/**
 * AnnotationPublic
 * Annotation public model.
 */
export interface AnnotationPublic {
  label?: Label | null;
  /** Reasoning */
  reasoning?: string | null;
  /** @default "manual" */
  type?: EvaluationType | null;
  /** Data */
  data?: object | null;
  /**
   * Uuid
   * @format uuid
   */
  uuid: string;
  /**
   * Project Uuid
   * @format uuid
   */
  project_uuid: string;
  /**
   * Span Uuid
   * @format uuid
   */
  span_uuid: string;
  /**
   * Generation Uuid
   * @format uuid
   */
  generation_uuid: string;
  /** Span more details model. */
  span: SpanMoreDetails;
  /** Assigned To */
  assigned_to: string | null;
}

/**
 * AnnotationUpdate
 * Annotation update model.
 */
export interface AnnotationUpdate {
  label?: Label | null;
  /** Reasoning */
  reasoning?: string | null;
  /** @default "manual" */
  type?: EvaluationType | null;
  /** Data */
  data?: object | null;
  /** Assigned To */
  assigned_to?: string | null;
}

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

/**
 * DeploymentPublic
 * Deployment public model.
 */
export interface DeploymentPublic {
  /**
   * Environment Uuid
   * @format uuid
   */
  environment_uuid: string;
  /**
   * Generation Uuid
   * @format uuid
   */
  generation_uuid: string;
  /** Project Uuid */
  project_uuid?: string | null;
  /**
   * Is Active
   * @default true
   */
  is_active?: boolean;
  /**
   * Version Num
   * @default 1
   */
  version_num?: number;
  /** Notes */
  notes?: string | null;
  /**
   * Activated At
   * Timestamp when the deployment was activated.
   * @format date-time
   */
  activated_at?: string;
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
  generation?: GenerationPublic | null;
  environment?: EnvironmentPublic | null;
}

/**
 * EnvironmentCreate
 * Environment create model.
 */
export interface EnvironmentCreate {
  /** Name */
  name: string;
  /** Description */
  description?: string | null;
  /**
   * Project Uuid
   * @format uuid
   */
  project_uuid: string;
  /**
   * Is Default
   * @default false
   */
  is_default?: boolean;
}

/**
 * EnvironmentPublic
 * Environment public model.
 */
export interface EnvironmentPublic {
  /** Name */
  name: string;
  /** Description */
  description?: string | null;
  /**
   * Project Uuid
   * @format uuid
   */
  project_uuid: string;
  /**
   * Is Default
   * @default false
   */
  is_default?: boolean;
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
}

/**
 * EvaluationType
 * Evaluation type enum
 */
export enum EvaluationType {
  MANUAL = "manual",
  VERIFIED = "verified",
  EDITED = "edited",
}

/**
 * Event
 * Event model.
 */
export interface Event {
  /** Name */
  name: string;
  /** Type */
  type: string;
  /** Message */
  message: string;
  /**
   * Timestamp
   * @format date-time
   */
  timestamp: string;
}

/**
 * GenerationCreate
 * Generation create model.
 */
export interface GenerationCreate {
  /** Project Uuid */
  project_uuid?: string | null;
  /** Version Num */
  version_num?: number | null;
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
  /** Arg Values */
  arg_values?: object;
  /** Archived */
  archived?: string | null;
  /** Custom Id */
  custom_id?: string | null;
  /** Prompt Template */
  prompt_template?: string | null;
  /** Provider */
  provider?: string | null;
  /** Model */
  model?: string | null;
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
   * Is Default
   * @default false
   */
  is_default?: boolean | null;
  /**
   * Is Managed
   * @default false
   */
  is_managed?: boolean | null;
}

/**
 * GenerationPublic
 * Generation public model.
 */
export interface GenerationPublic {
  /** Project Uuid */
  project_uuid?: string | null;
  /** Version Num */
  version_num?: number | null;
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
  /** Arg Values */
  arg_values?: object;
  /** Archived */
  archived?: string | null;
  /** Custom Id */
  custom_id?: string | null;
  /** Prompt Template */
  prompt_template?: string | null;
  /** Provider */
  provider?: string | null;
  /** Model */
  model?: string | null;
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
   * Is Default
   * @default false
   */
  is_default?: boolean | null;
  /**
   * Is Managed
   * @default false
   */
  is_managed?: boolean | null;
  /**
   * Uuid
   * @format uuid
   */
  uuid: string;
}

/** HTTPValidationError */
export interface HTTPValidationError {
  /** Detail */
  detail?: ValidationError[];
}

/**
 * Label
 * Label enum
 */
export enum Label {
  PASS = "pass",
  FAIL = "fail",
}

/**
 * LicenseInfo
 * Pydantic model for license validation
 */
export interface LicenseInfo {
  /** Customer */
  customer: string;
  /** License Id */
  license_id: string;
  /**
   * Expires At
   * @format date-time
   */
  expires_at: string;
  /** License tier enum. */
  tier: Tier;
  /**
   * Organization Uuid
   * @format uuid
   */
  organization_uuid: string;
  /**
   * Is Expired
   * Check if the license has expired
   */
  is_expired: boolean;
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
 * PlaygroundParameters
 * Playground parameters model.
 */
export interface PlaygroundParameters {
  /** Arg Values */
  arg_values: object;
  /** Provider name enum */
  provider: Provider;
  /** Model */
  model: string;
  generation?: GenerationCreate | null;
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
 * SpanMoreDetails
 * Span more details model.
 */
export interface SpanMoreDetails {
  /**
   * Uuid
   * @format uuid
   */
  uuid: string;
  /** Project Uuid */
  project_uuid?: string | null;
  /** Generation Uuid */
  generation_uuid?: string | null;
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
  duration_ms?: number | null;
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
  /** Template */
  template?: string | null;
  /** Status */
  status?: string | null;
  /** Events */
  events?: Event[] | null;
}

/**
 * Tier
 * License tier enum.
 */
export enum Tier {
  FREE = 0,
  PRO = 1,
  TEAM = 2,
  ENTERPRISE = 3,
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
