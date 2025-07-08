/**
 * Lilypad TypeScript SDK
 *
 * LLM observability and monitoring for TypeScript/JavaScript applications
 */

import { configure, getTracerProvider, getTracer } from './configure';
import { shutdown } from './shutdown';
import { Span, span, syncSpan } from './span';
import {
  session,
  sessionAsync,
  withSession,
  withSessionAsync,
  getCurrentSession,
  generateSessionId,
} from './session';
import { logger } from './utils/logger';

export { configure, getTracerProvider, getTracer } from './configure';
export { shutdown } from './shutdown';
export { Span, span, syncSpan } from './span';
export {
  session,
  sessionAsync,
  withSession,
  withSessionAsync,
  getCurrentSession,
  generateSessionId,
} from './session';
export { logger } from './utils/logger';
export type { LilypadConfig, LogLevel } from './types';

const lilypad = {
  configure,
  shutdown,
  Span,
  span,
  syncSpan,
  session,
  sessionAsync,
  withSession,
  withSessionAsync,
  getCurrentSession,
  generateSessionId,
  getTracerProvider,
  getTracer,
  logger,
};

export default lilypad;
