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
import {
  propagatedContext,
  propagatedContextSync,
  getCurrentContext,
  detachedSpan,
} from './context-managers';
import { extractContext, injectContext } from './utils/context-propagation';

export { configure, getTracerProvider, getTracer } from './configure';
export { shutdown } from './shutdown';
export { logger } from './utils/logger';
export { Span, span, syncSpan } from './span';
export { session, sessionAsync, getCurrentSession, withSession, withSessionAsync } from './session';
export { wrapOpenAI } from './wrap-openai';
export { wrapAnthropic } from './wrap-anthropic';
export { wrapGoogle } from './wrap-google';
export { wrapBedrock } from './wrap-bedrock';
export { wrapAzureInference } from './wrap-azure-inference';
export { wrapMistral } from './wrap-mistral';
export { trace, Trace, AsyncTrace, getCurrentSpan, logToCurrentSpan, wrapWithTrace } from './trace';
export { trace as lilypad } from './trace';
export {
  propagatedContext,
  propagatedContextSync,
  getCurrentContext,
  detachedSpan,
} from './context-managers';
export { extractContext, injectContext } from './utils/context-propagation';
export type { LilypadConfig, LogLevel, Propagator } from './types';
export type { Session } from './session';
export type { TraceOptions } from './trace';
export type { PropagatedContextOptions } from './context-managers';

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
  propagatedContext,
  propagatedContextSync,
  getCurrentContext,
  detachedSpan,
  extractContext,
  injectContext,
};

export default lilypad;
