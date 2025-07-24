import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  validateAttributeValue,
  sanitizeErrorMessage,
  validateSpanName,
  checkAttributeCount,
  validateMetadataSize,
} from './validation';
import { logger } from './logger';
import { SPAN_LIMITS } from '../types/span';

vi.mock('./logger', () => ({
  logger: {
    warn: vi.fn(),
    error: vi.fn(),
  },
}));

describe('validation utilities', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('validateAttributeValue', () => {
    it('should return string values as-is if within length limit', () => {
      const value = 'test string';
      expect(validateAttributeValue(value)).toBe(value);
      expect(logger.warn).not.toHaveBeenCalled();
    });

    it('should truncate long strings', () => {
      const longString = 'a'.repeat(SPAN_LIMITS.MAX_ATTRIBUTE_VALUE_LENGTH + 100);
      const result = validateAttributeValue(longString);

      expect(result).toHaveLength(SPAN_LIMITS.MAX_ATTRIBUTE_VALUE_LENGTH + 14); // + '...[truncated]'
      expect(result.endsWith('...[truncated]')).toBe(true);
      expect(logger.warn).toHaveBeenCalledWith(
        expect.stringContaining('Attribute value truncated'),
      );
    });

    it('should return number values as-is', () => {
      expect(validateAttributeValue(42)).toBe(42);
      expect(validateAttributeValue(3.14)).toBe(3.14);
      expect(validateAttributeValue(0)).toBe(0);
      expect(validateAttributeValue(-10)).toBe(-10);
    });

    it('should return boolean values as-is', () => {
      expect(validateAttributeValue(true)).toBe(true);
      expect(validateAttributeValue(false)).toBe(false);
    });

    it('should handle arrays of primitives', () => {
      const array = ['string', 42, true];
      const result = validateAttributeValue(array);
      expect(result).toEqual(['string', 42, true]);
    });

    it('should convert non-primitive array items to strings', () => {
      const array = ['string', { obj: true }, null, undefined];
      const result = validateAttributeValue(array);
      expect(result).toEqual(['string', '[object Object]', 'null', 'undefined']);
    });

    it('should convert null to string', () => {
      expect(validateAttributeValue(null)).toBe('null');
    });

    it('should convert undefined to string', () => {
      expect(validateAttributeValue(undefined)).toBe('undefined');
    });

    it('should serialize objects to JSON', () => {
      const obj = { key: 'value', nested: { data: true } };
      const result = validateAttributeValue(obj);
      expect(result).toBe('{"key":"value","nested":{"data":true}}');
    });

    it('should truncate large serialized objects', () => {
      const largeObj = {
        data: 'x'.repeat(SPAN_LIMITS.MAX_ATTRIBUTE_VALUE_LENGTH),
      };
      const result = validateAttributeValue(largeObj);

      expect(result).toHaveLength(SPAN_LIMITS.MAX_ATTRIBUTE_VALUE_LENGTH + 14);
      expect(result.endsWith('...[truncated]')).toBe(true);
      expect(logger.warn).toHaveBeenCalled();
    });
  });

  describe('sanitizeErrorMessage', () => {
    it('should redact API keys', () => {
      const messages = [
        'Error with api_key=12345',
        'Failed: api-key: "secret123"',
        'apiKey=abcdef',
        'API_KEY:xyz789',
      ];

      messages.forEach((msg) => {
        expect(sanitizeErrorMessage(msg)).not.toContain('12345');
        expect(sanitizeErrorMessage(msg)).not.toContain('secret123');
        expect(sanitizeErrorMessage(msg)).not.toContain('abcdef');
        expect(sanitizeErrorMessage(msg)).not.toContain('xyz789');
        expect(sanitizeErrorMessage(msg)).toContain('[REDACTED]');
      });
    });

    it('should redact passwords', () => {
      const messages = [
        // gitguardian:ignore
        'Login failed password=mysecret',
        // gitguardian:ignore
        'password: "p@ssw0rd"',
        // gitguardian:ignore
        'PASSWORD="admin123"',
      ];

      messages.forEach((msg) => {
        expect(sanitizeErrorMessage(msg)).not.toContain('mysecret');
        expect(sanitizeErrorMessage(msg)).not.toContain('p@ssw0rd');
        expect(sanitizeErrorMessage(msg)).not.toContain('admin123');
        expect(sanitizeErrorMessage(msg)).toContain('[REDACTED]');
      });
    });

    it('should redact tokens', () => {
      const messages = [
        // gitguardian:ignore
        'Invalid token=abc123def',
        // gitguardian:ignore
        'Authorization failed: token: "xyz789"',
        // gitguardian:ignore
        'bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9',
      ];

      messages.forEach((msg) => {
        expect(sanitizeErrorMessage(msg)).not.toContain('abc123def');
        expect(sanitizeErrorMessage(msg)).not.toContain('xyz789');
        expect(sanitizeErrorMessage(msg)).not.toContain('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9');
        expect(sanitizeErrorMessage(msg)).toContain('[REDACTED]');
      });
    });

    it('should redact AWS credentials', () => {
      const messages = [
        'aws_access_key_id=AKIAIOSFODNN7EXAMPLE',
        'aws-secret-access-key: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"',
        'AWS_SECRET_ACCESS_KEY=mysecret',
      ];

      messages.forEach((msg) => {
        expect(sanitizeErrorMessage(msg)).not.toContain('AKIAIOSFODNN7EXAMPLE');
        expect(sanitizeErrorMessage(msg)).not.toContain('wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY');
        expect(sanitizeErrorMessage(msg)).not.toContain('mysecret');
        expect(sanitizeErrorMessage(msg)).toContain('[REDACTED]');
      });
    });

    it('should redact database URLs', () => {
      const messages = [
        'Failed to connect: postgres://user:pass@localhost:5432/dbname',
        'mysql://admin:secret@db.example.com/mydb',
        'mongodb://user:password@cluster0.mongodb.net/test?retryWrites=true',
      ];

      messages.forEach((msg) => {
        expect(sanitizeErrorMessage(msg)).not.toContain('user:pass');
        expect(sanitizeErrorMessage(msg)).not.toContain('admin:secret');
        expect(sanitizeErrorMessage(msg)).not.toContain('user:password');
        expect(sanitizeErrorMessage(msg)).toContain('[REDACTED]');
      });
    });

    it('should handle multiple sensitive items in one message', () => {
      const message = 'Error: api_key=12345, password=secret, token=abc123';
      const sanitized = sanitizeErrorMessage(message);

      expect(sanitized).toBe('Error: [REDACTED], [REDACTED] [REDACTED]');
    });

    it('should preserve non-sensitive content', () => {
      const message = 'Normal error message without sensitive data';
      expect(sanitizeErrorMessage(message)).toBe(message);
    });
  });

  describe('validateSpanName', () => {
    it('should accept valid span names', () => {
      expect(validateSpanName('my-span')).toBe('my-span');
      expect(validateSpanName('MyService.method')).toBe('MyService.method');
      expect(validateSpanName('HTTP GET /api/users')).toBe('HTTP GET /api/users');
    });

    it('should trim whitespace', () => {
      expect(validateSpanName('  my-span  ')).toBe('my-span');
      expect(validateSpanName('\n\tspan\n\t')).toBe('span');
    });

    it('should throw for non-string values', () => {
      expect(() => validateSpanName(null as any)).toThrow('Span name must be a non-empty string');
      expect(() => validateSpanName(undefined as any)).toThrow(
        'Span name must be a non-empty string',
      );
      expect(() => validateSpanName(123 as any)).toThrow('Span name must be a non-empty string');
      expect(() => validateSpanName({} as any)).toThrow('Span name must be a non-empty string');
    });

    it('should throw for empty string', () => {
      expect(() => validateSpanName('')).toThrow('Span name must be a non-empty string');
      expect(() => validateSpanName('   ')).toThrow('Span name cannot be empty');
    });

    it('should truncate long span names', () => {
      const longName = 'a'.repeat(600);
      const result = validateSpanName(longName);

      expect(result).toHaveLength(512);
      expect(result).toBe('a'.repeat(512));
      expect(logger.warn).toHaveBeenCalledWith(expect.stringContaining('Span name truncated'));
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
      expect(checkAttributeCount(1000)).toBe(false);
    });
  });

  describe('validateMetadataSize', () => {
    it('should return true for small metadata', () => {
      const metadata = { key: 'value', data: [1, 2, 3] };
      expect(validateMetadataSize(metadata)).toBe(true);
      expect(logger.error).not.toHaveBeenCalled();
    });

    it('should return false for metadata exceeding 100KB', () => {
      // Create object larger than 100KB
      const largeData = 'x'.repeat(110 * 1024);
      const metadata = { data: largeData };

      expect(validateMetadataSize(metadata)).toBe(false);
      expect(logger.error).toHaveBeenCalledWith(
        expect.stringMatching(/Metadata too large: \d+ bytes > 102400 bytes/),
      );
    });

    it('should handle various metadata types', () => {
      expect(validateMetadataSize('string')).toBe(true);
      expect(validateMetadataSize(123)).toBe(true);
      expect(validateMetadataSize(true)).toBe(true);
      expect(validateMetadataSize(null)).toBe(true);
      expect(validateMetadataSize(undefined)).toBe(true);
      expect(validateMetadataSize([])).toBe(true);
    });

    it('should handle metadata at the size boundary', () => {
      // Create object close to 100KB
      const data = 'x'.repeat(100 * 1024 - 100); // Just under limit
      const metadata = { data };

      expect(validateMetadataSize(metadata)).toBe(true);
      expect(logger.error).not.toHaveBeenCalled();
    });
  });
});
