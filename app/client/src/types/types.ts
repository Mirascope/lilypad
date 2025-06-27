/* eslint-disable */
/* tslint:disable */
// @ts-nocheck
/*
 * ---------------------------------------------------------------
 * ## THIS FILE WAS GENERATED VIA SWAGGER-TYPESCRIPT-API        ##
 * ##                                                           ##
 * ## AUTHOR: acacode                                           ##
 * ## SOURCE: https://github.com/acacode/swagger-typescript-api ##
 * ---------------------------------------------------------------
 */

/**
 * UserRole
 * User role enum.
 */
export enum UserRole {
  OWNER = "owner",
  ADMIN = "admin",
  MEMBER = "member",
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
 * Tier
 * License tier enum.
 */
export enum Tier {
  FREE = 0,
  PRO = 1,
  TEAM = 2,
  ENTERPRISE = 3,
}

/**
 * SubscriptionStatus
 * Subscription status enum based on Stripe's subscription statuses.
 */
export enum SubscriptionStatus {
  ACTIVE = "active",
  PAST_DUE = "past_due",
  UNPAID = "unpaid",
  CANCELED = "canceled",
  INCOMPLETE = "incomplete",
  INCOMPLETE_EXPIRED = "incomplete_expired",
  TRIALING = "trialing",
  PAUSED = "paused",
}

/**
 * SpanType
 * Span type
 */
export enum SpanType {
  FUNCTION = "function",
  TRACE = "trace",
  MIRASCOPE_V_1 = "mirascope.v1",
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
 * PlaygroundErrorType
 * Categorizes the types of errors that can occur during playground execution.
 */
export enum PlaygroundErrorType {
  TIMEOUT_ERROR = "TimeoutError",
  CONFIGURATION_ERROR = "ConfigurationError",
  SUBPROCESS_ERROR = "SubprocessError",
  OUTPUT_PARSING_ERROR = "OutputParsingError",
  OUTPUT_MARKER_ERROR = "OutputMarkerError",
  INTERNAL_PLAYGROUND_ERROR = "InternalPlaygroundError",
  EXECUTION_ERROR = "ExecutionError",
  BAD_REQUEST_ERROR = "BadRequestError",
  NOT_FOUND_ERROR = "NotFoundError",
  INVALID_INPUT_ERROR = "InvalidInputError",
  API_KEY_ISSUE = "ApiKeyIssue",
  UNEXPECTED_SERVER_ERROR = "UnexpectedServerError",
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
 * EvaluationType
 * Evaluation type enum
 */
export enum EvaluationType {
  MANUAL = "manual",
  VERIFIED = "verified",
  EDITED = "edited",
}

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
  /** Environment Uuid */
  environment_uuid?: string | null;
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
  /** Environment Uuid */
  environment_uuid?: string | null;
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
  /** Environment public model. */
  environment: EnvironmentPublic;
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
  /** Function Uuid */
  function_uuid: string | null;
}

/**
 * AnnotationCreate
 * Annotation create model.
 */
export interface AnnotationCreate {
  /** Span Uuid */
  span_uuid?: string | null;
  /** Project Uuid */
  project_uuid?: string | null;
  /** Function Uuid */
  function_uuid?: string | null;
  label?: Label | null;
  /** Reasoning */
  reasoning?: string | null;
  type?: EvaluationType | null;
  /** Data */
  data?: object | null;
  /** Assigned To */
  assigned_to?: string[] | null;
  /** Assignee Email */
  assignee_email?: string[] | null;
}

/**
 * AnnotationMetrics
 * Annotation metrics model.
 */
export interface AnnotationMetrics {
  /**
   * Function Uuid
   * @format uuid
   */
  function_uuid: string;
  /** Total Count */
  total_count: number;
  /** Success Count */
  success_count: number;
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
  /** Function Uuid */
  function_uuid?: string | null;
  /**
   * Created At
   * @format date-time
   */
  created_at: string;
  /** Span more details model. */
  span: SpanMoreDetails;
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
 * BillingPublic
 * Schema for public billing information.
 */
export interface BillingPublic {
  /** Stripe Customer Id */
  stripe_customer_id: string | null;
  /** Stripe Subscription Id */
  stripe_subscription_id?: string | null;
  /** Stripe Price Id */
  stripe_price_id?: string | null;
  subscription_status?: SubscriptionStatus | null;
  /** Subscription Current Period Start */
  subscription_current_period_start?: string | null;
  /** Subscription Current Period End */
  subscription_current_period_end?: string | null;
  /**
   * Usage Quantity
   * @default 0
   */
  usage_quantity?: number;
  /** Last Usage Report */
  last_usage_report?: string | null;
  /**
   * Cancel At Period End
   * Whether the subscription should be canceled at the end of the period
   * @default false
   */
  cancel_at_period_end?: boolean | null;
  /** Metadata */
  metadata_?: object;
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
  /**
   * Created At
   * @format date-time
   */
  created_at: string;
}

/**
 * CommentCreate
 * Comment Create Model.
 */
export interface CommentCreate {
  /** Text */
  text: string;
  /**
   * Span Uuid
   * @format uuid
   */
  span_uuid: string;
  /** Parent Comment Uuid */
  parent_comment_uuid?: string | null;
}

/**
 * CommentPublic
 * Comment Public Model.
 */
export interface CommentPublic {
  /** Text */
  text: string;
  /**
   * User Uuid
   * @format uuid
   */
  user_uuid: string;
  /**
   * Span Uuid
   * @format uuid
   */
  span_uuid: string;
  /** Parent Comment Uuid */
  parent_comment_uuid?: string | null;
  /** Updated At */
  updated_at?: string | null;
  /**
   * Is Edited
   * @default false
   */
  is_edited?: boolean;
  /**
   * Uuid
   * @format uuid
   */
  uuid: string;
  /**
   * Created At
   * @format date-time
   */
  created_at: string;
}

/**
 * CommentUpdate
 * Comment Update Model.
 */
export interface CommentUpdate {
  /** Text */
  text?: string | null;
  /** Is Edited */
  is_edited?: boolean | null;
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

/**
 * CreateUserOrganizationToken
 * Create user organization token model
 */
export interface CreateUserOrganizationToken {
  /** Token */
  token: string;
}

/**
 * DependencyInfo
 * Dependency information.
 */
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
   * Function Uuid
   * @format uuid
   */
  function_uuid: string;
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
  function?: FunctionPublic | null;
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
   * Is Development
   * @default false
   */
  is_development?: boolean | null;
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
   * Is Development
   * @default false
   */
  is_development?: boolean | null;
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
  /**
   * Created At
   * @format date-time
   */
  created_at: string;
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
 * EventSummaryResponse
 * Response model for event summaries.
 */
export interface EventSummaryResponse {
  /** Current Meter */
  current_meter: number;
  /** Monthly Total */
  monthly_total: number;
}

/**
 * ExternalAPIKeyCreate
 * Request model for creating a secret.
 */
export interface ExternalAPIKeyCreate {
  /** Service Name */
  service_name: string;
  /**
   * Api Key
   * New API key
   * @minLength 1
   */
  api_key: string;
}

/**
 * ExternalAPIKeyPublic
 * Response model for a secret.
 */
export interface ExternalAPIKeyPublic {
  /** Service Name */
  service_name: string;
  /**
   * Masked Api Key
   * Partially masked API key
   */
  masked_api_key: string;
}

/**
 * ExternalAPIKeyUpdate
 * Request model for updating a secret.
 */
export interface ExternalAPIKeyUpdate {
  /**
   * Api Key
   * New API key
   * @minLength 1
   */
  api_key: string;
}

/**
 * FunctionCreate
 * Function create model.
 */
export interface FunctionCreate {
  /** Project Uuid */
  project_uuid?: string | null;
  /** Version Num */
  version_num?: number | null;
  /**
   * Name
   * @minLength 1
   * @maxLength 512
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
   * Is Versioned
   * @default false
   */
  is_versioned?: boolean | null;
}

/**
 * FunctionPublic
 * Function public model.
 */
export interface FunctionPublic {
  /** Project Uuid */
  project_uuid?: string | null;
  /** Version Num */
  version_num?: number | null;
  /**
   * Name
   * @minLength 1
   * @maxLength 512
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
   * Is Versioned
   * @default false
   */
  is_versioned?: boolean | null;
  /**
   * Uuid
   * @format uuid
   */
  uuid: string;
}

/**
 * FunctionUpdate
 * Function update model.
 */
export type FunctionUpdate = object;

/** HTTPValidationError */
export interface HTTPValidationError {
  /** Detail */
  detail?: ValidationError[];
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
  /** Organization Uuid */
  organization_uuid: string | null;
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
 * OrganizationCreate
 * Organization create model
 */
export interface OrganizationCreate {
  /**
   * Name
   * @minLength 1
   */
  name: string;
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
  billing?: BillingPublic | null;
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

/** Paginated[SpanPublic] */
export interface PaginatedSpanPublic {
  /**
   * Items
   * Current slice of items
   */
  items: SpanPublic[];
  /**
   * Limit
   * Requested page size (limit)
   * @min 1
   */
  limit: number;
  /**
   * Offset
   * Requested offset
   * @min 0
   */
  offset: number;
  /**
   * Total
   * Total number of items
   * @min 0
   */
  total: number;
}

/**
 * PlaygroundErrorDetail
 * Detailed information about a playground error.
 */
export interface PlaygroundErrorDetail {
  /**
   * Type
   * Category of the error (Enum value) or specific Python Exception type name.
   */
  type: PlaygroundErrorType | string;
  /**
   * Reason
   * User-friendly description of the error.
   */
  reason: string;
  /**
   * Details
   * Additional technical details, if available.
   */
  details?: string | null;
}

/**
 * PlaygroundErrorResponse
 * Standard structure for playground error responses.
 */
export interface PlaygroundErrorResponse {
  /** Detailed information about a playground error. */
  error: PlaygroundErrorDetail;
}

/**
 * PlaygroundParameters
 * Playground parameters model.
 */
export interface PlaygroundParameters {
  /** Arg Values */
  arg_values: Record<string, number | boolean | string | any[] | object>;
  /** Arg Types */
  arg_types: Record<string, string> | null;
  /** Provider name enum */
  provider: Provider;
  /** Model */
  model: string;
  /** Prompt Template */
  prompt_template: string;
  call_params: CommonCallParams | null;
}

/**
 * PlaygroundSuccessResponse
 * Standard structure for successful playground execution responses.
 */
export interface PlaygroundSuccessResponse {
  /**
   * Result
   * The result returned by the executed function. Can be any JSON-serializable type.
   */
  result: any;
  /** Tracing context associated with the execution. */
  trace_context?: TraceContextModel | null;
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
   * Created At
   * @format date-time
   */
  created_at: string;
}

/**
 * RecentSpansResponse
 * Response model for recent spans polling endpoint.
 */
export interface RecentSpansResponse {
  /** Spans */
  spans: SpanPublic[];
  /**
   * Timestamp
   * @format date-time
   */
  timestamp: string;
  /** Project Uuid */
  project_uuid: string;
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
  /**
   * Project Uuid
   * @format uuid
   */
  project_uuid: string;
  /** Function Uuid */
  function_uuid?: string | null;
  /** Display Name */
  display_name: string;
  /** Provider */
  provider: string;
  /** Model */
  model: string;
  /** Instrumentation Scope name of the span */
  scope: Scope;
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
  /** Tags */
  tags?: TagPublic[] | null;
  /** Session Id */
  session_id?: string | null;
  /** Span Id */
  span_id: string;
  /** Response */
  response?: object | null;
  /** Response Model */
  response_model?: object | null;
}

/**
 * SpanPublic
 * Span public model
 */
export interface SpanPublic {
  /** Span Id */
  span_id: string;
  /** Trace Id */
  trace_id: string | null;
  /** Function Uuid */
  function_uuid?: string | null;
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
  /** Session Id */
  session_id?: string | null;
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
  function: FunctionPublic | null;
  /** Annotations */
  annotations: AnnotationPublic[];
  /** Child Spans */
  child_spans: SpanPublic[];
  /**
   * Created At
   * @format date-time
   */
  created_at: string;
  /** Status */
  status?: string | null;
  /** Tags */
  tags: TagPublic[];
  /** Score */
  score?: number | null;
}

/**
 * SpanUpdate
 * Span update model
 */
export interface SpanUpdate {
  /** Tags By Uuid */
  tags_by_uuid?: string[] | null;
  /** Tags By Name */
  tags_by_name?: string[] | null;
}

/**
 * StripeCheckoutSession
 * Response model for Stripe checkout session creation.
 */
export interface StripeCheckoutSession {
  /** License tier enum. */
  tier: Tier;
}

/**
 * StripeWebhookResponse
 * Response schema for Stripe webhook events.
 */
export interface StripeWebhookResponse {
  /** Status */
  status: "success" | "error" | "ignored";
  /** Event */
  event?: string | null;
  /** Message */
  message?: string | null;
}

/**
 * TagCreate
 * Tag Create Model.
 */
export interface TagCreate {
  /** Project Uuid */
  project_uuid?: string | null;
  /**
   * Name
   * @minLength 1
   */
  name: string;
}

/**
 * TagPublic
 * Tag Public Model.
 */
export interface TagPublic {
  /** Project Uuid */
  project_uuid?: string | null;
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
  /**
   * Created At
   * @format date-time
   */
  created_at: string;
  /**
   * Organization Uuid
   * @format uuid
   */
  organization_uuid: string;
}

/**
 * TraceContextModel
 * Represents the tracing context information provided by Lilypad.
 */
export interface TraceContextModel {
  /**
   * Span Uuid
   * The unique identifier for the current span within the trace.
   */
  span_uuid?: string | null;
}

/**
 * TracesQueueResponse
 * Response model for queued traces.
 */
export interface TracesQueueResponse {
  /** Trace Status */
  trace_status: "queued" | "processed";
  /** Span Count */
  span_count: number;
  /** Message */
  message: string;
  /** Trace Ids */
  trace_ids: string[];
}

/**
 * UserConsentCreate
 * UserConsent create model.
 */
export interface UserConsentCreate {
  /** Privacy Policy Version */
  privacy_policy_version: string;
  /** Privacy Policy Accepted At */
  privacy_policy_accepted_at?: string | null;
  /** Tos Version */
  tos_version: string;
  /** Tos Accepted At */
  tos_accepted_at?: string | null;
  /** User Uuid */
  user_uuid?: string | null;
}

/**
 * UserConsentPublic
 * UserConsent public model.
 */
export interface UserConsentPublic {
  /**
   * Privacy Policy Version
   * Last updated date of the privacy policy accepted
   * @default "2025-04-04"
   */
  privacy_policy_version?: string;
  /**
   * Privacy Policy Accepted At
   * @format date-time
   */
  privacy_policy_accepted_at: string;
  /**
   * Tos Version
   * Last updated date of the terms of service accepted
   * @default "2025-04-04"
   */
  tos_version?: string;
  /**
   * Tos Accepted At
   * @format date-time
   */
  tos_accepted_at: string;
  /**
   * Uuid
   * @format uuid
   */
  uuid: string;
}

/**
 * UserConsentUpdate
 * UserConsent update model.
 */
export interface UserConsentUpdate {
  /** Privacy Policy Version */
  privacy_policy_version?: string | null;
  /** Privacy Policy Accepted At */
  privacy_policy_accepted_at?: string | null;
  /** Tos Version */
  tos_version?: string | null;
  /** Tos Accepted At */
  tos_accepted_at?: string | null;
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
  /** Scopes */
  scopes?: string[];
  user_consents?: UserConsentPublic | null;
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
