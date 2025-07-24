import { randomBytes } from 'crypto';
import { INVALID_SPANID, INVALID_TRACEID } from '@opentelemetry/api';
import { IdGenerator } from '@opentelemetry/sdk-trace-base';

/**
 * Generate span/trace IDs with cryptographically secure randomness.
 */
export class CryptoIdGenerator implements IdGenerator {
  private randomInt(nBytes: number): string {
    return randomBytes(nBytes).toString('hex');
  }

  generateSpanId(): string {
    let spanId = this.randomInt(8); // 64 bits
    while (spanId === INVALID_SPANID) {
      spanId = this.randomInt(8);
    }
    return spanId;
  }

  generateTraceId(): string {
    let traceId = this.randomInt(16); // 128 bits
    while (traceId === INVALID_TRACEID) {
      traceId = this.randomInt(16);
    }
    return traceId;
  }
}
