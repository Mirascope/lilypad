/**
 * Types for function versioning support
 */

export interface FunctionVersion {
  version: number;
  uuid: string;
  created_at: string;
  is_deployed: boolean;
}

export interface VersionedFunctionMethods<T extends (...args: any[]) => any> {
  /**
   * Call a specific version of the function
   */
  version(version: number): T;

  /**
   * Call the currently deployed version (remote execution)
   */
  remote(...args: Parameters<T>): Promise<any>;

  /**
   * Get available versions
   */
  versions(): Promise<FunctionVersion[]>;

  /**
   * Deploy a specific version
   */
  deploy(version: number): Promise<void>;
}

export type VersionedFunction<T extends (...args: any[]) => any> = T & VersionedFunctionMethods<T>;

export type AsyncVersionedFunction<T extends (...args: any[]) => Promise<any>> = T &
  VersionedFunctionMethods<T>;

export interface VersionedTrace<T> {
  result: T;
  traceId: string;
  version?: number;
  isRemote?: boolean;
}

export interface AsyncVersionedTrace<T> extends VersionedTrace<T> {
  result: T;
}
