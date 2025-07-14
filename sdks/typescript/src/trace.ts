/**
 * Industry-standard trace decorator implementation for Lilypad TypeScript SDK
 *
 * This implementation follows OpenTelemetry standards and TypeScript best practices,
 * avoiding parameter injection patterns in favor of context-based span access.
 */

import { trace as otelTrace, SpanStatusCode, SpanKind } from '@opentelemetry/api';
import type { Span as OTelSpan, Attributes } from '@opentelemetry/api';
import { getSettings } from './utils/settings';
// _LilypadClient type is used in the closure analysis below
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import type { LilypadClient as _LilypadClient } from '../lilypad/generated/Client';
import { safeStringify } from './utils/json';
import { getCachedClosure } from './utils/closure';
import { getProvider } from './configure';
import { getPooledClient } from './utils/client-pool';
import { handleBackgroundError, ensureError } from './utils/error-handler';
import { logger } from './utils/logger';
import type { AnnotationCreate, FunctionCreate } from '../lilypad/generated/api/types';
import type { SpanAttributesValue } from './types/span';

/**
 * Options for the trace decorator
 */
export interface TraceOptions {
  name?: string;
  mode?: 'wrap' | null;
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
): Promise<string | null> {
  try {
    const closure = getCachedClosure(fn);

    // Check cache first
    const cached = functionUuidCache.get(closure.hash);
    if (cached) return cached;

    const client = getPooledClient({
      apiKey,
      projectId,
      baseUrl,
      serviceName: 'lilypad-node-app',
    });

    // Try to get existing function
    try {
      const existing = await client.projects.functions.getByHash(projectId, closure.hash);
      functionUuidCache.set(closure.hash, existing.uuid);
      return existing.uuid;
    } catch (error) {
      const err = ensureError(error);
      if ('statusCode' in err && (err as any).statusCode !== 404) {
        throw err;
      }
    }

    // Create new function
    const createData: FunctionCreate = {
      project_uuid: projectId,
      code: closure.code,
      hash: closure.hash,
      name: closure.name,
      signature: closure.signature,
      arg_types: {},
      dependencies: closure.dependencies,
      is_versioned: false,
      prompt_template: '',
    };

    const created = await client.projects.functions.create(projectId, createData);
    functionUuidCache.set(closure.hash, created.uuid);
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

/**
 * Wrap a standalone function with tracing (high-order function usage)
 *
 * @param fn - Function to trace
 * @param options - Trace options
 * @returns Traced function
 *
 * @example
 * const traced = wrapWithTrace(async (x: number) => x * 2, { name: 'double' });
 * const result = await traced(5);
 *
 * @example
 * // With auto_llm enabled, combine with custom tracing:
 * const processData = wrapWithTrace(
 *   async (data: string) => {
 *     // This OpenAI call is auto-traced
 *     const response = await openai.chat.completions.create({...});
 *     return response.choices[0].message.content;
 *   },
 *   { name: 'processData', tags: ['data-processing'] }
 * );
 */
export function wrapWithTrace<T extends (...args: any[]) => any>(
  fn: T,
  options?: TraceOptions | string,
): T {
  const opts: TraceOptions = typeof options === 'string' ? { name: options } : options || {};
  const spanName = opts.name || fn.name || 'anonymous';

  const settings = getSettings();
  if (!settings) {
    logger.warn('Lilypad SDK not configured. Function will execute without tracing.');
    return fn;
  }

  const isAsync =
    fn.constructor.name === 'AsyncFunction' || fn.constructor.name === 'AsyncGeneratorFunction';

  return async function (...args: Parameters<T>): Promise<ReturnType<T>> {
    const tracer = otelTrace.getTracer('lilypad');

    return tracer.startActiveSpan(
      spanName,
      {
        kind: SpanKind.INTERNAL,
        attributes: {
          'lilypad.project_uuid': settings.projectId,
          'lilypad.type': 'trace',
          'code.function': spanName,
          ...opts.attributes,
        },
      },
      async (span) => {
        let functionUuid = '';

        try {
          // Set argument values
          const argValues: Record<string, unknown> = {};
          args.forEach((arg, index) => {
            argValues[`arg${index}`] = arg;
          });
          span.setAttribute('lilypad.trace.arg_values', safeStringify(argValues));

          // Set tags if provided
          if (opts.tags) {
            span.setAttribute('lilypad.trace.tags', opts.tags);
          }

          // Get or create function
          if (opts.mode === 'wrap') {
            const uuid = await getOrCreateFunction(
              fn,
              settings.projectId,
              settings.apiKey,
              settings.baseUrl || 'https://api.getlilypad.com',
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
              settings.baseUrl || 'https://api.getlilypad.com',
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

          // Set output
          span.setAttribute('lilypad.trace.output', safeStringify(result));
          span.setStatus({ code: SpanStatusCode.OK });

          // Handle wrap mode
          if (opts.mode === 'wrap') {
            const spanId = span.spanContext().spanId;
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
}

/**
 * Type guard to check if we're using Stage-3 decorators
 */
function isStage3DecoratorContext(
  args: any[],
): args is [unknown, { kind: string; name?: string | symbol }] {
  return args.length === 2 && typeof args[1] === 'object' && args[1] !== null && 'kind' in args[1];
}

/**
 * Industry-standard trace decorator implementation with dual decorator support
 *
 * Supports both legacy decorators (experimentalDecorators: true) and Stage-3 decorators
 * Runtime detection automatically handles both standards.
 *
 * @param options - Trace options or name string
 * @returns Method decorator
 *
 * @example
 * // Works with both decorator standards
 * class Service {
 *   @trace()
 *   async method() { ... }
 *
 *   @trace({ mode: 'wrap', tags: ['api'] })
 *   async traced() { ... }
 * }
 */
export function trace(options?: TraceOptions | string): any {
  const opts: TraceOptions = typeof options === 'string' ? { name: options } : options || {};

  // Return a function that handles both decorator signatures
  return function (...args: any[]) {
    // Debug logging to understand what tsx is passing
    logger.debug('[trace decorator] Args:', {
      length: args.length,
      types: args.map((arg) => typeof arg),
      arg0Type: typeof args[0],
      arg1Type: typeof args[1],
      arg2Type: typeof args[2],
      isStage3:
        args.length === 2 && typeof args[1] === 'object' && args[1] !== null && 'kind' in args[1],
    });

    // Stage-3 decorator detection
    if (isStage3DecoratorContext(args)) {
      const [value, context] = args;

      logger.debug('[trace decorator] Stage-3 context:', {
        kind: context.kind,
        name: context.name,
        nameType: typeof context.name,
        valueType: typeof value,
      });

      if (context.kind !== 'method') {
        throw new Error('trace decorator can only be applied to methods');
      }

      // In Stage-3, value is the original method
      if (typeof value !== 'function') {
        // This is the case where tsx might be passing something else
        logger.warn('[trace decorator] Stage-3 value is not a function:', {
          valueType: typeof value,
          value: value,
        });

        // Try to handle tsx's transformation
        return function (originalMethod: any) {
          logger.debug('[trace decorator] tsx Stage-3 wrapper called with:', {
            originalMethodType: typeof originalMethod,
          });

          if (typeof originalMethod !== 'function') {
            throw new Error(
              `trace decorator: originalMethod is not a function, got ${typeof originalMethod}`,
            );
          }

          const methodName = typeof context.name === 'string' ? context.name : String(context.name);

          // Return the wrapped method
          return function (this: any, ...args: any[]) {
            return traceMethod.call(this, originalMethod, opts, methodName, args);
          };
        };
      }

      // Standard Stage-3 decorator - value is the original method
      const originalMethod = value;
      const methodName = typeof context.name === 'string' ? context.name : String(context.name);

      // Return the replacement method
      return function (this: any, ...args: any[]) {
        return traceMethod.call(this, originalMethod, opts, methodName, args);
      };
    }

    // Legacy decorator
    const [target, propertyKey, descriptor] = args as [
      object,
      string | symbol,
      PropertyDescriptor?,
    ];

    logger.debug('[trace decorator] Legacy decorator args:', {
      targetType: typeof target,
      propertyKeyType: typeof propertyKey,
      propertyKey: propertyKey,
      descriptorType: typeof descriptor,
      hasDescriptor: !!descriptor,
      descriptorValue: descriptor?.value,
      descriptorValueType: descriptor ? typeof descriptor.value : 'no descriptor',
    });

    // Handle the case where tsx passes the method name as the second argument
    // when using --require (no descriptor)
    if (!descriptor && typeof propertyKey === 'string' && typeof target === 'function') {
      logger.debug('[trace decorator] tsx --require mode detected, using target as constructor');

      // In this case, target is the constructor and propertyKey is the method name
      // We need to wrap the method on the prototype
      const prototype = target.prototype;
      const originalMethod = prototype[propertyKey];

      if (typeof originalMethod !== 'function') {
        throw new Error(`trace decorator: method ${propertyKey} is not a function on prototype`);
      }

      // Create a wrapped method
      prototype[propertyKey] = function (this: any, ...args: any[]) {
        return traceMethod.call(this, originalMethod, opts, propertyKey as string, args);
      };

      return;
    }

    if (!descriptor) {
      throw new Error('trace decorator descriptor is undefined - check TypeScript configuration');
    }

    const originalMethod = descriptor.value;
    if (typeof originalMethod !== 'function') {
      throw new Error('trace decorator can only be applied to methods');
    }

    descriptor.value = function (this: any, ...methodArgs: any[]) {
      return traceMethod.call(this, originalMethod, opts, propertyKey, methodArgs);
    };

    return descriptor;
  };
}

/**
 * Common trace implementation for both decorator standards
 */
function traceMethod(
  this: any,
  originalMethod: Function,
  opts: TraceOptions,
  propertyKey: string | symbol,
  args: unknown[],
): any {
  const settings = getSettings();
  if (!settings) {
    logger.warn('Lilypad SDK not configured. Executing without tracing.');
    return originalMethod.apply(this, args);
  }

  const spanName = opts.name || `${this.constructor.name}.${String(propertyKey)}`;
  const isAsync =
    originalMethod.constructor.name === 'AsyncFunction' ||
    originalMethod.constructor.name === 'AsyncGeneratorFunction';

  const tracer = otelTrace.getTracer('lilypad');

  return tracer.startActiveSpan(
    spanName,
    {
      kind: SpanKind.INTERNAL,
      attributes: {
        'lilypad.project_uuid': settings.projectId,
        'lilypad.type': 'trace',
        'code.function': String(propertyKey),
        'code.namespace': this.constructor.name,
        ...opts.attributes,
      },
    },
    async (span) => {
      // Store function UUID for later use
      let functionUuid = '';

      try {
        // Set argument values
        const argValues: Record<string, unknown> = {};
        args.forEach((arg, index) => {
          argValues[`arg${index}`] = arg;
        });
        span.setAttribute('lilypad.trace.arg_values', safeStringify(argValues));

        // Set tags if provided
        if (opts.tags) {
          span.setAttribute('lilypad.trace.tags', opts.tags);
        }

        // Get or create function
        // For wrap mode, we need to wait for the function UUID
        if (opts.mode === 'wrap') {
          const uuid = await getOrCreateFunction(
            originalMethod as (...args: unknown[]) => unknown,
            settings.projectId,
            settings.apiKey,
            settings.baseUrl || 'https://api.getlilypad.com',
          );
          if (uuid) {
            functionUuid = uuid;
            span.setAttribute('lilypad.function.uuid', uuid);
          }
        } else {
          // For non-wrap mode, we can fire and forget
          getOrCreateFunction(
            originalMethod as (...args: unknown[]) => unknown,
            settings.projectId,
            settings.apiKey,
            settings.baseUrl || 'https://api.getlilypad.com',
          )
            .then((uuid) => {
              if (uuid) {
                functionUuid = uuid;
                span.setAttribute('lilypad.function.uuid', uuid);
              }
            })
            .catch((err) => logger.error('Failed to create function:', ensureError(err)));
        }

        // Execute the original method
        const result = await originalMethod.apply(this, args);

        // Set output
        span.setAttribute('lilypad.trace.output', safeStringify(result));
        span.setStatus({ code: SpanStatusCode.OK });

        // Handle wrap mode
        if (opts.mode === 'wrap') {
          const spanId = span.spanContext().spanId;
          if (isAsync) {
            return new AsyncTrace(result, spanId, functionUuid);
          }
          // For sync functions, log deprecation warning
          logger.warn(
            'Returning Trace (fire-and-forget) for synchronous functions is deprecated. ' +
              'Consider using async functions with AsyncTrace for proper error handling.',
          );
          return new Trace(result, spanId, functionUuid);
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
}
