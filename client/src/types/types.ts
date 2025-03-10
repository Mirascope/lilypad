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
 * APIKeyCreate
 * API key create model
 */
export interface APIKeyCreate {
  /**
   * Name
   * @minLength 1
   */
  name: string;
  /**
   * Expires At
   * @format date-time
   */
  expires_at?: string;
  /**
   * Project Uuid
   * @format uuid
   */
  project_uuid: string;
  /** Key Hash */
  key_hash?: string | null;
}

/**
 * APIKeyPublic
 * API key public model
 */
export interface APIKeyPublic {
  /**
   * Name
   * @minLength 1
   */
  name: string;
  /**
   * Expires At
   * @format date-time
   */
  expires_at?: string;
  /**
   * Project Uuid
   * @format uuid
   */
  project_uuid: string;
  /**
   * Uuid
   * @format uuid
   */
  uuid: string;
  /** Key Hash */
  key_hash: string;
  /** User public model */
  user: UserPublic;
  /** Project Public Model. */
  project: ProjectPublic;
}

/**
 * AggregateMetrics
 * Aggregated metrics for spans
 */
export interface AggregateMetrics {
  /** Total Cost */
  total_cost: number;
  /** Total Input Tokens */
  total_input_tokens: number;
  /** Total Output Tokens */
  total_output_tokens: number;
  /** Average Duration Ms */
  average_duration_ms: number;
  /** Span Count */
  span_count: number;
  /** Start Date */
  start_date: string | null;
  /** End Date */
  end_date: string | null;
  /** Generation Uuid */
  generation_uuid: string | null;
}

/**
 * AnnotationTable
 * Annotation table.
 */
export interface AnnotationTable {
  /** Uuid */
  uuid?: string | null;
  /**
   * Created At
   * @format date-time
   */
  created_at?: string;
  /**
   * Organization Uuid
   * @format uuid
   */
  organization_uuid: string;
  label?: Label | null;
  /** Reasoning */
  reasoning?: string | null;
  /** @default "manual" */
  type?: EvaluationType | null;
  /** Data */
  data?: object | null;
  /** Assigned To */
  assigned_to?: string | null;
  /** Project Uuid */
  project_uuid?: string | null;
  /** Span Uuid */
  span_uuid?: string | null;
  /** Generation Uuid */
  generation_uuid?: string | null;
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

/** CreateUserOrganizationToken */
export interface CreateUserOrganizationToken {
  /** Token */
  token: string;
}

/** DependencyInfo */
export interface DependencyInfo {
  /** Version */
  version: string;
  /** Extras */
  extras: string[] | null;
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

/**
 * GenerationUpdate
 * Generation update model.
 */
export type GenerationUpdate = object;

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
 * OrganizationInviteCreate
 * OrganizationInvite create model
 */
export interface OrganizationInviteCreate {
  /**
   * Invited By
   * @format uuid
   */
  invited_by: string;
  /**
   * Email
   * @minLength 1
   */
  email: string;
  /**
   * Expires At
   * @format date-time
   */
  expires_at?: string;
  /** Token */
  token?: string | null;
  /** Resend Email Id */
  resend_email_id?: string | null;
  /** Organization Uuid */
  organization_uuid?: string | null;
}

/**
 * OrganizationInvitePublic
 * OrganizationInvite public model
 */
export interface OrganizationInvitePublic {
  /**
   * Invited By
   * @format uuid
   */
  invited_by: string;
  /**
   * Email
   * @minLength 1
   */
  email: string;
  /**
   * Expires At
   * @format date-time
   */
  expires_at?: string;
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
  /** User public model */
  user: UserPublic;
  /** Resend Email Id */
  resend_email_id: string;
  /** Invite Link */
  invite_link?: string | null;
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
 * OrganizationUpdate
 * Organization update model
 */
export interface OrganizationUpdate {
  /** Name */
  name?: string | null;
  /** License */
  license?: string | null;
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
   * Created At
   * @format date-time
   */
  created_at: string;
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
 * Scope
 * Instrumentation Scope name of the span
 */
export enum Scope {
  LILYPAD = "lilypad",
  LLM = "llm",
}

/** SettingsPublic */
export interface SettingsPublic {
  /** Remote Client Url */
  remote_client_url: string;
  /** Remote Api Url */
  remote_api_url: string;
  /** Github Client Id */
  github_client_id: string;
  /** Google Client Id */
  google_client_id: string;
  /** Environment */
  environment: string;
  /** Experimental */
  experimental: boolean;
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
 * SpanPublic
 * Span public model
 */
export interface SpanPublic {
  /** Span Id */
  span_id: string;
  /** Generation Uuid */
  generation_uuid?: string | null;
  type?: SpanType | null;
  /** Cost */
  cost?: number | null;
  /** Instrumentation Scope name of the span */
  scope: Scope;
  /** Input Tokens */
  input_tokens?: number | null;
  /** Output Tokens */
  output_tokens?: number | null;
  /** Duration Ms */
  duration_ms?: number | null;
  /** Data */
  data?: object;
  /** Parent Span Id */
  parent_span_id?: string | null;
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
  /** Display Name */
  display_name?: string | null;
  generation?: GenerationPublic | null;
  /** Annotations */
  annotations: AnnotationTable[];
  /** Child Spans */
  child_spans: SpanPublic[];
  /**
   * Created At
   * @format date-time
   */
  created_at: string;
  /** Version */
  version?: number | null;
  /** Status */
  status?: string | null;
}

/**
 * SpanType
 * Span type
 */
export enum SpanType {
  GENERATION = "generation",
  TRACE = "trace",
}

/**
 * TimeFrame
 * Timeframe for aggregation
 */
export enum TimeFrame {
  DAY = "day",
  WEEK = "week",
  MONTH = "month",
  LIFETIME = "lifetime",
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
 * UserOrganizationTable
 * UserOrganization table.
 */
export interface UserOrganizationTable {
  /** Uuid */
  uuid?: string | null;
  /**
   * Created At
   * @format date-time
   */
  created_at?: string;
  /**
   * Organization Uuid
   * @format uuid
   */
  organization_uuid: string;
  /** User role enum. */
  role: UserRole;
  /**
   * User Uuid
   * @format uuid
   */
  user_uuid: string;
}

/**
 * UserOrganizationUpdate
 * UserOrganization update model
 */
export interface UserOrganizationUpdate {
  /** User role enum. */
  role: UserRole;
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
  /** Keys */
  keys?: Record<string, string>;
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
  OWNER = "owner",
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
