/**
 * Context managers for distributed tracing.
 *
 * This module provides context managers for handling trace context propagation
 * in special cases where automatic instrumentation is not sufficient.
 */

import { Context, context as otelContext, SpanStatusCode, ROOT_CONTEXT } from '@opentelemetry/api';
import { extractContext } from './utils/context-propagation';
import { Span } from './span';

/**
 * Options for propagated context
 */
export interface PropagatedContextOptions {
  /**
   * Parent context to attach (for cross-thread/async propagation)
   */
  parent?: Context;

  /**
   * Carrier dict to extract context from (e.g., HTTP headers, message headers)
   */
  extractFrom?: Record<string, unknown>;
}

/**
 * Context manager for OpenTelemetry trace context propagation.
 *
 * This function allows you to propagate trace context across service boundaries
 * or async boundaries where automatic propagation doesn't work.
 *
 * @param options - Options for context propagation
 * @param fn - Function to execute with the propagated context
 * @returns The result of the function
 *
 * @example
 * Extract from HTTP request headers:
 * ```ts
 * import { propagatedContext } from '@lilypad/sdk';
 *
 * app.post('/api/process', async (req, res) => {
 *   await propagatedContext(
 *     { extractFrom: req.headers },
 *     async () => {
 *       // Any traced functions called here will be children of the incoming trace
 *       const result = await processData(req.body);
 *       res.json(result);
 *     }
 *   );
 * });
 * ```
 *
 * Cross-thread/async propagation:
 * ```ts
 * import { propagatedContext } from '@lilypad/sdk';
 * import { context } from '@opentelemetry/api';
 *
 * // In main thread
 * const parentCtx = context.active();
 *
 * // In worker thread or async callback
 * await propagatedContext(
 *   { parent: parentCtx },
 *   async () => {
 *     // This will be a child of the parent context
 *     await processInWorker(data);
 *   }
 * );
 * ```
 *
 * Extract from message queue headers:
 * ```ts
 * consumer.on('message', async (message) => {
 *   await propagatedContext(
 *     { extractFrom: message.headers },
 *     async () => {
 *       await handleMessage(message.data);
 *     }
 *   );
 * });
 * ```
 */
export async function propagatedContext<T>(
  options: PropagatedContextOptions,
  fn: () => Promise<T>,
): Promise<T> {
  const { parent, extractFrom } = options;

  if (parent && extractFrom) {
    throw new Error('Cannot specify both parent and extractFrom');
  }

  let ctx: Context;

  if (extractFrom) {
    // Extract context from carrier
    ctx = extractContext(extractFrom);
  } else if (parent) {
    // Use explicitly provided parent context
    ctx = parent;
  } else {
    // No context to attach - use current context
    ctx = otelContext.active();
  }

  // Run the function with the context
  return await otelContext.with(ctx, fn);
}

/**
 * Synchronous version of propagatedContext for non-async functions
 *
 * @param options - Options for context propagation
 * @param fn - Function to execute with the propagated context
 * @returns The result of the function
 *
 * @example
 * ```ts
 * import { propagatedContextSync } from '@lilypad/sdk';
 *
 * const result = propagatedContextSync(
 *   { extractFrom: headers },
 *   () => {
 *     // Synchronous traced operations
 *     return processDataSync(data);
 *   }
 * );
 * ```
 */
export function propagatedContextSync<T>(options: PropagatedContextOptions, fn: () => T): T {
  const { parent, extractFrom } = options;

  if (parent && extractFrom) {
    throw new Error('Cannot specify both parent and extractFrom');
  }

  let ctx: Context;

  if (extractFrom) {
    // Extract context from carrier
    ctx = extractContext(extractFrom);
  } else if (parent) {
    // Use explicitly provided parent context
    ctx = parent;
  } else {
    // No context to attach - use current context
    ctx = otelContext.active();
  }

  // Run the function with the context
  return otelContext.with(ctx, fn);
}

/**
 * Get the current active context
 *
 * @returns The current OpenTelemetry context
 *
 * @example
 * ```ts
 * import { getCurrentContext } from '@lilypad/sdk';
 *
 * // Save context for later use
 * const ctx = getCurrentContext();
 *
 * // Later, in another async operation
 * await propagatedContext({ parent: ctx }, async () => {
 *   // Operations here will be children of the saved context
 * });
 * ```
 */
export function getCurrentContext(): Context {
  return otelContext.active();
}

/**
 * Create a detached span that is not linked to the current trace.
 * Useful for background operations that shouldn't be part of the main trace.
 *
 * @param name - Name of the span
 * @param fn - Function to execute in the detached context
 * @returns The result of the function
 *
 * @example
 * ```ts
 * import { detachedSpan } from '@lilypad/sdk';
 *
 * // This span won't be a child of any current trace
 * const result = await detachedSpan('background-cleanup', async (span) => {
 *   span.metadata({ 'cleanup.type': 'daily' });
 *   await cleanupOldData();
 *   return { cleaned: 100 };
 * });
 * ```
 */
export async function detachedSpan<T>(name: string, fn: (span: Span) => Promise<T>): Promise<T> {
  // Create a new root context (not linked to current trace)
  return await otelContext.with(ROOT_CONTEXT, async () => {
    // Create a Lilypad Span in the detached context
    const span = new Span(name);

    if (!span.opentelemetry_span || !span.context) {
      // If span creation failed, run the function without a span
      return await fn(span);
    }

    try {
      // Run the function with the span's context
      return await otelContext.with(span.context, () => fn(span));
    } catch (error) {
      if (span.opentelemetry_span) {
        span.opentelemetry_span.recordException(error as Error);
        span.opentelemetry_span.setStatus({ code: SpanStatusCode.ERROR });
      }
      throw error;
    } finally {
      span.finish();
    }
  });
}
