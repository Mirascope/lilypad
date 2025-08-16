import { INVALID_SPANID, INVALID_TRACEID } from '@opentelemetry/api';
import type { IdGenerator } from '@opentelemetry/sdk-trace-base';
import { randomBytes } from 'crypto';

export class CryptoIdGenerator implements IdGenerator {
  generateTraceId(): string {
    let id: string;
    do {
      id = randomBytes(16).toString('hex');
    } while (id === INVALID_TRACEID);
    return id;
  }

  generateSpanId(): string {
    let id: string;
    do {
      id = randomBytes(8).toString('hex');
    } while (id === INVALID_SPANID);
    return id;
  }
}
