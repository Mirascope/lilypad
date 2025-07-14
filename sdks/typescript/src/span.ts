import {
  trace,
  Span as OTelSpan,
  SpanStatusCode,
  context,
  Context,
  SpanKind,
  AttributeValue,
  Attributes,
} from '@opentelemetry/api';
import { getCurrentSession } from './session';
import { logger } from './utils/logger';
import { isConfigured } from './utils/settings';
import { safeStringify } from './utils/json';
import { validateAttributeValue, sanitizeErrorMessage, validateSpanName } from './utils/validation';
import type { SpanMetadata, SpanAttributesValue } from './types/span';

/**
 * Log level types matching Python SDK
 */
type LogLevel = 'debug' | 'info' | 'warning' | 'error' | 'critical';

/**
 * Convert our span attribute value to OpenTelemetry AttributeValue
 */
function toOTelAttributeValue(value: SpanAttributesValue | string): AttributeValue {
  if (Array.isArray(value)) {
    // OpenTelemetry expects homogeneous arrays
    if (value.length === 0) return [];

    const firstType = typeof value[0];
    if (firstType === 'string') return value as string[];
    if (firstType === 'number') return value as number[];
    if (firstType === 'boolean') return value as boolean[];

    // Mixed types - convert all to strings
    return value.map(String);
  }

  return value as AttributeValue;
}

/**
 * Convert metadata to OpenTelemetry Attributes
 */
function toOTelAttributes(metadata: SpanMetadata): Attributes {
  const attributes: Attributes = {};

  for (const [key, value] of Object.entries(metadata)) {
    if (value === undefined) continue;

    // Convert value to OTel-compatible type
    const validatedValue = validateAttributeValue(value);
    attributes[key] = toOTelAttributeValue(validatedValue);
  }

  return attributes;
}

/**
 * Span class that wraps OpenTelemetry span with additional functionality
 * matching the Python SDK behavior.
 */
export class Span {
  private _span: OTelSpan | null = null;
  private _context: Context | null = null;
  private _finished: boolean = false;

  constructor(name: string) {
    if (!isConfigured()) {
      logger.warn(
        'Span created but Lilypad SDK not configured. Call configure() first. This span will be a no-op.',
      );
      return;
    }

    // Validate span name
    const validatedName = validateSpanName(name);

    // Create OpenTelemetry span with proper parent context
    const tracer = trace.getTracer('lilypad');
    const activeContext = context.active();

    // Start span with current context as parent
    this._span = tracer.startSpan(
      validatedName,
      {
        kind: SpanKind.INTERNAL,
      },
      activeContext,
    );

    // Set up context with the new span
    this._context = trace.setSpan(activeContext, this._span);

    // Set default attributes
    this._span.setAttribute('lilypad.type', 'trace');
    this._span.setAttribute('lilypad.timestamp', new Date().toISOString());

    // Attach session ID if available
    const session = getCurrentSession();
    if (session?.id) {
      this._span.setAttribute('lilypad.session_id', session.id);
    }
  }

  /**
   * Get the span ID
   */
  get span_id(): string | null {
    if (!this._span) return null;
    return this._span.spanContext().spanId;
  }

  /**
   * Get the underlying OpenTelemetry span
   */
  get opentelemetry_span(): OTelSpan | null {
    return this._span;
  }

  /**
   * Get the span context
   */
  get context(): Context | null {
    return this._context;
  }

  /**
   * Finish the span
   */
  finish(): void {
    if (this._finished || !this._span) {
      return;
    }

    this._span.end();
    this._finished = true;
  }

  /**
   * Set metadata attributes on the span (Python SDK compatible)
   *
   * @param metadata - Metadata object
   * @returns The span instance for chaining
   */
  metadata(metadata: SpanMetadata): this;
  /**
   * Set a metadata attribute on the span
   *
   * @param key - Attribute key
   * @param value - Attribute value
   * @returns The span instance for chaining
   */
  metadata(key: string, value: unknown): this;
  metadata(...args: unknown[]): this {
    if (!this._span) return this;

    let attributes: SpanMetadata;

    if (
      args.length === 1 &&
      typeof args[0] === 'object' &&
      args[0] !== null &&
      !Array.isArray(args[0])
    ) {
      attributes = args[0] as SpanMetadata;
    } else if (args.length === 2) {
      const key = String(args[0]);
      attributes = { [key]: args[1] };
    } else if (args.length > 0) {
      this._span.setAttribute('lilypad.metadata', safeStringify(args));
      return this;
    } else {
      return this;
    }

    if ('metadata' in attributes && Object.keys(attributes).length === 1) {
      const metadataValue = attributes['metadata'];
      this._span.setAttribute('lilypad.metadata', safeStringify(metadataValue));
      return this;
    }

    for (const [key, val] of Object.entries(attributes)) {
      if (val === undefined) continue;

      const validatedValue = validateAttributeValue(val);
      this._span.setAttribute(key, toOTelAttributeValue(validatedValue));
    }

    return this;
  }

