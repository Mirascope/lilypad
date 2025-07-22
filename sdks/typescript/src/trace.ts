/**
 * Trace implementation for Lilypad TypeScript SDK
 *
 * This implementation follows OpenTelemetry standards and TypeScript best practices,
 * providing higher-order function tracing capabilities.
 */

import { trace as otelTrace, SpanStatusCode, SpanKind } from '@opentelemetry/api';
import type { Span as OTelSpan, Attributes } from '@opentelemetry/api';
import { getSettings } from './utils/settings';
// _LilypadClient type is used in the closure analysis below
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import type { LilypadClient as _LilypadClient } from '../lilypad/generated/Client';
import { safeStringify } from './utils/json';
import { getCachedClosure, Closure } from './utils/closure';
import { getProvider } from './configure';
import { getPooledClient } from './utils/client-pool';
import { handleBackgroundError, ensureError } from './utils/error-handler';
import { logger } from './utils/logger';
import type { AnnotationCreate, FunctionCreate } from '../lilypad/generated/api/types';
import type { SpanAttributesValue } from './types/span';
// Removed versioning imports - no longer needed
import { BASE_URL } from './constants';

/**
 * Options for the trace function
 */
export interface TraceOptions {
  name?: string;
  mode?: 'wrap' | null;
  versioning?: 'automatic' | null;
  tags?: string[];
  attributes?: Record<string, SpanAttributesValue>;
}

/**
 * Get the currently active span
 */
export function getCurrentSpan(): OTelSpan | undefined {
  return otelTrace.getActiveSpan();
}

/**
 * Log a message to the current span
 */
export function logToCurrentSpan(
  level: string,
  message: string,
  attributes?: Record<string, SpanAttributesValue>,
): void {
  const span = getCurrentSpan();
  if (span) {
    const eventAttributes: Attributes = {
      [`${level}.message`]: message,
    };

    // Convert attributes to OpenTelemetry format
    if (attributes) {
      for (const [key, value] of Object.entries(attributes)) {
        if (value !== undefined && value !== null) {
          // Convert arrays to string representation
          if (Array.isArray(value)) {
            eventAttributes[key] = JSON.stringify(value);
          } else {
            eventAttributes[key] = value as string | number | boolean;
          }
        }
      }
    }

    span.addEvent(level, eventAttributes);

    if (level === 'error' || level === 'critical') {
      span.setStatus({ code: SpanStatusCode.ERROR, message });
    }
  }
}

// Cache for function UUIDs
const functionUuidCache = new Map<string, string>();

/**
 * Get or create function in Lilypad backend
 */
async function getOrCreateFunction(
  fn: (...args: unknown[]) => unknown,
  projectId: string,
  apiKey: string,
  baseUrl: string,
  isVersioned: boolean = false,
  functionName?: string, // New parameter
): Promise<string | null> {
  try {
    const { hash, code, name, signature, dependencies } = getCachedClosure(
      fn,
      undefined,
      isVersioned,
      functionName,
    );

    // Check cache first
    const cached = functionUuidCache.get(hash);
    if (cached) return cached;

    const client = getPooledClient({
      apiKey,
      projectId,
      baseUrl,
      serviceName: 'lilypad-node-app',
    });

    // Try to get existing function
    try {
      const { uuid } = await client.projects.functions.getByHash(projectId, hash);
      functionUuidCache.set(hash, uuid);
      return uuid;
    } catch (error) {
      const err = ensureError(error);
      if ('statusCode' in err && (err as any).statusCode !== 404) {
        throw err;
      }
    }

    // Create new function
    const createData: FunctionCreate = {
      project_uuid: projectId,
      code,
      hash,
      name: functionName || name, // Use provided functionName or extracted name
      signature,
      arg_types: {},
      dependencies,
      is_versioned: isVersioned,
      prompt_template: '',
    };

    // Debug log the code being sent
    logger.debug(`[getOrCreateFunction] Creating function ${name} with code:`, {
      codeLength: code.length,
      codePreview: code.substring(0, 300),
      isTypeScript: code.includes(': ') || code.includes('Promise<'),
      hash,
    });

    const created = await client.projects.functions.create(projectId, createData);
    functionUuidCache.set(hash, created.uuid);
    return created.uuid;
  } catch (error) {
    logger.error('Failed to get or create function:', ensureError(error));
    return null;
  }
}

