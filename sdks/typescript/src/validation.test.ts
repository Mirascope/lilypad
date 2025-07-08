import { describe, it, expect } from 'vitest';
import {
  validateAttributeValue,
  sanitizeErrorMessage,
  validateSpanName,
  checkAttributeCount,
  validateMetadataSize,
} from './utils/validation';
import { SPAN_LIMITS } from './types/span';

describe('Validation Utils', () => {
  describe('validateAttributeValue', () => {
    it('should pass through primitive values', () => {
      expect(validateAttributeValue('string')).toBe('string');
      expect(validateAttributeValue(123)).toBe(123);
      expect(validateAttributeValue(true)).toBe(true);
    });

    it('should truncate long strings', () => {
      const longString = 'a'.repeat(SPAN_LIMITS.MAX_ATTRIBUTE_VALUE_LENGTH + 100);
      const result = validateAttributeValue(longString);
      expect(result).toHaveLength(SPAN_LIMITS.MAX_ATTRIBUTE_VALUE_LENGTH + '...[truncated]'.length);
      expect(result.endsWith('...[truncated]')).toBe(true);
    });

    it('should handle arrays of primitives', () => {
      expect(validateAttributeValue([1, 2, 3])).toEqual([1, 2, 3]);
      expect(validateAttributeValue(['a', 'b', 'c'])).toEqual(['a', 'b', 'c']);
      expect(validateAttributeValue([true, false])).toEqual([true, false]);
    });

    it('should convert non-primitive array elements to strings', () => {
      expect(validateAttributeValue([1, { obj: true }, 'string'])).toEqual([
        1,
        '[object Object]',
        'string',
      ]);
    });

    it('should convert null and undefined to strings', () => {
      expect(validateAttributeValue(null)).toBe('null');
      expect(validateAttributeValue(undefined)).toBe('undefined');
    });

    it('should serialize complex objects', () => {
      const obj = { key: 'value', nested: { data: true } };
      expect(validateAttributeValue(obj)).toBe(JSON.stringify(obj));
    });
  });

  describe('sanitizeErrorMessage', () => {
    it('should redact API keys', () => {
      expect(sanitizeErrorMessage('Error with api_key=abc123')).toBe('Error with [REDACTED]');
      expect(sanitizeErrorMessage('api-key: "xyz789"')).toBe('[REDACTED]');
      expect(sanitizeErrorMessage('API_KEY="secret"')).toBe('[REDACTED]');
    });

    it('should redact passwords', () => {
      expect(sanitizeErrorMessage('password: mysecret')).toBe('[REDACTED]');
      expect(sanitizeErrorMessage('password="12345"')).toBe('[REDACTED]');
    });

    it('should redact tokens', () => {
      expect(sanitizeErrorMessage('token: abc123')).toBe('[REDACTED]');
      expect(sanitizeErrorMessage('bearer xyz789')).toBe('[REDACTED]');
    });

    it('should redact AWS credentials', () => {
      expect(sanitizeErrorMessage('aws_access_key_id=AKIA123')).toBe('[REDACTED]');
      expect(sanitizeErrorMessage('aws-secret-access-key: secret')).toBe('[REDACTED]');
    });

    it('should redact database URLs', () => {
      expect(sanitizeErrorMessage('postgres://user:pass@host/db')).toBe('[REDACTED]');
      expect(sanitizeErrorMessage('mysql://admin:secret@localhost')).toBe('[REDACTED]');
      expect(sanitizeErrorMessage('mongodb://user:pwd@cluster.net')).toBe('[REDACTED]');
    });

    it('should handle multiple sensitive values', () => {
      const message = 'Error: api_key=123, password=secret, token=xyz';
      const sanitized = sanitizeErrorMessage(message);
      // Password pattern captures until space, so it gets "password=secret,"
      expect(sanitized).toBe('Error: [REDACTED], [REDACTED] [REDACTED]');
    });

    it('should preserve non-sensitive content', () => {
      expect(sanitizeErrorMessage('Normal error message')).toBe('Normal error message');
    });
  });

  describe('validateSpanName', () => {
    it('should accept valid span names', () => {
      expect(validateSpanName('valid-span')).toBe('valid-span');
      expect(validateSpanName('span.with.dots')).toBe('span.with.dots');
      expect(validateSpanName('span_with_underscores')).toBe('span_with_underscores');
    });

    it('should trim whitespace', () => {
      expect(validateSpanName('  trimmed  ')).toBe('trimmed');
    });

    it('should throw on empty names', () => {
      expect(() => validateSpanName('')).toThrow('Span name must be a non-empty string');
      expect(() => validateSpanName('   ')).toThrow('Span name cannot be empty');
    });

    it('should throw on invalid types', () => {
      expect(() => validateSpanName(null as unknown as string)).toThrow(
        'Span name must be a non-empty string',
      );
      expect(() => validateSpanName(123 as unknown as string)).toThrow(
        'Span name must be a non-empty string',
      );
    });

    it('should truncate long names', () => {
      const longName = 'a'.repeat(600);
      const result = validateSpanName(longName);
      expect(result).toHaveLength(512);
    });
  });

  describe('checkAttributeCount', () => {
    it('should return true when under limit', () => {
      expect(checkAttributeCount(0)).toBe(true);
      expect(checkAttributeCount(50)).toBe(true);
      expect(checkAttributeCount(SPAN_LIMITS.MAX_ATTRIBUTES_COUNT - 1)).toBe(true);
    });

    it('should return false when at or over limit', () => {
      expect(checkAttributeCount(SPAN_LIMITS.MAX_ATTRIBUTES_COUNT)).toBe(false);
      expect(checkAttributeCount(SPAN_LIMITS.MAX_ATTRIBUTES_COUNT + 1)).toBe(false);
    });
  });

  describe('validateMetadataSize', () => {
    it('should accept small metadata', () => {
      expect(validateMetadataSize({ key: 'value' })).toBe(true);
      expect(validateMetadataSize(['array', 'data'])).toBe(true);
    });

    it('should reject large metadata', () => {
      // Create object larger than 100KB
      // Use a much larger object to ensure it exceeds the limit
      const hugeObject: Record<string, string> = {};
      for (let i = 0; i < 1000; i++) {
        hugeObject[`key${i}`] = 'x'.repeat(1000);
      }
      const result = validateMetadataSize(hugeObject);
      expect(result).toBe(false);
    });
  });
});