  /**
   * Add a debug log event to the span
   */
  debug(message: string, attributes?: SpanMetadata): void {
    this._log('debug', message, attributes);
  }

  /**
   * Add an info log event to the span
   */
  info(message: string, attributes?: SpanMetadata): void {
    this._log('info', message, attributes);
  }

  /**
   * Add a warning log event to the span
   */
  warning(message: string, attributes?: SpanMetadata): void {
    this._log('warning', message, attributes);
  }

  /**
   * Add an error log event to the span
   */
  error(message: string, attributes?: SpanMetadata): void {
    this._log('error', message, attributes);
  }

  /**
   * Add a critical log event to the span
   */
  critical(message: string, attributes?: SpanMetadata): void {
    this._log('critical', message, attributes);
  }

  /**
   * Internal method to add log events
   */
  private _log(level: LogLevel, message: string, attributes?: SpanMetadata): void {
    if (!this._span) return;

    const eventAttributes: SpanMetadata = {
      [`${level}.message`]: message,
      ...attributes,
    };

    this._span.addEvent(level, toOTelAttributes(eventAttributes));

    // Set span status to ERROR for error/critical logs
    if (level === 'error' || level === 'critical') {
      this._span.setStatus({
        code: SpanStatusCode.ERROR,
        message: message,
      });
    }
  }

  /**
   * Record an exception on the span
   */
  recordException(error: unknown): void {
    if (!this._span) return;

    let errorMessage: string;

    if (error instanceof Error) {
      this._span.recordException(error);
      errorMessage = error.message;
    } else {
      errorMessage = String(error);
      this._span.recordException(new Error(errorMessage));
    }

    // Sanitize error message before setting status
    const sanitizedMessage = sanitizeErrorMessage(errorMessage);

    this._span.setStatus({
      code: SpanStatusCode.ERROR,
      message: sanitizedMessage,
    });
  }

  /**
   * Set the span status
   */
  setStatus(code: SpanStatusCode, message?: string): void {
    if (!this._span) return;

    // Sanitize message if provided
    const sanitizedMessage = message ? sanitizeErrorMessage(message) : undefined;

    this._span.setStatus({ code, message: sanitizedMessage });
  }

  /**
   * Support for using Span with `using` statement (TC39 Stage 3 Explicit Resource Management)
   * This enables: `using span = new Span('name');`
   */
  [Symbol.dispose](): void {
    this.finish();
  }

  /**
   * Support for using Span with `await using` statement
   * This enables: `await using span = new Span('name');`
   */
  async [Symbol.asyncDispose](): Promise<void> {
    this.finish();
  }
}

/**
 * Create a span and run a synchronous function within its context
 *
 * @param name - The name of the span
 * @param fn - The function to run within the span context
 * @returns The result of the function
 *
 * @example
 * ```ts
 * const result = syncSpan('process-data', (span) => {
 *   span.metadata({ userId: 123 });
 *   span.info('Processing data');
 *   return processData();
 * });
 * ```
 */
export function syncSpan<T>(name: string, fn: (span: Span) => T): T {
  const span = new Span(name);
  const ctx = span.context;

  try {
    // Run within span context
    if (ctx && span.opentelemetry_span) {
      return context.with(ctx, () => fn(span));
    } else {
      // No-op mode
      return fn(span);
    }
  } catch (error) {
    span.recordException(error);
    throw error;
  } finally {
    span.finish();
  }
}

/**
 * Create a span and run an asynchronous function within its context
 *
 * @param name - The name of the span
 * @param fn - The async function to run within the span context
 * @returns Promise with the result of the function
 *
 * @example
 * ```ts
 * const result = await span('fetch-data', async (span) => {
 *   span.metadata({ endpoint: '/api/data' });
 *   span.info('Fetching data from API');
 *   const data = await fetchData();
 *   span.info('Data fetched successfully');
 *   return data;
 * });
 * ```
 */
export async function span<T>(name: string, fn: (span: Span) => Promise<T>): Promise<T> {
  const spanObj = new Span(name);
  const ctx = spanObj.context;

  try {
    // Run within span context
    if (ctx && spanObj.opentelemetry_span) {
      return await context.with(ctx, () => fn(spanObj));
    } else {
      // No-op mode
      return await fn(spanObj);
    }
  } catch (error) {
    spanObj.recordException(error);
    throw error;
  } finally {
    spanObj.finish();
  }
}
