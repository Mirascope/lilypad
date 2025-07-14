/**
 * Code formatter utilities
 */

/**
 * Format minified JavaScript code to be more readable
 * This is a simple formatter that preserves the original code structure
 */
export function formatCode(code: string): string {
  // For TypeScript/JavaScript, the compiled code is often minified
  // We'll keep it as-is since we don't have access to the original source
  // In production, you might want to use source maps or AST parsing

  // For now, just ensure consistent formatting of common patterns
  let formatted = code;

  // Add spaces around operators for readability
  formatted = formatted.replace(/([=+\-*/<>!]+)/g, ' $1 ');

  // Clean up extra spaces
  formatted = formatted.replace(/\s+/g, ' ');

  // Preserve the minified format but make it slightly more readable
  formatted = formatted.trim();

  return formatted;
}
