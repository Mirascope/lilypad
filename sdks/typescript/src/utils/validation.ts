import { logger } from './logger';
import { safeStringify } from './json';
import type { SpanAttributesValue, SpanAttributeArray } from '../types/span';

// Import the actual constants
import { SPAN_LIMITS as LIMITS } from '../types/span';

/**
 * Validate and normalize attribute values for OpenTelemetry spans
 */
export function validateAttributeValue(value: unknown): SpanAttributesValue | string {
  // Primitive types are valid as-is
  if (typeof value === 'string') {
    // Check string length
    if (value.length > LIMITS.MAX_ATTRIBUTE_VALUE_LENGTH) {
      logger.warn(
        `Attribute value truncated: ${value.length} > ${LIMITS.MAX_ATTRIBUTE_VALUE_LENGTH}`,
      );
      return value.substring(0, LIMITS.MAX_ATTRIBUTE_VALUE_LENGTH) + '...[truncated]';
    }
    return value;
  }

  if (typeof value === 'number' || typeof value === 'boolean') {
    return value;
  }

  // Arrays of primitives
  if (Array.isArray(value)) {
    const validArray: SpanAttributeArray = [];
    for (const item of value) {
      if (typeof item === 'string' || typeof item === 'number' || typeof item === 'boolean') {
        validArray.push(item);
      } else {
        // Convert non-primitive to string
        validArray.push(String(item));
      }
    }
    return validArray;
  }

  // null/undefined to string
  if (value === null) return 'null';
  if (value === undefined) return 'undefined';

  // Complex objects need serialization
  const serialized = safeStringify(value);

  // Size check
  if (serialized.length > LIMITS.MAX_ATTRIBUTE_VALUE_LENGTH) {
    logger.warn(
      `Attribute value truncated: ${serialized.length} > ${LIMITS.MAX_ATTRIBUTE_VALUE_LENGTH}`,
    );
    return serialized.substring(0, LIMITS.MAX_ATTRIBUTE_VALUE_LENGTH) + '...[truncated]';
  }

  return serialized;
}

/**
 * Sanitize error messages to remove sensitive information
 */
export function sanitizeErrorMessage(message: string): string {
  // Patterns for sensitive information
  const patterns = [
    // API keys
    /api[_-]?key[\s]*[:=][\s]*["']?[\w-]+["']?/gi,
    // Passwords
    /password[\s]*[:=][\s]*["']?[^"'\s]+["']?/gi,
    // Tokens
    /token[\s]*[:=][\s]*["']?[\w-]+["']?/gi,
    // Bearer tokens
    /bearer\s+[\w-]+/gi,
    // AWS credentials
    /aws[_-]?access[_-]?key[_-]?id[\s]*[:=][\s]*["']?[\w-]+["']?/gi,
    /aws[_-]?secret[_-]?access[_-]?key[\s]*[:=][\s]*["']?[\w-]+["']?/gi,
    // Database URLs - match the entire URL including path
    /(?:postgres|mysql|mongodb):\/\/[^@\s]+@[^/\s]+(?:\/[^\s]*)?/gi,
  ];

  let sanitized = message;
  patterns.forEach((pattern) => {
    sanitized = sanitized.replace(pattern, '[REDACTED]');
  });

  return sanitized;
}

/**
 * Validate span name
 */
export function validateSpanName(name: string): string {
  if (!name || typeof name !== 'string') {
    throw new Error('Span name must be a non-empty string');
  }

  // Trim and check length
  const trimmed = name.trim();
  if (trimmed.length === 0) {
    throw new Error('Span name cannot be empty');
  }

  // Limit span name length
  const MAX_SPAN_NAME_LENGTH = 512;
  if (trimmed.length > MAX_SPAN_NAME_LENGTH) {
    logger.warn(`Span name truncated: ${trimmed.length} > ${MAX_SPAN_NAME_LENGTH}`);
    return trimmed.substring(0, MAX_SPAN_NAME_LENGTH);
  }

  return trimmed;
}

/**
 * Check if attributes count exceeds limit
 */
export function checkAttributeCount(currentCount: number): boolean {
  return currentCount < LIMITS.MAX_ATTRIBUTES_COUNT;
}

/**
 * Validate metadata object size
 */
export function validateMetadataSize(metadata: unknown): boolean {
  const MAX_METADATA_SIZE = 100 * 1024; // 100KB
  const serialized = safeStringify(metadata, MAX_METADATA_SIZE + 1000); // Allow slightly more to check actual size

  if (serialized.length > MAX_METADATA_SIZE) {
    logger.error(`Metadata too large: ${serialized.length} bytes > ${MAX_METADATA_SIZE} bytes`);
    return false;
  }

  return true;
}
