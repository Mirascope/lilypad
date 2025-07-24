/**
 * Safely stringify an object to JSON, handling circular references and other issues
 */
export function safeStringify(obj: unknown, maxLength = 10000): string {
  try {
    const seen = new WeakSet();
    const json = JSON.stringify(obj, (_key, value) => {
      // Handle circular references
      if (typeof value === 'object' && value !== null) {
        if (seen.has(value)) {
          return '[Circular]';
        }
        seen.add(value);
      }

      // Handle functions
      if (typeof value === 'function') {
        return '[Function]';
      }

      // Handle undefined
      if (value === undefined) {
        return '[undefined]';
      }

      return value;
    });

    // Truncate if too long
    if (json.length > maxLength) {
      return json.substring(0, maxLength) + '... [truncated]';
    }

    return json;
  } catch (error) {
    return '[Unable to stringify]';
  }
}
