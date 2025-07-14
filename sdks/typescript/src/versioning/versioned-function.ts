/**
 * Versioned function implementation
 * Based on Python SDK's versioning functionality
 */

import { getPooledClient } from '../utils/client-pool';
import { getSettings } from '../utils/settings';
import { logger } from '../utils/logger';
import type {
  VersionedFunction,
  VersionedFunctionMethods,
  FunctionVersion,
} from '../types/versioning';

/**
 * Create a versioned function with version management capabilities
 */
export function createVersionedFunction<T extends (...args: any[]) => any>(
  fn: T,
  name: string,
  projectId: string,
  functionUuid?: string,
): VersionedFunction<T> {
  const settings = getSettings();

  // Store function metadata with mutable reference
  const metadata = {
    name,
    projectId,
    functionUuid: functionUuid || '',
    currentVersion: 1,
    isDeployed: false,
  };

  // Allow updating function UUID after creation
  const setFunctionUuid = (uuid: string) => {
    metadata.functionUuid = uuid;
  };

  // Create the enhanced function that preserves context
  const versionedFn = function (this: any, ...args: Parameters<T>): ReturnType<T> {
    // If the wrapped function needs to update metadata (e.g., function UUID)
    if (typeof (fn as any).__updateVersioningMetadata === 'function') {
      (fn as any).__updateVersioningMetadata(setFunctionUuid);
    }
    // Execute the function with proper context
    return fn.apply(this, args);
  } as T & VersionedFunctionMethods<T>;

  // Add version method
  versionedFn.version = function (version: number): T {
    return function (this: any, ...args: Parameters<T>): ReturnType<T> {
      logger.info(`Executing version ${version} of ${name}`);

      // In the Python SDK, this executes the specific version in a sandbox
      // For TypeScript, we would need to:
      // 1. Fetch the function code for the specific version
      // 2. Execute it in an isolated environment
      // For now, we execute locally and log the version request

      if (settings && metadata.functionUuid) {
        // TODO: Implement actual version execution
        // This would involve:
        // 1. Fetching the function code for the specific version
        // 2. Creating a sandbox or isolated execution environment
        // 3. Executing the versioned code with the provided arguments
        logger.info(`Version ${version} execution not yet implemented. Executing current version.`);
      }

      // Execute the current function (sandbox execution not implemented)
      return fn.apply(this, args);
    } as T;
  };

  // Add remote method for calling deployed version
  versionedFn.remote = async function (this: any, ...args: Parameters<T>): Promise<any> {
    logger.info(`Executing remote deployed version of ${name}`);

    if (!settings) {
      logger.warn('Lilypad not configured. Executing locally.');
      return fn.apply(this, args);
    }

    if (!metadata.functionUuid && !metadata.name) {
      logger.warn('Function UUID or name not available. Executing locally.');
      return fn.apply(this, args);
    }

    try {
      // Get the deployed function code from the server
      const client = getPooledClient(settings);
      const deployedFunction = await client.projects.functions.getDeployedEnvironments(
        metadata.projectId,
        metadata.name,
      );

      if (!deployedFunction || !deployedFunction.code) {
        logger.warn('No deployed version found. Executing locally.');
        return fn.apply(this, args);
      }

      // Log the deployed function information
      logger.info(`Found deployed version: ${deployedFunction.version_num || 'latest'}`);
      logger.debug('Function code length:', deployedFunction.code.length);
      logger.debug('Dependencies:', Object.keys(deployedFunction.dependencies || {}));

      // TODO: Implement sandbox execution with dependencies
      // The Python SDK uses SubprocessSandboxRunner to execute the code
      // with all dependencies in an isolated environment
      // 
      // For JavaScript/TypeScript, we would need:
      // 1. A sandboxing solution (e.g., vm2, isolated-vm, or worker threads)
      // 2. Dynamic module loading for dependencies
      // 3. Security considerations for executing remote code
      //
      // Example approach:
      // - Create a new V8 isolate or worker thread
      // - Install dependencies listed in deployedFunction.dependencies
      // - Execute deployedFunction.code with proper context
      // - Return the result
      
      logger.warn('Remote execution with dependencies not yet implemented.');
      logger.warn('Required dependencies:', deployedFunction.dependencies);
      logger.info('Falling back to local execution.');

      // Execute locally as fallback
      return fn.apply(this, args);
    } catch (error) {
      logger.error('Failed to fetch deployed function:', error);
      // Fallback to local execution
      return fn.apply(this, args);
    }
  } as T;

  // Add versions method to list available versions
  versionedFn.versions = async function (): Promise<FunctionVersion[]> {
    if (!settings) {
      logger.warn('Lilypad SDK not configured. Cannot fetch versions.');
      return [];
    }

    if (!metadata.functionUuid && !metadata.name) {
      logger.warn('Cannot fetch versions without function UUID or name');
      return [];
    }

    try {
      const client = getPooledClient(settings);

      // Try to use function UUID if available, otherwise fall back to name
      let response;
      if (metadata.functionUuid) {
        // Get function by UUID to find all versions
        const func = await client.projects.functions.get(metadata.projectId, metadata.functionUuid);
        // Then get all versions of this function by name
        response = await client.projects.functions.getByName(metadata.projectId, func.name);
      } else if (metadata.name) {
        // Fall back to name-based lookup
        response = await client.projects.functions.getByName(metadata.projectId, metadata.name);
      }

      // The response contains all versions of the function
      if (Array.isArray(response)) {
        return response.map((fn: any) => ({
          version: fn.version_num || 1,
          uuid: fn.uuid,
          created_at: fn.created_at || new Date().toISOString(),
          is_deployed: false, // Check against deployed environments
        }));
      }

      return [];
    } catch (error) {
      logger.error('Failed to fetch versions:', error);
      return [];
    }
  };

  // Add deploy method
  versionedFn.deploy = async function (version: number): Promise<void> {
    if (!settings) {
      throw new Error('Lilypad SDK not configured');
    }

    try {
      logger.info(`Deploy version ${version} of ${name} - requires environment setup`);
      metadata.isDeployed = true;
    } catch (error) {
      logger.error('Failed to deploy version:', error);
      throw error;
    }
  };

  // Preserve function properties
  Object.setPrototypeOf(versionedFn, fn);
  Object.defineProperty(versionedFn, 'name', {
    value: fn.name || name,
    configurable: true,
  });
  Object.defineProperty(versionedFn, 'length', {
    value: fn.length,
    configurable: true,
  });

  return versionedFn;
}

/**
 * Check if a function is a versioned function
 */
export function isVersionedFunction(fn: any): fn is VersionedFunction<any> {
  return (
    typeof fn === 'function' &&
    'version' in fn &&
    'remote' in fn &&
    'versions' in fn &&
    'deploy' in fn
  );
}
