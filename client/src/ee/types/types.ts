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

/**
 * EvaluationType
 * Evaluation type enum
 */
export enum EvaluationType {
  MANUAL = "manual",
  VERIFIED = "verified",
  EDITED = "edited",
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
