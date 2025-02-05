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
 * AnnotationCreate
 * Annotation create model.
 */
export interface AnnotationCreate {
  label?: Label | null;
  /** Reasoning */
  reasoning?: string | null;
  /** @default "manual" */
  type?: EvaluationType | null;
  /** Assigned To */
  assigned_to?: string | null;
  /** Span Uuid */
  span_uuid?: string | null;
  /** Project Uuid */
  project_uuid?: string | null;
  /** Generation Uuid */
  generation_uuid?: string | null;
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
  /** Assigned To */
  assigned_to?: string | null;
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
 * AnnotationUpdate
 * Annotation update model.
 */
export interface AnnotationUpdate {
  label?: Label | null;
  /** Reasoning */
  reasoning?: string | null;
  /** @default "manual" */
  type?: EvaluationType | null;
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

/** CreateUserOrganizationToken */
export interface CreateUserOrganizationToken {
  /** Token */
  token: string;
}

/**
 * DatasetRow
 * Dataset row model.
 */
export interface DatasetRow {
  /**
   * Uuid
   * @format uuid
   */
  uuid: string;
  /** Input */
  input: Record<string, string> | null;
  /** Output */
  output: string;
  label: Label | null;
  /** Reasoning */
  reasoning: string | null;
  type: EvaluationType | null;
}

/**
 * DatasetRowsResponse
 * Response model containing the rows from the Oxen DataFrame.
 */
export interface DatasetRowsResponse {
  /** Rows */
  rows: DatasetRow[];
  /** Next Page */
  next_page?: number | null;
}

/** DependencyInfo */
export interface DependencyInfo {
  /** Version */
  version: string;
  /** Extras */
  extras: string[] | null;
}

/**
 * DeviceCodeTable
 * Device codes table.
 */
export interface DeviceCodeTable {
  /** Uuid */
  uuid?: string | null;
  /**
   * Created At
   * @format date-time
   */
  created_at?: string;
  /**
   * Id
   * Generated device code
   */
  id: string;
  /** Token */
  token: string;
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
 * GenerationCreate
 * Generation create model.
 */
export interface GenerationCreate {
  /** Project Uuid */
  project_uuid?: string | null;
  /** Prompt Uuid */
  prompt_uuid?: string | null;
  /** Response Model Uuid */
  response_model_uuid?: string | null;
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
  /** Response Model Uuid */
  response_model_uuid?: string | null;
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
  /**
   * Uuid
   * @format uuid
   */
  uuid: string;
  prompt?: PromptPublic | null;
  response_model?: ResponseModelPublic | null;
}

/**
 * GenerationUpdate
 * Generation update model.
 */
export interface GenerationUpdate {
  /** Prompt Uuid */
  prompt_uuid?: string | null;
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
  prompt?: PromptCreate | null;
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
  /**
   * Response Models
   * @default []
   */
  response_models?: ResponseModelPublic[];
  /**
   * Created At
   * @format date-time
   */
  created_at: string;
}

/**
 * PromptCreate
 * Prompt create model.
 */
export interface PromptCreate {
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
  dependencies?: Record<string, string>;
  /** Template */
  template: string;
  /**
   * Is Default
   * @default false
   */
  is_default?: boolean;
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
  /** Arg Types */
  arg_types?: Record<string, string>;
  /** Archived */
  archived?: string | null;
}

/**
 * PromptPublic
 * Prompt public model.
 */
export interface PromptPublic {
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
  dependencies?: Record<string, string>;
  /** Template */
  template: string;
  /**
   * Is Default
   * @default false
   */
  is_default?: boolean;
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
  /** Arg Types */
  arg_types?: Record<string, string>;
  /** Archived */
  archived?: string | null;
  /**
   * Uuid
   * @format uuid
   */
  uuid: string;
}

/**
 * PromptUpdate
 * Prompt update model
 */
export interface PromptUpdate {
  /** Is Default */
  is_default?: boolean | null;
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
 * ResponseModelCreate
 * Create model for response models.
 */
export interface ResponseModelCreate {
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
  dependencies?: Record<string, DependencyInfo>;
  /** Schema Data */
  schema_data?: object;
  /** Examples */
  examples?: object[];
  /**
   * Is Active
   * @default false
   */
  is_active?: boolean;
}

/**
 * ResponseModelPublic
 * Public model for response models.
 */
export interface ResponseModelPublic {
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
  dependencies?: Record<string, DependencyInfo>;
  /** Schema Data */
  schema_data?: object;
  /** Examples */
  examples?: object[];
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
  /** Environment */
  environment: string;
}

/**
 * SpanMoreDetails
 * Span more details model.
 */
export interface SpanMoreDetails {
  /** Project Uuid */
  project_uuid?: string | null;
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
  /** Template */
  template?: string | null;
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
  /** Prompt Uuid */
  prompt_uuid?: string | null;
  /** Response Model Uuid */
  response_model_uuid?: string | null;
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
  /**
   * Project Uuid
   * @format uuid
   */
  project_uuid: string;
  /** Display Name */
  display_name?: string | null;
  generation?: GenerationPublic | null;
  prompt?: PromptPublic | null;
  response_model?: ResponseModelPublic | null;
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
