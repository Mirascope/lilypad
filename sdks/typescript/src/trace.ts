/**
 * Industry-standard trace decorator implementation for Lilypad TypeScript SDK
 *
 * This implementation follows OpenTelemetry standards and TypeScript best practices,
 * avoiding parameter injection patterns in favor of context-based span access.
 */

import { trace as otelTrace, SpanStatusCode, SpanKind } from '@opentelemetry/api';
import type { Span as OTelSpan } from '@opentelemetry/api';
import { getSettings } from './utils/settings';
import { LilypadClient } from '../lilypad/generated/Client';
import { safeStringify } from './utils/json';
import { getCachedClosure } from './utils/closure';
import type {
  AnnotationCreate,
  FunctionCreate,
  Label,
  EvaluationType,
} from '../lilypad/generated/api/types';

/**
 * Options for the trace decorator
 */
export interface TraceOptions {
  name?: string;
  mode?: 'wrap' | null;
  tags?: string[];
  attributes?: Record<string, any>;
}

/**
 * Annotation data structure
 */
export interface Annotation {
  data?: Record<string, any> | null;
  label?: Label | null;
  reasoning?: string | null;
  type?: EvaluationType | null;
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
  attributes?: Record<string, any>,
): void {
  const span = getCurrentSpan();
  if (span) {
    span.addEvent(level, {
      [`${level}.message`]: message,
      ...attributes,
    });

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
  fn: Function,
  projectId: string,
  apiKey: string,
  baseUrl: string,
): Promise<string | null> {
  try {
    const closure = getCachedClosure(fn);

    // Check cache first
    const cached = functionUuidCache.get(closure.hash);
    if (cached) return cached;

    const client = new LilypadClient({
      environment: () => baseUrl,
      apiKey: () => apiKey,
    });

    // Try to get existing function
    try {
      const existing = await client.projects.functions.getByHash(projectId, closure.hash);
      functionUuidCache.set(closure.hash, existing.uuid);
      return existing.uuid;
    } catch (error: any) {
      if (error?.statusCode !== 404) throw error;
    }

    // Create new function
    const createData: FunctionCreate = {
      project_uuid: projectId,
      code: closure.code,
      hash: closure.hash,
      name: closure.name,
      signature: closure.signature,
      arg_types: {},
      dependencies: closure.dependencies as any,
      is_versioned: false,
      prompt_template: '',
    };

    const created = await client.projects.functions.create(projectId, createData);
    functionUuidCache.set(closure.hash, created.uuid);
    return created.uuid;
  } catch (error) {
    console.error('Failed to get or create function:', error);
    return null;
  }
}

/**
 * Base class for trace wrappers
 */
abstract class TraceBase<T> {
  constructor(
    public readonly response: T,
    protected readonly spanId: string,
    protected readonly functionUuid: string,
  ) {}

  protected async getSpanUuid(): Promise<string | null> {
    const settings = getSettings();
    if (!settings) return null;

    const client = new LilypadClient({
      environment: () => settings.baseUrl || 'https://api.getlilypad.com',
      apiKey: () => settings.apiKey,
    });

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
      console.error('Failed to get span UUID:', error);
    }

    return null;
  }

  protected createAnnotationRequests(
    projectId: string,
    spanUuid: string,
    annotations: Annotation[],
  ): AnnotationCreate[] {
    return annotations.map(
      (annotation) =>
        ({
          data: annotation.data,
          function_uuid: this.functionUuid,
          span_uuid: spanUuid,
          label: annotation.label,
          reasoning: annotation.reasoning,
          type: annotation.type,
          project_uuid: projectId,
        }) as AnnotationCreate,
    );
  }
}

/**
 * Synchronous trace wrapper
 */
export class Trace<T> extends TraceBase<T> {
  annotate(...annotations: Annotation[]): void {
    if (!annotations.length) {
      throw new Error('At least one annotation must be provided');
    }

    const settings = getSettings();
    if (!settings) {
      throw new Error('Lilypad SDK not configured');
    }

    // Execute asynchronously in background
    this.getSpanUuid()
      .then((spanUuid) => {
        if (!spanUuid) {
          console.error(`Cannot annotate: span not found for function ${this.functionUuid}`);
          return;
        }

        const client = new LilypadClient({
          environment: () => settings.baseUrl || 'https://api.getlilypad.com',
          apiKey: () => settings.apiKey,
        });

        const requests = this.createAnnotationRequests(settings.projectId, spanUuid, annotations);
        return client.ee.projects.annotations.create(settings.projectId, requests);
      })
      .catch((error) => {
        console.error('Failed to create annotations:', error);
      });
  }

