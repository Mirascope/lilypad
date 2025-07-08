/**
 * Lilypad TypeScript SDK
 *
 * LLM observability and monitoring for TypeScript/JavaScript applications
 */

import { configure, getTracerProvider, getTracer } from './configure';
import { shutdown } from './shutdown';
import { traceOpenAICompletion, createSpan, getActiveSpan, withSpan } from './trace';
import { logger } from './utils/logger';

export { configure, getTracerProvider, getTracer } from './configure';
export { shutdown } from './shutdown';
export { traceOpenAICompletion, createSpan, getActiveSpan, withSpan } from './trace';
export { logger } from './utils/logger';
export type { LilypadConfig, LogLevel } from './types';

const lilypad = {
  configure,
  shutdown,
  traceOpenAICompletion,
  createSpan,
  getActiveSpan,
  withSpan,
  getTracerProvider,
  getTracer,
  logger,
};

export default lilypad;
