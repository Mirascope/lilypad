/**
 * Context propagation utilities for distributed tracing.
 *
 * This module provides utilities for extracting and injecting trace context
 * across process boundaries using OpenTelemetry propagators.
 */

import { Context, propagation, TextMapGetter, TextMapSetter, context } from '@opentelemetry/api';
import { CompositePropagator, W3CTraceContextPropagator } from '@opentelemetry/core';
import { B3Propagator, B3InjectEncoding } from '@opentelemetry/propagator-b3';
import { JaegerPropagator } from '@opentelemetry/propagator-jaeger';
import { logger } from './logger';

import type { Propagator } from '../types';

/**
 * Get the configured propagator based on environment settings.
 *
 * Supports multiple propagation formats:
 * - tracecontext (W3C Trace Context) - default
 * - b3 (B3 Single Format)
 * - b3multi (B3 Multi Format)
 * - jaeger (Jaeger)
 * - composite (all of the above)
 *
 * @returns A configured propagator instance
 */
export function getPropagator(type?: Propagator): CompositePropagator {
  const propagatorType = (
    type ||
    process.env.LILYPAD_PROPAGATOR ||
    'tracecontext'
  ).toLowerCase() as Propagator;

  switch (propagatorType) {
    case 'b3':
      return new CompositePropagator({
        propagators: [new B3Propagator({ injectEncoding: B3InjectEncoding.SINGLE_HEADER })],
      });
    case 'b3multi':
      return new CompositePropagator({
        propagators: [new B3Propagator({ injectEncoding: B3InjectEncoding.MULTI_HEADER })],
      });
    case 'jaeger':
      return new CompositePropagator({
        propagators: [new JaegerPropagator()],
      });
    case 'composite':
      // Support all common formats
      return new CompositePropagator({
        propagators: [
          new W3CTraceContextPropagator(),
          new B3Propagator({ injectEncoding: B3InjectEncoding.SINGLE_HEADER }),
          new B3Propagator({ injectEncoding: B3InjectEncoding.MULTI_HEADER }),
          new JaegerPropagator(),
        ],
      });
    default:
      // Default to W3C Trace Context
      return new CompositePropagator({
        propagators: [new W3CTraceContextPropagator()],
      });
  }
}

/**
 * Utility class for extracting and injecting trace context.
 *
 * WARNING: This class modifies global OpenTelemetry state by calling
 * `propagation.setGlobalPropagator()`. This affects all OpenTelemetry
 * instrumentation in the current process. If you have other OpenTelemetry
 * integrations, they will use the propagator configured here.
 *
 * The propagator type can be controlled via the LILYPAD_PROPAGATOR
 * environment variable. Supported values:
 * - "tracecontext" (default): W3C Trace Context
 * - "b3": B3 Single Format
 * - "b3multi": B3 Multi Format
 * - "jaeger": Jaeger format
 * - "composite": All formats (for maximum compatibility)
 */
export class ContextPropagator {
  private propagator: CompositePropagator;

  constructor(setGlobal: boolean = true, propagatorType?: Propagator) {
    this.propagator = getPropagator(propagatorType);

    // Set the global propagator - this affects the entire process
    if (setGlobal) {
      propagation.setGlobalPropagator(this.propagator);
      logger.debug(`Set global propagator to: ${propagatorType || 'tracecontext'}`);
    }
  }

  /**
   * Extract trace context from a carrier (e.g., HTTP headers).
   *
   * @param carrier - A dictionary-like object containing trace context
   *                 (typically HTTP headers)
   * @returns The extracted context
   */
  extractContext(carrier: Record<string, unknown>): Context {
    const getter: TextMapGetter = {
      keys: (carrier) => Object.keys(carrier),
      get: (carrier, key) => {
        const value = carrier[key];
        return Array.isArray(value) ? value[0] : value;
      },
    };

    return propagation.extract(context.active(), carrier, getter);
  }

  /**
   * Inject current trace context into a carrier.
   *
   * @param carrier - A mutable mapping to inject context into
   *                 (typically HTTP headers)
   * @param context - Optional context to inject. If undefined, uses current context
   */
  injectContext(carrier: Record<string, string>, contextParam?: Context): void {
    const setter: TextMapSetter = {
      set: (carrier, key, value) => {
        carrier[key] = value;
      },
    };

    propagation.inject(contextParam || context.active(), carrier, setter);
  }

