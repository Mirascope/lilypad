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
 * CallBase
 * Call model
 */
export interface CallBase {
  /** Prompt Version Id */
  prompt_version_id?: number;
  /** Input */
  input: string;
  /** Output */
  output: string;
  /**
   * Created At
   * @format date-time
   * @default "2024-09-19T23:07:10.231056Z"
   */
  created_at?: string;
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
   * @default "2024-09-19T23:07:10.231056Z"
   */
  created_at?: string;
  /** Id */
  id: number;
  /** Prompt Version public model. */
  prompt_version: PromptVersionPublic;
}

/**
 * CallTable
 * Call table
 */
export interface CallTable {
  /** Prompt Version Id */
  prompt_version_id?: number;
  /** Input */
  input: string;
  /** Output */
  output: string;
  /**
   * Created At
   * @format date-time
   * @default "2024-09-19T23:07:10.231056Z"
   */
  created_at?: string;
  /** Id */
  id?: number | null;
}

/** HTTPValidationError */
export interface HTTPValidationError {
  /** Detail */
  detail?: ValidationError[];
}

/**
 * PromptVersionBase
 * Prompt version model
 */
export interface PromptVersionBase {
  /** Function Name */
  function_name: string;
  /** Version Hash */
  version_hash?: string | null;
  /** Lexical Closure */
  lexical_closure: string;
  /** Prompt Template */
  prompt_template: string;
  /** Input Arguments */
  input_arguments?: string | null;
  /** Previous Version Id */
  previous_version_id?: number | null;
}

/**
 * PromptVersionPublic
 * Prompt Version public model.
 */
export interface PromptVersionPublic {
  /** Function Name */
  function_name: string;
  /** Version Hash */
  version_hash?: string | null;
  /** Lexical Closure */
  lexical_closure: string;
  /** Prompt Template */
  prompt_template: string;
  /** Input Arguments */
  input_arguments?: string | null;
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
