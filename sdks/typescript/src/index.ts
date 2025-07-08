/**
 * Lilypad TypeScript SDK
 *
 * LLM observability and monitoring for TypeScript/JavaScript applications
 */

import { configure, getTracer } from './configure';
import { shutdown } from './shutdown';
import { logger } from './utils/logger';
import { Span, span, syncSpan } from './span';
import { session, sessionAsync, getCurrentSession, withSession, withSessionAsync } from './session';

export { configure, getTracerProvider, getTracer } from './configure';
export { shutdown } from './shutdown';
export { logger } from './utils/logger';
export { Span, span, syncSpan } from './span';
export { session, sessionAsync, getCurrentSession, withSession, withSessionAsync } from './session';
export type { LilypadConfig, LogLevel } from './types';
export type { Session } from './session';

const lilypad = {
  configure,
  shutdown,
  getTracer,
  logger,
  // New span functionality
  Span,
  span,
  syncSpan,
  // Session functionality
  session,
  sessionAsync,
  getCurrentSession,
  withSession,
  withSessionAsync,
};

export default lilypad;