/**
 * Base class for trace wrappers
 */
abstract class TraceBase<T> {
  private _flushed = false;

  constructor(
    public readonly response: T,
    protected readonly spanId: string,
    protected readonly functionUuid: string,
  ) {}

  /**
   * Force flush spans to ensure they're available for querying
   */
  protected async forceFlush(): Promise<void> {
    if (this._flushed) return;

    const provider = getProvider();
    if (provider) {
      try {
        await provider.forceFlush();
        this._flushed = true;
      } catch (error) {
        logger.error('Failed to force flush traces:', ensureError(error));
      }
    }
  }

  protected async getSpanUuid(): Promise<string | null> {
    const settings = getSettings();
    if (!settings) return null;

    // Force flush to ensure spans are available
    if (!this._flushed) {
      await this.forceFlush();
    }

    const client = getPooledClient(settings);

    try {
      const response = await client.projects.functions.spans.listPaginated(
        settings.projectId,
        this.functionUuid,
        {
          environment_uuid: settings.projectId,
        },
      );

      for (const span of response.items) {
        if (span.span_id === this.spanId) {
          return span.uuid;
        }
      }
    } catch (error) {
      logger.error('Failed to get span UUID:', ensureError(error));
    }

    return null;
  }
}

/**
 * Fire-and-forget trace wrapper for backward compatibility
 *
 * @deprecated This class performs async operations without proper error handling.
 * Use AsyncTrace instead for production code.
 *
 * WARNING: Errors in annotation/assignment/tagging are silently logged and cannot be caught.
 */
export class Trace<T> extends TraceBase<T> {
  /**
   * @deprecated Sync trace methods will be removed in the next major version.
   * Use AsyncTrace for proper error handling.
   */
  assign(...emails: string[]): void {
    if (!emails.length) {
      throw new Error('At least one email address must be provided');
    }

    const settings = getSettings();
    if (!settings) {
      throw new Error('Lilypad SDK not configured');
    }

    // Execute asynchronously in background with proper error handling
    void this.getSpanUuid()
      .then(async (spanUuid) => {
        if (!spanUuid) {
          const error = new Error(
            `Cannot assign: span not found for function ${this.functionUuid}`,
          );
          handleBackgroundError(error, { functionUuid: this.functionUuid, method: 'assign' });
          return;
        }

        const client = getPooledClient(settings);
        const request: AnnotationCreate[] = [
          {
            assignee_email: emails,
            function_uuid: this.functionUuid,
            project_uuid: settings.projectId,
            span_uuid: spanUuid,
          } as AnnotationCreate,
        ];

        await client.ee.projects.annotations.create(settings.projectId, request);
      })
      .catch((error) => {
        handleBackgroundError(error, {
          functionUuid: this.functionUuid,
          method: 'assign',
          emails: emails.length,
        });
      });
  }

  /**
   * @deprecated Sync trace methods will be removed in the next major version.
   * Use AsyncTrace for proper error handling.
   */
  tag(...tags: string[]): void {
    if (!tags.length) return;

    const settings = getSettings();
    if (!settings) {
      throw new Error('Lilypad SDK not configured');
    }

    // Execute asynchronously in background with proper error handling
    void this.getSpanUuid()
      .then(async (spanUuid) => {
        if (!spanUuid) {
          const error = new Error(`Cannot tag: span not found for function ${this.functionUuid}`);
          handleBackgroundError(error, { functionUuid: this.functionUuid, method: 'tag' });
          return;
        }

        const client = getPooledClient(settings);
        await client.spans.update(spanUuid, { tags_by_name: tags });
      })
      .catch((error) => {
        handleBackgroundError(error, {
          functionUuid: this.functionUuid,
          method: 'tag',
          tags,
        });
      });
  }
}

