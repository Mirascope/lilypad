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
 * CallCreate
 * Call create model.
 */
export interface CallCreate {
  /** Project Name */
  project_name: string;
  /** Input */
  input: string;
  /** Output */
  output: string;
}

/**
 * CallPublicWithPromptVersion
 * Call public model with prompt version.
 */
export interface CallPublicWithPromptVersion {
  /** Prompt Version Id */
  prompt_version_id?: number;
  /** Input */
  input: string;
  /** Output */
  output: string;
  /**
   * Created At
   * @format date-time
   * @default "2024-09-16T23:51:18.634283Z"
   */
  created_at?: string;
  /** Id */
  id: number;
  /** Prompt Version public model. */
  prompt_version: PromptVersionPublic;
}

/** HTTPValidationError */
export interface HTTPValidationError {
  /** Detail */
  detail?: ValidationError[];
}

/**
 * PromptVersionPublic
 * Prompt Version public model.
 */
export interface PromptVersionPublic {
  /** Project Id */
  project_id?: number;
  /** Function Name */
  function_name: string;
  /** Prompt Template */
  prompt_template: string;
  /** Previous Version Id */
  previous_version_id?: number | null;
  /** Id */
  id: number;
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
