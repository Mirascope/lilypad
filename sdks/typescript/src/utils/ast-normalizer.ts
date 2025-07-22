/**
 * AST normalization for consistent function hashing
 */

import * as crypto from 'crypto';
import * as acorn from 'acorn';
import * as walk from 'acorn-walk';

export interface NormalizedFunction {
  signature: string;
  normalizedCode: string;
}

/**
 * Normalize a function's code for consistent hashing
 * This removes formatting differences and normalizes variable names
 */
export function normalizeFunction(code: string): NormalizedFunction {
  try {
    // Parse the function code
    const ast = acorn.parse(code, {
      ecmaVersion: 'latest',
      sourceType: 'module',
      allowReturnOutsideFunction: true,
    });

    // Extract function signature
    let signature = 'function()';
    let normalizedCode = code;

    walk.simple(ast, {
      FunctionDeclaration(node: any) {
        signature = extractSignature(node);
        normalizedCode = normalizeNode(node);
      },
      FunctionExpression(node: any) {
        signature = extractSignature(node);
        normalizedCode = normalizeNode(node);
      },
      ArrowFunctionExpression(node: any) {
        signature = extractArrowSignature(node);
        normalizedCode = normalizeNode(node);
      },
    });

    return { signature, normalizedCode };
  } catch (error) {
    // If parsing fails, return the original code
    return {
      signature: extractSimpleSignature(code),
      normalizedCode: normalizeWhitespace(code),
    };
  }
}

/**
 * Create a hash of the normalized function code
 */
export function createFunctionHash(
  normalizedCode: string,
  dependencies?: Record<string, string>,
): string {
  const hash = crypto.createHash('sha256');

  // Hash the normalized code
  hash.update(normalizedCode);

  // Hash dependencies in a consistent order
  if (dependencies) {
    const sortedDeps = Object.keys(dependencies)
      .sort()
      .map((key) => `${key}:${dependencies[key]}`)
      .join(',');
    hash.update(sortedDeps);
  }

  return hash.digest('hex');
}

/**
 * Extract function signature from AST node
 */
function extractSignature(node: any): string {
  const name = node.id?.name || 'anonymous';
  const params = node.params
    .map((p: any) => {
      if (p.type === 'Identifier') return p.name;
      if (p.type === 'RestElement') return `...${p.argument.name}`;
      if (p.type === 'AssignmentPattern') return `${p.left.name}=${p.right.raw || '...'}`;
      return '...';
    })
    .join(', ');

  const isAsync = node.async ? 'async ' : '';
  const isGenerator = node.generator ? '*' : '';

  return `${isAsync}function${isGenerator} ${name}(${params})`;
}

/**
 * Extract arrow function signature
 */
function extractArrowSignature(node: any): string {
  const params = node.params
    .map((p: any) => {
      if (p.type === 'Identifier') return p.name;
      if (p.type === 'RestElement') return `...${p.argument.name}`;
      if (p.type === 'AssignmentPattern') return `${p.left.name}=${p.right.raw || '...'}`;
      return '...';
    })
    .join(', ');

  const isAsync = node.async ? 'async ' : '';
  return `${isAsync}(${params}) =>`;
}

/**
 * Extract simple signature from code string
 */
function extractSimpleSignature(code: string): string {
  const match = code.match(/^(?:async\s+)?(?:function\s*\*?\s*)?(?:[a-zA-Z_$][\w$]*)?\s*\([^)]*\)/);
  if (match) return match[0];

  const arrowMatch = code.match(/^(?:async\s+)?\([^)]*\)\s*=>/);
  if (arrowMatch) return arrowMatch[0];

  return 'function()';
}

/**
 * Normalize AST node to string
 */
function normalizeNode(node: any): string {
  // For now, just normalize whitespace
  // In a full implementation, this would rename variables consistently
  const code = node.toString();
  return normalizeWhitespace(code);
}

/**
 * Normalize whitespace in code
 */
function normalizeWhitespace(code: string): string {
  return code
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .join('\n')
    .replace(/\s+/g, ' ')
    .trim();
}
