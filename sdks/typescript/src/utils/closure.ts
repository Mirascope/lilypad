import * as crypto from 'crypto';
import { logger } from './logger';
import { formatCode } from './code-formatter';
import { getTypeScriptSource } from '../versioning/metadata-loader';

export interface DependencyInfo {
  version: string;
  extras?: string[];
}

export interface ImportInfo {
  module: string;
  names?: string[];
  isDefault?: boolean;
  isNamespace?: boolean;
}

export interface ClosureData {
  name: string;
  signature: string;
  code: string;
  hash: string;
  dependencies: Record<string, DependencyInfo>;
  isVersioned?: boolean;
}

// Type for any callable function - using unknown is safer than any
export type AnyFunction = (...args: unknown[]) => unknown;

/**
 * Get the qualified name of a function
 */
export function getQualifiedName(fn: AnyFunction): string {
  // In TypeScript/JavaScript, we don't have __qualname__ like Python
  // Use function name or 'anonymous'
  return fn.name || 'anonymous';
}

/**
 * Get function signature (simplified version)
 */
function getFunctionSignature(fn: AnyFunction): string {
  const fnStr = fn.toString();

  // Extract the function signature part
  const match = fnStr.match(
    /^(?:async\s+)?(?:function\s*\*?\s*)?(?:[a-zA-Z_$][\w$]*)?\s*\([^)]*\)/,
  );
  if (match) {
    return match[0];
  }

  // For arrow functions
  const arrowMatch = fnStr.match(/^(?:async\s+)?\([^)]*\)\s*=>/);
  if (arrowMatch) {
    return arrowMatch[0].replace(/\s*=>$/, '');
  }

  // Fallback
  return 'function()';
}

/**
 * Simple closure representation for TypeScript
 */
export class Closure implements ClosureData {
  name: string;
  signature: string;
  code: string;
  hash: string;
  dependencies: Record<string, DependencyInfo>;

  constructor(data: ClosureData) {
    this.name = data.name;
    this.signature = data.signature;
    this.code = data.code;
    this.hash = data.hash;
    this.dependencies = data.dependencies;
  }

  /**
   * Create a closure from a function
   * Note: This is a simplified version compared to Python implementation
   */
  static fromFunction(
    fn: AnyFunction,
    dependencies?: Record<string, DependencyInfo>,
    isVersioned: boolean = false,
    functionName?: string,
  ): Closure {
    const name = functionName || getQualifiedName(fn);
    const rawJsCode = fn.toString();

    let code: string;
    let hash: string;

    // For versioned functions, try to get TypeScript source from metadata
    if (isVersioned) {
      logger.debug(`[Closure.fromFunction] Looking for TypeScript source for ${name}`);
      // Use name-based lookup since hash won't match between TS and JS
      const tsSource = getTypeScriptSource('', name);
      if (tsSource) {
        // Use TypeScript source
        code = tsSource;
        // Compute hash based on TypeScript source
        hash = crypto
          .createHash('sha256')
          .update(tsSource)
          .update(JSON.stringify(dependencies || {}))
          .digest('hex');
        logger.debug(
          `[Closure.fromFunction] ✅ Using TypeScript source for ${name}, hash: ${hash}`,
        );
      } else {
        // Fall back to formatted JavaScript
        code = formatCode(rawJsCode);
        // Compute hash based on JavaScript code
        hash = crypto
          .createHash('sha256')
          .update(code)
          .update(JSON.stringify(dependencies || {}))
          .digest('hex');
        logger.debug(
          `[Closure.fromFunction] ⚠️ TypeScript source not found for ${name}, using JavaScript`,
        );
      }
    } else {
      // Non-versioned functions use raw JavaScript
      code = rawJsCode;
      hash = crypto
        .createHash('sha256')
        .update(code)
        .update(JSON.stringify(dependencies || {}))
        .digest('hex');
    }

    // Debug log
    logger.debug(`[Closure.fromFunction] Creating closure for function ${name}:`, {
      name,
      codeLength: code.length,
      codePreview: code.substring(0, 100),
      isVersioned,
      usingTypeScript: isVersioned && code !== formatCode(rawJsCode),
    });

    const signature = getFunctionSignature(fn);

    return new Closure({
      name,
      signature,
      code,
      hash,
      dependencies: dependencies || {},
      isVersioned,
    });
  }
}

// Function cache for memoization
const functionCache = new WeakMap<AnyFunction, Closure>();

/**
 * Get or create closure for a function with caching
 */
export function getCachedClosure(
  fn: AnyFunction,
  dependencies?: Record<string, DependencyInfo>,
  isVersioned: boolean = false,
  functionName?: string,
): Closure {
  // For versioned functions, always create a new closure to ensure
  // we get the latest code
  if (isVersioned) {
    logger.debug(`[getCachedClosure] Creating versioned closure for ${functionName || 'unknown'}`);
    const closure = Closure.fromFunction(fn, dependencies, isVersioned, functionName);

    // Check if TypeScript source was used
    const tsFound =
      closure.code.includes(': ') ||
      closure.code.includes('Promise<') ||
      closure.code.includes('interface') ||
      closure.code.includes('type ');
    logger.debug(
      `[getCachedClosure] TypeScript source ${tsFound ? 'USED' : 'NOT USED'} for ${functionName || closure.name}`,
    );
    logger.debug(`[getCachedClosure] Code preview:`, closure.code.substring(0, 200));

    return closure;
  }

  const cached = functionCache.get(fn);
  if (cached && !dependencies) {
    return cached;
  }

  const closure = Closure.fromFunction(fn, dependencies, isVersioned, functionName);
  functionCache.set(fn, closure);
  return closure;
}
