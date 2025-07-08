/**
 * Lilypad TypeScript SDK
 *
 * LLM observability and monitoring for TypeScript/JavaScript applications
 */

import { configure, getTracer } from './configure';
import { shutdown } from './shutdown';
import { logger } from './utils/logger';

export { configure, getTracerProvider, getTracer } from './configure';
export { shutdown } from './shutdown';
export { logger } from './utils/logger';
export type { LilypadConfig, LogLevel } from './types';

const lilypad = {
  configure,
  shutdown,
  getTracer,
  logger,
};

export default lilypad;
