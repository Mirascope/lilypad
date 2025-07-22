import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('crypto', () => ({
  randomBytes: vi.fn(),
}));

import { CryptoIdGenerator } from './id-generator';
import { INVALID_SPANID, INVALID_TRACEID } from '@opentelemetry/api';
import { randomBytes } from 'crypto';

describe('CryptoIdGenerator', () => {
  const generator = new CryptoIdGenerator();

  beforeEach(() => {
    vi.clearAllMocks();
    // Reset mock to normal behavior
    vi.mocked(randomBytes).mockImplementation((size: number) => {
      // Generate actual random bytes for most tests
      const bytes = Buffer.alloc(size);
      for (let i = 0; i < size; i++) {
        bytes[i] = Math.floor(Math.random() * 256);
      }
      return bytes;
    });
  });

  describe('generateSpanId', () => {
    it('should generate valid span IDs', () => {
      const spanId = generator.generateSpanId();
      expect(spanId).toHaveLength(16); // 8 bytes = 16 hex chars
      expect(spanId).toMatch(/^[0-9a-f]{16}$/);
    });

    it('should never generate INVALID_SPANID', () => {
      // Generate many IDs to ensure we never get invalid ones
      for (let i = 0; i < 100; i++) {
        const spanId = generator.generateSpanId();
        expect(spanId).not.toBe(INVALID_SPANID);
      }
    });

    it('should generate unique span IDs', () => {
      const ids = new Set();
      for (let i = 0; i < 100; i++) {
        ids.add(generator.generateSpanId());
      }
      expect(ids.size).toBe(100);
    });

    it('should retry when generating INVALID_SPANID', () => {
      // Mock to return invalid ID first, then valid ID
      const invalidBuffer = Buffer.from(INVALID_SPANID, 'hex');
      const validBuffer = Buffer.from('1234567890abcdef', 'hex');

      vi.mocked(randomBytes).mockReturnValueOnce(invalidBuffer).mockReturnValueOnce(validBuffer);

      const spanId = generator.generateSpanId();

      expect(spanId).toBe('1234567890abcdef');
      expect(randomBytes).toHaveBeenCalledTimes(2);
    });
  });

  describe('generateTraceId', () => {
    it('should generate valid trace IDs', () => {
      const traceId = generator.generateTraceId();
      expect(traceId).toHaveLength(32); // 16 bytes = 32 hex chars
      expect(traceId).toMatch(/^[0-9a-f]{32}$/);
    });

    it('should never generate INVALID_TRACEID', () => {
      // Generate many IDs to ensure we never get invalid ones
      for (let i = 0; i < 100; i++) {
        const traceId = generator.generateTraceId();
        expect(traceId).not.toBe(INVALID_TRACEID);
      }
    });

    it('should generate unique trace IDs', () => {
      const ids = new Set();
      for (let i = 0; i < 100; i++) {
        ids.add(generator.generateTraceId());
      }
      expect(ids.size).toBe(100);
    });

    it('should retry when generating INVALID_TRACEID', () => {
      // Mock to return invalid ID first, then valid ID
      const invalidBuffer = Buffer.from(INVALID_TRACEID, 'hex');
      const validBuffer = Buffer.from('1234567890abcdef1234567890abcdef', 'hex');

      vi.mocked(randomBytes).mockReturnValueOnce(invalidBuffer).mockReturnValueOnce(validBuffer);

      const traceId = generator.generateTraceId();

      expect(traceId).toBe('1234567890abcdef1234567890abcdef');
      expect(randomBytes).toHaveBeenCalledTimes(2);
    });
  });

  it('should implement IdGenerator interface', () => {
    expect(generator).toHaveProperty('generateSpanId');
    expect(generator).toHaveProperty('generateTraceId');
    expect(typeof generator.generateSpanId).toBe('function');
    expect(typeof generator.generateTraceId).toBe('function');
  });
});
