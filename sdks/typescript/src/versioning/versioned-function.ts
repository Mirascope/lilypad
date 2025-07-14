/**
 * Versioned function implementation
 * Based on Python SDK's versioning functionality
 */

import { getPooledClient } from '../utils/client-pool';
import { getSettings } from '../utils/settings';
import { logger } from '../utils/logger';
import { createSandbox } from './sandbox';
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
    // Return an async wrapper if the original function is async
    const isAsync = fn.constructor.name === 'AsyncFunction' || 
                   fn.toString().includes('async') ||
                   fn.toString().match(/^\s*async/);
    
    const versionedExecutor = async function (this: any, ...args: Parameters<T>): Promise<any> {
      logger.info(`Executing version ${version} of ${name}`);

      if (!settings) {
        logger.warn('Lilypad not configured. Executing current version.');
        return fn.apply(this, args);
      }

      try {
        const client = getPooledClient(settings);
        
        // Fetch all versions of the function
        const versions = await versionedFn.versions();
        const targetVersion = versions.find(v => v.version === version);
        
        if (!targetVersion) {
          logger.warn(`Version ${version} not found. Executing current version.`);
          return fn.apply(this, args);
        }
        
        // Get the specific version's code
        const versionedFunc = await client.projects.functions.get(
          metadata.projectId,
          targetVersion.uuid
        );
        
        if (!versionedFunc.code) {
          logger.warn(`No code found for version ${version}. Executing current version.`);
          return fn.apply(this, args);
        }
        
        logger.info(`Found version ${version} code, executing in sandbox...`);
        
        // Prepare code for execution
        let executableCode = versionedFunc.code;
        
        // If the code looks like a method definition (no 'function' keyword at start),
        // wrap it as a function expression
        if (!executableCode.trim().startsWith('function') && 
            !executableCode.trim().startsWith('(') &&
            !executableCode.trim().startsWith('async function')) {
          // It's likely a method definition like "async calculateTax(amount) { ... }"
          // Convert to function expression
          if (executableCode.trim().startsWith('async ')) {
            executableCode = `(async function ${executableCode.substring(6)})`;
          } else {
            executableCode = `(function ${executableCode})`;
          }
        }
        
        // Execute in sandbox
        const sandbox = createSandbox();
        // Convert dependencies if needed
        let sandboxDeps: Record<string, string> = {};
        if (versionedFunc.dependencies) {
          sandboxDeps = Object.entries(versionedFunc.dependencies).reduce((acc, [key, value]) => {
            acc[key] = typeof value === 'string' ? value : (value as any).version;
            return acc;
          }, {} as Record<string, string>);
        }
        
        const result = await sandbox.execute(executableCode, args, {
          timeout: 30000,
          memoryLimit: 128,
          dependencies: sandboxDeps,
        });
        
        if (result.error) {
          logger.error(`Version ${version} execution failed:`, result.error);
          throw result.error;
        }
        
        logger.info(`Version ${version} executed successfully in ${result.executionTime}ms`);
        return result.result;
      } catch (error) {
        logger.error(`Failed to execute version ${version}:`, error);
        // Fallback to current version
        return fn.apply(this, args);
      }
    };
    
    // For sync functions, create a sync wrapper that throws
    if (!isAsync) {
      return function (this: any): ReturnType<T> {
        throw new Error(
          `Version execution requires async operation. ` +
          `Please use an async function or await the result.`
        );
      } as T;
    }
    
    return versionedExecutor as T;
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
      
      // First, try to get the latest deployed version
      // In a real implementation, this would fetch from the deployment API
      let deployedCode: string | null = null;
      let dependencies: Record<string, string> = {};
      
      try {
        // Try to get function by UUID first
        if (metadata.functionUuid) {
          const func = await client.projects.functions.get(metadata.projectId, metadata.functionUuid);
          deployedCode = func.code;
          // Convert DependencyInfo to simple version string
          if (func.dependencies) {
            dependencies = Object.entries(func.dependencies).reduce((acc, [key, value]) => {
              acc[key] = typeof value === 'string' ? value : value.version;
              return acc;
            }, {} as Record<string, string>);
          }
        } else if (metadata.name) {
          // Fall back to name-based lookup
          const funcs = await client.projects.functions.getByName(metadata.projectId, metadata.name);
          if (Array.isArray(funcs) && funcs.length > 0) {
            // Get the latest version
            const latest = funcs.sort((a: any, b: any) => 
              (b.version_num || 0) - (a.version_num || 0)
            )[0];
            deployedCode = latest.code;
            // Convert dependencies
            if (latest.dependencies) {
              dependencies = Object.entries(latest.dependencies).reduce((acc, [key, value]) => {
                acc[key] = typeof value === 'string' ? value : (value as any).version;
                return acc;
              }, {} as Record<string, string>);
            }
          }
        }
      } catch (error) {
        logger.debug('Failed to fetch deployed function:', error);
      }

      if (!deployedCode) {
        logger.warn('No deployed version found. Executing locally.');
        return fn.apply(this, args);
      }

      // Log deployment info
      logger.info(`Found deployed version with ${Object.keys(dependencies).length} dependencies`);
      logger.debug('Deployed code preview:', deployedCode.substring(0, 200));
      
      // Check if we have a bundled version (from build artifacts)
      // This would be the IIFE bundle generated by the build process
      const artifactsDir = process.env.LILYPAD_ARTIFACTS_DIR || './dist/trace-artifacts';
      const bundlePath = `${artifactsDir}/${name}.bundle.js`;
      
      let codeToExecute = deployedCode;
      
      try {
        // Try to load the bundle if available
        const fs = await import('node:fs/promises');
        const bundleCode = await fs.readFile(bundlePath, 'utf-8');
        codeToExecute = bundleCode;
        logger.debug('Using bundled code for execution');
      } catch {
        logger.debug('Bundle not found, using raw code');
      }

      // Ensure code is properly formatted as an executable function
      let executableCode = codeToExecute;
      
      // If the code looks like a method definition (no 'function' keyword at start),
      // wrap it as a function expression
      if (!executableCode.trim().startsWith('function') && 
          !executableCode.trim().startsWith('(') &&
          !executableCode.trim().startsWith('async function')) {
        // It's likely a method definition like "async calculateTax(amount) { ... }"
        // Convert to function expression
        if (executableCode.trim().startsWith('async ')) {
          executableCode = `(async function ${executableCode.substring(6)})`;
        } else {
          executableCode = `(function ${executableCode})`;
        }
      }

      // Execute in sandbox
      const sandbox = createSandbox();
      const result = await sandbox.execute(executableCode, args, {
        timeout: 30000,
        memoryLimit: 128,
        dependencies,
      });

      // Log execution details
      if (result.logs.length > 0) {
        logger.debug('Remote execution logs:', result.logs);
      }
      logger.info(`Remote execution completed in ${result.executionTime}ms`);

      if (result.error) {
        logger.error('Remote execution failed:', result.error);
        throw result.error;
      }

      return result.result;
    } catch (error) {
      logger.error('Failed to execute remote function:', error);
      // Fallback to local execution
      logger.info('Falling back to local execution');
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

// Export the original function with a different name
export { createVersionedFunction as createVersionedFunctionCore }
