import { describe, it, expect, vi, beforeEach } from 'vitest';
import { INVALID_SPANID, INVALID_TRACEID } from '@opentelemetry/api';
import { randomBytes } from 'crypto';
import { CryptoIdGenerator } from './id-generator';

vi.mock('crypto', () => ({
  randomBytes: vi.fn(),
}));

describe('CryptoIdGenerator', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });
  it('should generate valid trace id', () => {
    const mockHex = '1234567890abcdef1234567890abcdef';
    vi.mocked(randomBytes).mockReturnValue({
      toString: vi.fn().mockReturnValue(mockHex),
    } as any);

    const generator = new CryptoIdGenerator();
    const traceId = generator.generateTraceId();

    expect(randomBytes).toHaveBeenCalledWith(16);
    expect(traceId).toBe(mockHex);
  });

  it('should generate valid span id', () => {
    const mockHex = '1234567890abcdef';
    vi.mocked(randomBytes).mockReturnValue({
      toString: vi.fn().mockReturnValue(mockHex),
    } as any);

    const generator = new CryptoIdGenerator();
    const spanId = generator.generateSpanId();

    expect(randomBytes).toHaveBeenCalledWith(8);
    expect(spanId).toBe(mockHex);
  });

  it('should regenerate trace id if invalid', () => {
    const validHex = '1234567890abcdef1234567890abcdef';
    vi.mocked(randomBytes)
      .mockReturnValueOnce({
        toString: vi.fn().mockReturnValue(INVALID_TRACEID),
      } as any)
      .mockReturnValueOnce({
        toString: vi.fn().mockReturnValue(validHex),
      } as any);

    const generator = new CryptoIdGenerator();
    const traceId = generator.generateTraceId();

    expect(randomBytes).toHaveBeenCalledTimes(2);
    expect(traceId).toBe(validHex);
    expect(traceId).not.toBe(INVALID_TRACEID);
  });

  it('should regenerate span id if invalid', () => {
    const validHex = '1234567890abcdef';
    vi.mocked(randomBytes)
      .mockReturnValueOnce({
        toString: vi.fn().mockReturnValue(INVALID_SPANID),
      } as any)
      .mockReturnValueOnce({
        toString: vi.fn().mockReturnValue(validHex),
      } as any);

    const generator = new CryptoIdGenerator();
    const spanId = generator.generateSpanId();

    expect(randomBytes).toHaveBeenCalledTimes(2);
    expect(spanId).toBe(validHex);
    expect(spanId).not.toBe(INVALID_SPANID);
  });

  it('should generate different ids on each call', () => {
    let callCount = 0;
    const hexValues = [
      '1234567890abcdef1234567890abcdef',
      'fedcba0987654321fedcba0987654321',
      'abcdef1234567890abcdef1234567890',
    ];

    vi.mocked(randomBytes).mockImplementation(
      () =>
        ({
          toString: vi.fn().mockReturnValue(hexValues[callCount++]),
        }) as any
    );

    const generator = new CryptoIdGenerator();
    const traceId1 = generator.generateTraceId();
    const traceId2 = generator.generateTraceId();
    const traceId3 = generator.generateTraceId();

    expect(traceId1).not.toBe(traceId2);
    expect(traceId2).not.toBe(traceId3);
    expect(traceId1).not.toBe(traceId3);
  });
});
