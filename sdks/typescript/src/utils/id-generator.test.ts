import { describe, it, expect } from 'vitest';
import { CryptoIdGenerator } from './id-generator';
import { INVALID_SPANID, INVALID_TRACEID } from '@opentelemetry/api';

describe('CryptoIdGenerator', () => {
  const generator = new CryptoIdGenerator();

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
  });

  it('should implement IdGenerator interface', () => {
    expect(generator).toHaveProperty('generateSpanId');
    expect(generator).toHaveProperty('generateTraceId');
    expect(typeof generator.generateSpanId).toBe('function');
    expect(typeof generator.generateTraceId).toBe('function');
  });
});
