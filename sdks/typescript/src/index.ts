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
import { trace, Trace, AsyncTrace } from './trace';

export { configure, getTracerProvider, getTracer } from './configure';
export { shutdown } from './shutdown';
export { logger } from './utils/logger';
export { Span, span, syncSpan } from './span';
export { session, sessionAsync, getCurrentSession, withSession, withSessionAsync } from './session';
export { wrapOpenAI } from './wrap-openai';
export { wrapAnthropic } from './wrap-anthropic';
export { wrapGoogle } from './wrap-google';
export { trace, Trace, AsyncTrace, getCurrentSpan, logToCurrentSpan, wrapWithTrace } from './trace';
export { trace as lilypad } from './trace';
export type { LilypadConfig, LogLevel } from './types';
export type { Session } from './session';
export type { TraceOptions } from './trace';

// Versioning-related exports removed - TypeScript extraction happens at build time

const lilypad = {
  configure,
  shutdown,
  getTracer,
  logger,
  Span,
  span,
  syncSpan,
  session,
  sessionAsync,
  getCurrentSession,
  withSession,
  withSessionAsync,
  trace,
  Trace,
  AsyncTrace,
};

export default lilypad;