  /**
   * Extract context and attach it, returning the context and token.
   *
   * This is useful for manual context management.
   *
   * @param carrier - A dictionary-like object containing trace context
   * @returns Tuple of [extracted context, detach token]
   */
  withExtractedContext(carrier: Record<string, unknown>): [Context, (() => void) | undefined] {
    const ctx = this.extractContext(carrier);

    // We'll return a function to restore the previous context
    const restoreFn = () => {
      // This is a workaround since JS API doesn't have attach/detach
      // In practice, you would use context.with() to run code in a context
    };

    return [ctx, restoreFn];
  }

  /**
   * Detach a previously attached context.
   *
   * @param token - The restore function returned from withExtractedContext
   */
  detachContext(token: (() => void) | undefined): void {
    if (token !== undefined) {
      token();
    }
  }
}

// Global instance for convenience - created lazily
let _propagator: ContextPropagator | null = null;

/**
 * Get or create the global propagator instance.
 */
function _getPropagator(): ContextPropagator {
  if (_propagator === null) {
    // Check if we should set global propagator
    // This is controlled by whether configure() has been called
    const setGlobal = process.env._LILYPAD_PROPAGATOR_SET_GLOBAL !== 'false';
    _propagator = new ContextPropagator(setGlobal);
  }
  return _propagator;
}

/**
 * Extract trace context from a carrier (e.g., HTTP headers).
 *
 * This function extracts OpenTelemetry trace context from a carrier object,
 * typically HTTP headers received from a request. This allows distributed
 * traces to maintain parent-child relationships across service boundaries.
 *
 * @param carrier - A dictionary-like object containing trace context headers.
 *                 Typically HTTP headers from an incoming request.
 * @returns An OpenTelemetry Context object containing the extracted trace information.
 *
 * @example
 * Basic usage in an Express handler:
 * ```ts
 * import express from 'express';
 * import { trace } from '@lilypad/sdk';
 * import { extractContext } from '@lilypad/sdk/utils/context-propagation';
 *
 * const app = express();
 *
 * app.post('/process', async (req, res) => {
 *   // Extract trace context from incoming request headers
 *   const context = extractContext(req.headers);
 *
 *   // Use the extracted context in a traced function
 *   const processData = trace(async (data: any) => {
 *     // This span will be a child of the incoming trace
 *     const result = await doProcessing(data);
 *     return result;
 *   });
 *
 *   const result = await processData(req.body);
 *   res.json(result);
 * });
 * ```
 */
export function extractContext(carrier: Record<string, unknown>): Context {
  return _getPropagator().extractContext(carrier);
}

/**
 * Inject current trace context into a carrier (e.g., HTTP headers).
 *
 * This function injects the current OpenTelemetry trace context into a carrier
 * object, typically HTTP headers. This allows trace context to be propagated
 * across service boundaries in distributed systems.
 *
 * @param carrier - A mutable mapping (e.g., object) to inject trace context into.
 *                 Typically HTTP headers that will be sent with a request.
 * @param context - Optional specific context to inject. If undefined,
 *                 uses the current active context.
 *
 * @example
 * Basic usage with fetch:
 * ```ts
 * import { trace } from '@lilypad/sdk';
 * import { injectContext } from '@lilypad/sdk/utils/context-propagation';
 *
 * const callExternalService = trace(async (data: any) => {
 *   // Create headers object
 *   const headers: Record<string, string> = {
 *     'Content-Type': 'application/json',
 *   };
 *
 *   // Inject current trace context into headers
 *   injectContext(headers);
 *   // Now headers contains: {'traceparent': '00-trace_id-span_id-01'}
 *
 *   // Make HTTP request with trace context
 *   const response = await fetch('https://api.example.com/process', {
 *     method: 'POST',
 *     headers,
 *     body: JSON.stringify(data),
 *   });
 *
 *   return response.json();
 * });
 * ```
 */
export function injectContext(carrier: Record<string, string>, context?: Context): void {
  _getPropagator().injectContext(carrier, context);
}

/**
 * Configure the global propagator for the SDK.
 * This should be called during SDK initialization.
 *
 * @param propagatorType - The type of propagator to use
 * @param setGlobal - Whether to set as global propagator (default: true)
 */
export function configurePropagator(propagatorType?: Propagator, setGlobal: boolean = true): void {
  if (setGlobal) {
    // Create new propagator and set it globally
    _propagator = new ContextPropagator(true, propagatorType);
  }
}
