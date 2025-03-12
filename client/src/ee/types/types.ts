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
 * Message parameter model.
 */
export interface MessageParam {
  /** Message */
  message: string;
  /**
   * Timestamp
   * @format date-time
   */
  timestamp: string;
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
