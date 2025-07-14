import * as crypto from 'crypto';

export interface DependencyInfo {
  version: string;
  extras?: string[];
}

export interface ClosureData {
  name: string;
  signature: string;
  code: string;
  hash: string;
  dependencies: Record<string, DependencyInfo>;
}

// Type for any callable function - using unknown is safer than any
type AnyFunction = (...args: unknown[]) => unknown;

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
  static fromFunction(fn: AnyFunction, dependencies?: Record<string, DependencyInfo>): Closure {
    const name = getQualifiedName(fn);
    const signature = getFunctionSignature(fn);
    const code = fn.toString();

    // Generate hash from the code
    const hash = crypto
      .createHash('sha256')
      .update(code)
      .update(JSON.stringify(dependencies || {}))
      .digest('hex');

    return new Closure({
      name,
      signature,
      code,
      hash,
      dependencies: dependencies || {},
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
): Closure {
  const cached = functionCache.get(fn);
  if (cached && !dependencies) {
    return cached;
  }

  const closure = Closure.fromFunction(fn, dependencies);
  functionCache.set(fn, closure);
  return closure;
}