/**
 * Asynchronous trace wrapper
 */
export class AsyncTrace<T> extends TraceBase<T> {
  async assign(...emails: string[]): Promise<void> {
    if (!emails.length) {
      throw new Error('At least one email address must be provided');
    }

    const settings = getSettings();
    if (!settings) {
      throw new Error('Lilypad SDK not configured');
    }

    const spanUuid = await this.getSpanUuid();
    if (!spanUuid) {
      throw new Error(`Cannot assign: span not found for function ${this.functionUuid}`);
    }

    const client = getPooledClient(settings);

    const request: AnnotationCreate[] = [
      {
        assignee_email: emails,
        function_uuid: this.functionUuid,
        project_uuid: settings.projectId,
        span_uuid: spanUuid,
      } as AnnotationCreate,
    ];

    await client.ee.projects.annotations.create(settings.projectId, request);
  }

  async tag(...tags: string[]): Promise<void> {
    if (!tags.length) return;

    const settings = getSettings();
    if (!settings) {
      throw new Error('Lilypad SDK not configured');
    }

    const spanUuid = await this.getSpanUuid();
    if (!spanUuid) {
      throw new Error(`Cannot tag: span not found for function ${this.functionUuid}`);
    }

    const client = getPooledClient(settings);

    await client.spans.update(spanUuid, { tags_by_name: tags });
  }
}

// Overload signatures for trace
export function trace<T extends (...args: any[]) => any>(fn: T, name?: string): T;
export function trace<T extends (...args: any[]) => any>(
  fn: T,
  options: { versioning?: null; mode?: null } & Omit<TraceOptions, 'versioning' | 'mode'>,
): T;
export function trace<T extends (...args: any[]) => any>(
  fn: T,
  options: { versioning: 'automatic'; mode?: null } & Omit<TraceOptions, 'versioning' | 'mode'>,
): T;
export function trace<T extends (...args: any[]) => any>(
  fn: T,
  options: { versioning?: null; mode: 'wrap' } & Omit<TraceOptions, 'versioning' | 'mode'>,
): T extends (...args: any[]) => Promise<infer R>
  ? (...args: Parameters<T>) => Promise<AsyncTrace<R>>
  : (...args: Parameters<T>) => Trace<ReturnType<T>>;
export function trace<T extends (...args: any[]) => any>(
  fn: T,
  options: { versioning: 'automatic'; mode: 'wrap' } & Omit<TraceOptions, 'versioning' | 'mode'>,
): T extends (...args: any[]) => Promise<infer R>
  ? (...args: Parameters<T>) => Promise<AsyncTrace<R>>
  : (...args: Parameters<T>) => Trace<ReturnType<T>>;

/**
 * Trace a function with OpenTelemetry (higher-order function)
 *
 * @param fn - Function to trace
 * @param options - Trace options
 * @returns Traced function
 *
 * @example
 * const traced = trace(async (x: number) => x * 2, { name: 'double' });
 * const result = await traced(5);
 *
 * @example
 * // With auto_llm enabled, combine with custom tracing:
 * const processData = trace(
 *   async (data: string) => {
 *     // This OpenAI call is auto-traced
 *     const response = await openai.chat.completions.create({...});
 *     return response.choices[0].message.content;
 *   },
 *   { name: 'processData', tags: ['data-processing'] }
 * );
 */
