import { describe, it, expect, beforeEach, afterEach, beforeAll } from 'vitest';
import { context as otelContext, trace } from '@opentelemetry/api';
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import {
  extractContext,
  injectContext,
  configurePropagator,
  ContextPropagator,
  getPropagator,
} from './context-propagation';

describe('Context Propagation', () => {
  let provider: NodeTracerProvider;

  beforeAll(() => {
    // Set up a tracer provider for all tests
    provider = new NodeTracerProvider();
    provider.register();
  });
  describe('getPropagator', () => {
    it('should return W3C TraceContext propagator by default', () => {
      const propagator = getPropagator();
      expect(propagator).toBeDefined();
      // Check that it has fields method which returns trace headers
      expect(propagator.fields()).toContain('traceparent');
    });

    it('should return B3 single header propagator when specified', () => {
      const propagator = getPropagator('b3');
      expect(propagator).toBeDefined();
    });

    it('should return B3 multi header propagator when specified', () => {
      const propagator = getPropagator('b3multi');
      expect(propagator).toBeDefined();
    });

    it('should return Jaeger propagator when specified', () => {
      const propagator = getPropagator('jaeger');
      expect(propagator).toBeDefined();
    });

    it('should return composite propagator when specified', () => {
      const propagator = getPropagator('composite');
      expect(propagator).toBeDefined();
    });
  });

  describe('ContextPropagator', () => {
    let propagator: ContextPropagator;

    beforeEach(() => {
      propagator = new ContextPropagator(false); // Don't set global in tests
    });

    describe('extractContext', () => {
      it('should extract W3C traceparent header', () => {
        const carrier = {
          traceparent: '00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01',
        };

        const ctx = propagator.extractContext(carrier);
        const spanContext = trace.getSpanContext(ctx);

        expect(spanContext).toBeDefined();
        expect(spanContext?.traceId).toBe('4bf92f3577b34da6a3ce929d0e0e4736');
        expect(spanContext?.spanId).toBe('00f067aa0ba902b7');
        expect(spanContext?.traceFlags).toBe(1);
      });

      it('should handle array header values', () => {
        const carrier = {
          traceparent: ['00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01'],
        };

        const ctx = propagator.extractContext(carrier);
        const spanContext = trace.getSpanContext(ctx);

        expect(spanContext).toBeDefined();
        expect(spanContext?.traceId).toBe('4bf92f3577b34da6a3ce929d0e0e4736');
      });

      it('should return empty context for invalid headers', () => {
        const carrier = {
          'some-header': 'some-value',
        };

        const ctx = propagator.extractContext(carrier);
        const spanContext = trace.getSpanContext(ctx);

        expect(spanContext).toBeUndefined();
      });
    });

    describe('injectContext', () => {
      it('should inject trace context into carrier', () => {
        // Create a span to have an active context
        const tracer = trace.getTracer('test');
        const span = tracer.startSpan('test-span');
        const ctx = trace.setSpan(otelContext.active(), span);

        const carrier: Record<string, string> = {};
        propagator.injectContext(carrier, ctx);

        expect(carrier.traceparent).toBeDefined();
        expect(carrier.traceparent).toMatch(/^00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$/);

        span.end();
      });

      it('should use current context if none provided', () => {
        const tracer = trace.getTracer('test');
        const span = tracer.startSpan('test-span');
        const ctx = trace.setSpan(otelContext.active(), span);

        // Run the test within the context
        otelContext.with(ctx, () => {
          const carrier: Record<string, string> = {};
          propagator.injectContext(carrier);

          expect(carrier.traceparent).toBeDefined();
        });

        span.end();
      });
    });

    describe('withExtractedContext', () => {
      it('should extract and attach context', () => {
        const carrier = {
          traceparent: '00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01',
        };

        const [ctx, token] = propagator.withExtractedContext(carrier);

        expect(ctx).toBeDefined();
        expect(token).toBeDefined();

        // Clean up
        propagator.detachContext(token);
      });
    });
  });

  describe('Module functions', () => {
    describe('extractContext', () => {
      it('should extract context from headers', () => {
        const headers = {
          traceparent: '00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01',
        };

        const ctx = extractContext(headers);
        const spanContext = trace.getSpanContext(ctx);

        expect(spanContext).toBeDefined();
        expect(spanContext?.traceId).toBe('4bf92f3577b34da6a3ce929d0e0e4736');
      });
    });

    describe('injectContext', () => {
      it('should inject context into headers', () => {
        const tracer = trace.getTracer('test');
        const span = tracer.startSpan('test-span');
        const ctx = trace.setSpan(otelContext.active(), span);

        const headers: Record<string, string> = {};
        injectContext(headers, ctx);

        expect(headers.traceparent).toBeDefined();

        span.end();
      });
    });
  });

  describe('configurePropagator', () => {
    // Store original env var
    const originalEnv = process.env._LILYPAD_PROPAGATOR_SET_GLOBAL;

    afterEach(() => {
      // Restore env var
      if (originalEnv !== undefined) {
        process.env._LILYPAD_PROPAGATOR_SET_GLOBAL = originalEnv;
      } else {
        delete process.env._LILYPAD_PROPAGATOR_SET_GLOBAL;
      }
    });

    it('should configure propagator type', () => {
      // Disable global setting for test
      process.env._LILYPAD_PROPAGATOR_SET_GLOBAL = 'false';

      // This should not throw
      expect(() => configurePropagator('b3', false)).not.toThrow();
    });
  });
});
