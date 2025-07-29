import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { context as otelContext, trace } from '@opentelemetry/api';
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import {
  propagatedContext,
  propagatedContextSync,
  getCurrentContext,
  detachedSpan,
} from './context-managers';
import { configure } from './configure';
import { shutdown } from './shutdown';

describe('Context Managers', () => {
  let provider: NodeTracerProvider;
  let tracer: trace.Tracer;

  beforeEach(() => {
    // Configure Lilypad SDK for testing
    configure({
      apiKey: 'test-api-key',
      projectId: '550e8400-e29b-41d4-a716-446655440000',
      baseUrl: 'http://localhost:8000',
    });

    // Set up a tracer provider for testing
    provider = new NodeTracerProvider();
    provider.register();
    tracer = trace.getTracer('test');
  });

  afterEach(async () => {
    await shutdown();
  });

  describe('propagatedContext', () => {
    it('should extract context from headers', async () => {
      const headers = {
        traceparent: '00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01',
      };

      let capturedContext: otelContext.Context | null = null;

      await propagatedContext({ extractFrom: headers }, async () => {
        capturedContext = otelContext.active();
      });

      expect(capturedContext).toBeDefined();
      const spanContext = trace.getSpanContext(capturedContext!);
      expect(spanContext?.traceId).toBe('4bf92f3577b34da6a3ce929d0e0e4736');
      expect(spanContext?.spanId).toBe('00f067aa0ba902b7');
    });

    it('should use parent context when provided', async () => {
      // Create a parent span
      const parentSpan = tracer.startSpan('parent');
      const parentCtx = trace.setSpan(otelContext.active(), parentSpan);

      let childSpanContext: trace.SpanContext | undefined;

      await propagatedContext({ parent: parentCtx }, async () => {
        const childSpan = tracer.startSpan('child');
        childSpanContext = childSpan.spanContext();
        childSpan.end();
      });

      expect(childSpanContext).toBeDefined();
      expect(childSpanContext?.traceId).toBe(parentSpan.spanContext().traceId);

      parentSpan.end();
    });

    it('should use current context when no options provided', async () => {
      const span = tracer.startSpan('current');
      const ctx = trace.setSpan(otelContext.active(), span);

      await otelContext.with(ctx, async () => {
        let capturedContext: otelContext.Context | null = null;

        await propagatedContext({}, async () => {
          capturedContext = otelContext.active();
        });

        const spanContext = trace.getSpanContext(capturedContext!);
        expect(spanContext?.traceId).toBe(span.spanContext().traceId);
      });

      span.end();
    });

    it('should throw error when both parent and extractFrom are provided', async () => {
      const headers = { traceparent: '00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01' };
      const parentCtx = otelContext.active();

      await expect(
        propagatedContext({ parent: parentCtx, extractFrom: headers }, async () => {}),
      ).rejects.toThrow('Cannot specify both parent and extractFrom');
    });

    it('should propagate return value', async () => {
      const result = await propagatedContext({}, async () => {
        return { data: 'test result' };
      });

      expect(result).toEqual({ data: 'test result' });
    });
  });

  describe('propagatedContextSync', () => {
    it('should extract context from headers synchronously', () => {
      const headers = {
        traceparent: '00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01',
      };

      let capturedContext: otelContext.Context | null = null;

      propagatedContextSync({ extractFrom: headers }, () => {
        capturedContext = otelContext.active();
      });

      expect(capturedContext).toBeDefined();
      const spanContext = trace.getSpanContext(capturedContext!);
      expect(spanContext?.traceId).toBe('4bf92f3577b34da6a3ce929d0e0e4736');
    });

    it('should propagate return value synchronously', () => {
      const result = propagatedContextSync({}, () => {
        return { data: 'sync result' };
      });

      expect(result).toEqual({ data: 'sync result' });
    });
  });

  describe('getCurrentContext', () => {
    it('should return the current active context', () => {
      const span = tracer.startSpan('test');
      const ctx = trace.setSpan(otelContext.active(), span);

      otelContext.with(ctx, () => {
        const currentCtx = getCurrentContext();
        const spanContext = trace.getSpanContext(currentCtx);
        expect(spanContext?.traceId).toBe(span.spanContext().traceId);
      });

      span.end();
    });
  });

  describe('detachedSpan', () => {
    it('should create a span not linked to current trace', async () => {
      // Create a parent span
      const parentSpan = tracer.startSpan('parent');
      const parentCtx = trace.setSpan(otelContext.active(), parentSpan);

      let detachedSpanContext: trace.SpanContext | undefined;

      await otelContext.with(parentCtx, async () => {
        await detachedSpan('background-task', async (span) => {
          detachedSpanContext = span.opentelemetry_span?.spanContext();
          span.metadata('task.type', 'background');
        });

        expect(detachedSpanContext).toBeDefined();
        // The detached span should have a different trace ID
        expect(detachedSpanContext?.traceId).not.toBe(parentSpan.spanContext().traceId);
      });

      parentSpan.end();
    });

    it('should handle errors in detached span', async () => {
      const error = new Error('Test error');

      await expect(
        detachedSpan('failing-task', async (span) => {
          span.metadata('will.fail', true);
          throw error;
        }),
      ).rejects.toThrow('Test error');
    });

    it('should propagate return value from detached span', async () => {
      const result = await detachedSpan('compute-task', async (span) => {
        span.metadata('compute.type', 'heavy');
        return { computed: 42 };
      });

      expect(result).toEqual({ computed: 42 });
    });
  });
});
