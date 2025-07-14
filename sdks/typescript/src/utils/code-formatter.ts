/**
 * Code formatter utilities
 */

/**
 * Format minified JavaScript code to be more readable
 * This is a simple formatter that preserves the original code structure
 */
export function formatCode(code: string): string {
  // For versioned functions, we need to preserve the exact function code
  // Don't apply any formatting that might break the code structure
  return code.trim();
}