  assign(...emails: string[]): void {
    if (!emails.length) {
      throw new Error('At least one email address must be provided');
    }

    const settings = getSettings();
    if (!settings) {
      throw new Error('Lilypad SDK not configured');
    }

    // Execute asynchronously in background
    this.getSpanUuid()
      .then((spanUuid) => {
        if (!spanUuid) {
          console.error(`Cannot assign: span not found for function ${this.functionUuid}`);
          return;
        }

        const client = new LilypadClient({
          environment: () => settings.baseUrl || 'https://api.getlilypad.com',
          apiKey: () => settings.apiKey,
        });

        const request: AnnotationCreate[] = [
          {
            assignee_email: emails,
            function_uuid: this.functionUuid,
            project_uuid: settings.projectId,
            span_uuid: spanUuid,
          } as AnnotationCreate,
        ];

        return client.ee.projects.annotations.create(settings.projectId, request);
      })
      .catch((error) => {
        console.error('Failed to assign trace:', error);
      });
  }

  tag(...tags: string[]): void {
    if (!tags.length) return;

    const settings = getSettings();
    if (!settings) {
      throw new Error('Lilypad SDK not configured');
    }

    // Execute asynchronously in background
    this.getSpanUuid()
      .then((spanUuid) => {
        if (!spanUuid) {
          console.error(`Cannot tag: span not found for function ${this.functionUuid}`);
          return;
        }

        const client = new LilypadClient({
          environment: () => settings.baseUrl || 'https://api.getlilypad.com',
          apiKey: () => settings.apiKey,
        });

        return client.spans.update(spanUuid, { tags_by_name: tags });
      })
      .catch((error) => {
        console.error('Failed to tag trace:', error);
      });
  }
}

/**
 * Asynchronous trace wrapper
 */
export class AsyncTrace<T> extends TraceBase<T> {
  async annotate(...annotations: Annotation[]): Promise<void> {
    if (!annotations.length) {
      throw new Error('At least one annotation must be provided');
    }

    const settings = getSettings();
    if (!settings) {
      throw new Error('Lilypad SDK not configured');
    }

    const spanUuid = await this.getSpanUuid();
    if (!spanUuid) {
      throw new Error(`Cannot annotate: span not found for function ${this.functionUuid}`);
    }

    const client = new LilypadClient({
      environment: () => settings.baseUrl || 'https://api.getlilypad.com',
      apiKey: () => settings.apiKey,
    });

    const requests = this.createAnnotationRequests(settings.projectId, spanUuid, annotations);
    await client.ee.projects.annotations.create(settings.projectId, requests);
  }

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

    const client = new LilypadClient({
      environment: () => settings.baseUrl || 'https://api.getlilypad.com',
      apiKey: () => settings.apiKey,
    });

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

    const client = new LilypadClient({
      environment: () => settings.baseUrl || 'https://api.getlilypad.com',
      apiKey: () => settings.apiKey,
    });

    await client.spans.update(spanUuid, { tags_by_name: tags });
  }
}

/**
 * Industry-standard trace decorator implementation
 *
 * @param options - Trace options or name string
 * @returns Method decorator
 */
export function trace(options?: TraceOptions | string) {
  return function (target: any, propertyKey: string | symbol, descriptor?: PropertyDescriptor) {
    // Handle both legacy and modern decorator APIs
    if (!descriptor) {
      throw new Error('trace decorator descriptor is undefined - check TypeScript configuration');
    }

    const originalMethod = descriptor.value;
    if (typeof originalMethod !== 'function') {
      throw new Error('trace decorator can only be applied to methods');
    }

    // Parse options
    const opts: TraceOptions = typeof options === 'string' ? { name: options } : options || {};
    const spanName = opts.name || `${target.constructor.name}.${String(propertyKey)}`;
    const isAsync =
      originalMethod.constructor.name === 'AsyncFunction' ||
      originalMethod.constructor.name === 'AsyncGeneratorFunction';

    descriptor.value = function (...args: any[]) {
      const settings = getSettings();
      if (!settings) {
        console.warn('Lilypad SDK not configured. Executing without tracing.');
        return originalMethod.apply(this, args);
      }

      const tracer = otelTrace.getTracer('lilypad');

      return tracer.startActiveSpan(
        spanName,
        {
          kind: SpanKind.INTERNAL,
          attributes: {
            'lilypad.project_uuid': settings.projectId,
            'lilypad.type': 'trace',
            'code.function': String(propertyKey),
            'code.namespace': target.constructor.name,
            ...opts.attributes,
          },
        },
        async (span) => {
          // Store function UUID for later use
          let functionUuid = '';

          try {
            // Set argument values
            const argValues: Record<string, any> = {};
            args.forEach((arg, index) => {
              argValues[`arg${index}`] = arg;
            });
            span.setAttribute('lilypad.trace.arg_values', safeStringify(argValues));

            // Set tags if provided
            if (opts.tags) {
              span.setAttribute('lilypad.trace.tags', opts.tags);
            }

            // Get or create function (async, but don't wait)
            getOrCreateFunction(
              originalMethod,
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
              .catch((err) => console.error('Failed to create function:', err));

            // Execute the original method
            const result = await originalMethod.apply(this, args);

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
            span.recordException(error as Error);
            span.setStatus({
              code: SpanStatusCode.ERROR,
              message: error instanceof Error ? error.message : String(error),
            });
            throw error;
          } finally {
            span.end();
          }
        },
      );
    };

    return descriptor;
  };
}