export function trace<T extends (...args: any[]) => any>(
  fn: T,
  options?: TraceOptions | string,
): T {
  const opts: TraceOptions = typeof options === 'string' ? { name: options } : options || {};
  const spanName = opts.name || fn.name || 'anonymous';

  const tracedFunction = function (this: any, ...args: Parameters<T>): any {
    // Check settings at execution time, not at definition time
    const settings = getSettings();
    if (!settings) {
      logger.warn('Lilypad SDK not configured. Function will execute without tracing.');
      return fn.apply(this, args);
    }

    const tracer = otelTrace.getTracer('lilypad');

    return tracer.startActiveSpan(
      spanName,
      {
        kind: SpanKind.INTERNAL,
        attributes: {
          'lilypad.project_uuid': settings.projectId,
          'lilypad.type': opts.versioning === 'automatic' ? 'function' : 'trace',
          'code.function': spanName,
          ...opts.attributes,
        },
      },
      async (span) => {
        const isVersioned = opts.versioning === 'automatic';
        let functionUuid = '';

        try {
          // Set argument values and types
          const argValues: Record<string, unknown> = {};
          const argTypes: Record<string, string> = {};
          args.forEach((arg, index) => {
            argValues[`arg${index}`] = arg;
            argTypes[`arg${index}`] = typeof arg;
          });

          // Set attributes based on type
          if (isVersioned) {
            span.setAttribute('lilypad.function.arg_values', safeStringify(argValues));
            span.setAttribute('lilypad.function.arg_types', safeStringify(argTypes));
            span.setAttribute('lilypad.is_async', true); // Always true for async functions

            // Add function metadata
            const closure = Closure.fromFunction(fn, undefined, isVersioned, spanName);
            span.setAttribute('lilypad.function.code', closure.code);
            span.setAttribute('lilypad.function.signature', closure.signature);
            span.setAttribute('lilypad.metadata', '[]'); // Empty metadata for now
          } else {
            span.setAttribute('lilypad.trace.arg_values', safeStringify(argValues));
          }

          // Set tags if provided
          if (opts.tags) {
            span.setAttribute('lilypad.trace.tags', opts.tags);
          }

          // Get or create function
          if (opts.mode === 'wrap' || isVersioned) {
            const uuid = await getOrCreateFunction(
              fn,
              settings.projectId,
              settings.apiKey,
              settings.baseUrl || BASE_URL,
              isVersioned,
              spanName, // Pass spanName as functionName
            );
            if (uuid) {
              functionUuid = uuid;
              span.setAttribute('lilypad.function.uuid', uuid);
            }
          } else {
            // Fire and forget for non-wrap mode
            getOrCreateFunction(
              fn,
              settings.projectId,
              settings.apiKey,
              settings.baseUrl || BASE_URL,
              isVersioned,
              spanName, // Pass spanName as functionName
            )
              .then((uuid) => {
                if (uuid) {
                  functionUuid = uuid;
                  span.setAttribute('lilypad.function.uuid', uuid);
                }
              })
              .catch((err) => logger.error('Failed to create function:', ensureError(err)));
          }

          // Execute the original function
          const result = await fn(...args);

          // Set output based on type
          if (isVersioned) {
            span.setAttribute('lilypad.function.output', safeStringify(result));
          } else {
            span.setAttribute('lilypad.trace.output', safeStringify(result));
          }
          span.setStatus({ code: SpanStatusCode.OK });

          // Handle wrap mode
          if (opts.mode === 'wrap') {
            const spanId = span.spanContext().spanId;
            const isAsync =
              fn.constructor.name === 'AsyncFunction' ||
              fn.constructor.name === 'AsyncGeneratorFunction';
            return isAsync
              ? new AsyncTrace(result, spanId, functionUuid)
              : new Trace(result, spanId, functionUuid);
          }

          return result;
        } catch (error) {
          const err = ensureError(error);
          span.recordException(err);
          span.setStatus({
            code: SpanStatusCode.ERROR,
            message: err.message,
          });
          throw err;
        } finally {
          span.end();
        }
      },
    );
  } as T;

  // If versioning is enabled, just return the traced function
  // The TypeScript code extraction happens at build time
  return tracedFunction;
}

/**
 * Backward compatibility alias for trace function
 * @deprecated Use trace() instead
 */
export const wrapWithTrace = trace;
