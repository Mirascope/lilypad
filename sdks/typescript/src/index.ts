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
export { trace, Trace, AsyncTrace, getCurrentSpan, logToCurrentSpan, wrapWithTrace } from './trace';
export { trace as lilypad } from './trace';
export type { LilypadConfig, LogLevel } from './types';
export type { Session } from './session';
export type { TraceOptions } from './trace';

export { isVersionedFunction, createVersionedFunctionCore } from './versioning/versioned-function';
import { getSettings } from './utils/settings';

// Export a wrapper that supports both old and new API
export function createVersionedFunction<T extends (...args: any[]) => any>(
  fn: T,
  nameOrOptions?: string | { name?: string; hash?: string; uuid?: string; dependencies?: Record<string, string> },
  projectId?: string,
  functionUuid?: string,
): import('./types/versioning').VersionedFunction<T> {
  const { createVersionedFunctionCore } = require('./versioning/versioned-function');
  const settings = getSettings();
  
  // Support both API styles
  if (typeof nameOrOptions === 'string') {
    // New API: createVersionedFunction(fn, name, projectId, functionUuid)
    return createVersionedFunctionCore(fn, nameOrOptions, projectId || settings?.projectId || '', functionUuid);
  } else {
    // Old API: createVersionedFunction(fn, options)
    const options = nameOrOptions || {};
    return createVersionedFunctionCore(
      fn,
      options.name || fn.name || 'anonymous',
      settings?.projectId || '',
      options.uuid
    );
  }
}
export type {
  VersionedFunction,
  AsyncVersionedFunction,
  VersionedFunctionMethods,
  FunctionVersion,
  VersionedTrace,
  AsyncVersionedTrace,
} from './types/versioning';

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
