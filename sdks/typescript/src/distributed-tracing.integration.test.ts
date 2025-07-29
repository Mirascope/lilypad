import { describe, it, expect, beforeAll } from 'vitest';
import { trace as otelTrace, context } from '@opentelemetry/api';
import { InMemorySpanExporter, SimpleSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { configure, getProvider } from './configure';
import { propagatedContext, getCurrentContext } from './context-managers';
import { injectContext, extractContext } from './utils/context-propagation';
import { trace } from './trace';

describe('Distributed Tracing Integration', () => {
  let spanExporter: InMemorySpanExporter;

  beforeAll(async () => {
    // Set up in-memory span exporter for testing
    spanExporter = new InMemorySpanExporter();

    // Configure Lilypad with test settings
    await configure({
      apiKey: 'test-api-key',
      projectId: '550e8400-e29b-41d4-a716-446655440000',
      propagator: 'tracecontext',
      baseUrl: 'http://localhost:8000',
    });

    // Add the in-memory exporter to capture spans
    const provider = getProvider();
    if (provider) {
      provider.addSpanProcessor(new SimpleSpanProcessor(spanExporter));
    }
  });

  it('should propagate trace context across service boundaries', async () => {
    // Clear any previous spans
    spanExporter.reset();

    // Simulate Service A creating a trace
    const serviceAFunction = trace(
      async (data: unknown) => {
        // Simulate calling Service B
        const headers: Record<string, string> = {};
        injectContext(headers);

        // Headers should now contain trace context
        expect(headers.traceparent).toBeDefined();
        expect(headers.traceparent).toMatch(/^00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$/);

        return { ...data, processedByA: true, headers };
      },
      { name: 'serviceA.process' },
    );

    // Execute Service A
    const resultA = await serviceAFunction({ value: 42 });

    // Simulate Service B receiving the request
    await propagatedContext({ extractFrom: resultA.headers }, async () => {
      const serviceBFunction = trace(
        async (data: unknown) => {
          return { ...data, processedByB: true };
        },
        { name: 'serviceB.process' },
      );

      await serviceBFunction(resultA);
    });

    // Wait a bit for spans to be exported
    await new Promise((resolve) => setTimeout(resolve, 100));

    // Check that spans were created with proper parent-child relationship
    const spans = spanExporter.getFinishedSpans();
    expect(spans.length).toBe(2);

    const spanA = spans.find((s) => s.name === 'serviceA.process');
    const spanB = spans.find((s) => s.name === 'serviceB.process');

    expect(spanA).toBeDefined();
    expect(spanB).toBeDefined();

    // Service B should have the same trace ID as Service A
    expect(spanB?.spanContext().traceId).toBe(spanA?.spanContext().traceId);

    // Service B should have Service A as its parent
    expect(spanB?.parentSpanId).toBe(spanA?.spanContext().spanId);
  });

  it('should support different propagation formats', async () => {
    // Test B3 propagation
    const headers: Record<string, string> = {};
    const tracer = otelTrace.getTracer('test');
    const span = tracer.startSpan('test-b3');
    const ctx = otelTrace.setSpan(context.active(), span);

    context.with(ctx, () => {
      injectContext(headers);
    });

    // Headers should contain trace context (exact format depends on propagator)
    expect(Object.keys(headers).length).toBeGreaterThan(0);

    span.end();
  });

  it('should handle detached spans correctly', async () => {
    spanExporter.reset();

    // Create a parent trace
    const parentFunction = trace(
      async () => {
        // Import detachedSpan
        const { detachedSpan } = await import('./context-managers');

        // Create a detached span
        await detachedSpan('background-task', async (span) => {
          span.metadata('detached', true);
        });

        return 'parent-complete';
      },
      { name: 'parent.operation' },
    );

    await parentFunction();

    // Wait for spans
    await new Promise((resolve) => setTimeout(resolve, 100));

    const spans = spanExporter.getFinishedSpans();
    const parentSpan = spans.find((s) => s.name === 'parent.operation');
    const detachedSpan = spans.find((s) => s.name === 'background-task');

    expect(parentSpan).toBeDefined();
    expect(detachedSpan).toBeDefined();

    // Detached span should have a different trace ID
    expect(detachedSpan?.spanContext().traceId).not.toBe(parentSpan?.spanContext().traceId);
  });

  it('should extract context from various header formats', () => {
    // W3C TraceContext format
    const w3cHeaders = {
      traceparent: '00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01',
    };

    const ctx = extractContext(w3cHeaders);
    const spanContext = otelTrace.getSpanContext(ctx);

    expect(spanContext).toBeDefined();
    expect(spanContext?.traceId).toBe('4bf92f3577b34da6a3ce929d0e0e4736');
    expect(spanContext?.spanId).toBe('00f067aa0ba902b7');
    expect(spanContext?.traceFlags).toBe(1);
  });

  it('should maintain context through async operations', async () => {
    spanExporter.reset();

    const asyncOperation = trace(
      async () => {
        const currentCtx = getCurrentContext();

        // Simulate async operation
        await new Promise((resolve) => setTimeout(resolve, 10));

        // Context should be maintained
        await propagatedContext({ parent: currentCtx }, async () => {
          const nestedOperation = trace(
            async () => {
              return 'nested-result';
            },
            { name: 'nested.operation' },
          );

          await nestedOperation();
        });

        return 'async-complete';
      },
      { name: 'async.operation' },
    );

    await asyncOperation();

    // Wait for spans
    await new Promise((resolve) => setTimeout(resolve, 100));

    const spans = spanExporter.getFinishedSpans();
    const asyncSpan = spans.find((s) => s.name === 'async.operation');
    const nestedSpan = spans.find((s) => s.name === 'nested.operation');

    expect(asyncSpan).toBeDefined();
    expect(nestedSpan).toBeDefined();

    // Nested span should be a child of async span
    expect(nestedSpan?.spanContext().traceId).toBe(asyncSpan?.spanContext().traceId);
    expect(nestedSpan?.parentSpanId).toBe(asyncSpan?.spanContext().spanId);
  });
});
