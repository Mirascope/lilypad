import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { SimpleSpanProcessor, InMemorySpanExporter } from '@opentelemetry/sdk-trace-base';
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { SpanStatusCode, trace } from '@opentelemetry/api';
import { Resource } from '@opentelemetry/resources';
import { SEMRESATTRS_SERVICE_NAME } from '@opentelemetry/semantic-conventions';
import { Span, span, syncSpan } from './span';
import { withSessionAsync } from './session';
import * as settings from './utils/settings';
import { logger } from './utils/logger';

describe('Span Integration Tests', () => {
  let memoryExporter: InMemorySpanExporter;
  let provider: NodeTracerProvider;

  beforeEach(() => {
    // Disable any previous providers
    trace.disable();

    // Clear any previous state
    memoryExporter = new InMemorySpanExporter();

    // Create real OpenTelemetry provider
    provider = new NodeTracerProvider({
      resource: new Resource({
        [SEMRESATTRS_SERVICE_NAME]: 'test-service',
      }),
    });

    // Add memory exporter
    provider.addSpanProcessor(new SimpleSpanProcessor(memoryExporter));

    // Register globally
    provider.register();

    // Mock isConfigured to return true
    vi.spyOn(settings, 'isConfigured').mockReturnValue(true);

    // Mock logger to suppress warnings
    vi.spyOn(logger, 'warn').mockImplementation(() => {});
    vi.spyOn(logger, 'error').mockImplementation(() => {});
  });

  afterEach(async () => {
    // Shutdown provider
    await provider.shutdown();

    // Clear spans
    memoryExporter.reset();

    // Restore mocks
    vi.restoreAllMocks();
  });

  describe('Basic Span Operations', () => {
    it('should create and export a span', async () => {
      const testSpan = new Span('test-span');
      testSpan.metadata({ key: 'value' });
      testSpan.info('Test log');
      testSpan.finish();

      // Force flush to ensure export
      await provider.forceFlush();

      const spans = memoryExporter.getFinishedSpans();
      expect(spans).toHaveLength(1);

      const exportedSpan = spans[0];
      expect(exportedSpan.name).toBe('test-span');
      expect(exportedSpan.attributes['lilypad.type']).toBe('trace');
      expect(exportedSpan.attributes['key']).toBe('value');

      // Check events
      expect(exportedSpan.events).toHaveLength(1);
      expect(exportedSpan.events[0].name).toBe('info');
      expect(exportedSpan.events[0].attributes?.['info.message']).toBe('Test log');
    });

    it('should handle sync span with context propagation', async () => {
      const result = syncSpan('sync-operation', (s) => {
        s.metadata({ operation: 'sync' });

        // Nested span should have parent
        const nestedResult = syncSpan('nested-sync', (child) => {
          child.metadata({ nested: true });
          return 'nested-result';
        });

        expect(nestedResult).toBe('nested-result');
        return 'sync-result';
      });

      expect(result).toBe('sync-result');

      await provider.forceFlush();

      const spans = memoryExporter.getFinishedSpans();
      expect(spans).toHaveLength(2);

      // Find parent and child
      const parentSpan = spans.find((s) => s.name === 'sync-operation');
      const childSpan = spans.find((s) => s.name === 'nested-sync');

      expect(parentSpan).toBeDefined();
      expect(childSpan).toBeDefined();
      expect(childSpan!.parentSpanId).toBe(parentSpan!.spanContext().spanId);
    });

    it('should handle async span with context propagation', async () => {
      const result = await span('async-operation', async (s) => {
        s.metadata({ operation: 'async' });

        // Simulate async work
        await new Promise((resolve) => setTimeout(resolve, 10));

        // Nested async span
        const nestedResult = await span('nested-async', async (child) => {
          child.metadata({ nested: true });
          await new Promise((resolve) => setTimeout(resolve, 10));
          return 'nested-async-result';
        });

        expect(nestedResult).toBe('nested-async-result');
        return 'async-result';
      });

      expect(result).toBe('async-result');

      await provider.forceFlush();

      const spans = memoryExporter.getFinishedSpans();
      expect(spans).toHaveLength(2);

      // Verify parent-child relationship
      const parentSpan = spans.find((s) => s.name === 'async-operation');
      const childSpan = spans.find((s) => s.name === 'nested-async');

      expect(parentSpan).toBeDefined();
      expect(childSpan).toBeDefined();
      expect(childSpan!.parentSpanId).toBe(parentSpan!.spanContext().spanId);
    });
  });

  describe('Session Integration', () => {
    it('should attach session ID to spans', async () => {
      await withSessionAsync('test-session-123', async () => {
        await span('session-span', async (s) => {
          s.info('Operation within session');
        });
      });

      await provider.forceFlush();

      const spans = memoryExporter.getFinishedSpans();
      expect(spans).toHaveLength(1);
      expect(spans[0].attributes['lilypad.session_id']).toBe('test-session-123');
    });

    it('should maintain session across nested spans', async () => {
      await withSessionAsync('parent-session', async () => {
        await span('outer-span', async () => {
          await span('inner-span', async () => {
            await span('deep-span', async (s) => {
              s.info('Deep operation');
            });
          });
        });
      });

      await provider.forceFlush();

      const spans = memoryExporter.getFinishedSpans();
      expect(spans).toHaveLength(3);

      // All spans should have the same session ID
      spans.forEach((s) => {
        expect(s.attributes['lilypad.session_id']).toBe('parent-session');
      });
    });
  });

  describe('Error Handling', () => {
    it('should record exceptions and set error status', async () => {
      const testError = new Error('Test error message with password: secret123');

      try {
        await span('error-span', async (s) => {
          s.info('Before error');
          throw testError;
        });
      } catch (e) {
        // Expected
      }

      await provider.forceFlush();

      const spans = memoryExporter.getFinishedSpans();
      expect(spans).toHaveLength(1);

      const errorSpan = spans[0];
      expect(errorSpan.status.code).toBe(SpanStatusCode.ERROR);
      // Check that password was sanitized
      expect(errorSpan.status.message).toContain('[REDACTED]');
      expect(errorSpan.status.message).not.toContain('secret123');

      // Should have exception event
      const exceptionEvents = errorSpan.events.filter((e) => e.name === 'exception');
      expect(exceptionEvents).toHaveLength(1);
    });

    it('should handle non-Error exceptions', async () => {
      try {
        await span('string-error-span', async () => {
          throw 'String error with api_key=abc123';
        });
      } catch (e) {
        // Expected
      }

      await provider.forceFlush();

      const spans = memoryExporter.getFinishedSpans();
      expect(spans).toHaveLength(1);

      const errorSpan = spans[0];
      expect(errorSpan.status.code).toBe(SpanStatusCode.ERROR);
      expect(errorSpan.status.message).toContain('[REDACTED]');
      expect(errorSpan.status.message).not.toContain('abc123');
    });
  });

  describe('Concurrent Spans', () => {
    it('should handle concurrent spans with independent contexts', async () => {
      const results = await Promise.all([
        span('concurrent-1', async (s) => {
          await new Promise((resolve) => setTimeout(resolve, Math.random() * 50));
          s.metadata({ task: 1 });
          return 'result-1';
        }),
        span('concurrent-2', async (s) => {
          await new Promise((resolve) => setTimeout(resolve, Math.random() * 50));
          s.metadata({ task: 2 });
          return 'result-2';
        }),
        span('concurrent-3', async (s) => {
          await new Promise((resolve) => setTimeout(resolve, Math.random() * 50));
          s.metadata({ task: 3 });
          return 'result-3';
        }),
      ]);

      expect(results).toEqual(['result-1', 'result-2', 'result-3']);

      await provider.forceFlush();

      const spans = memoryExporter.getFinishedSpans();
      expect(spans).toHaveLength(3);

      // Each span should be independent (no parent)
      spans.forEach((s) => {
        expect(s.parentSpanId).toBeUndefined();
      });

      // Check each span has correct metadata
      const span1 = spans.find((s) => s.name === 'concurrent-1');
      const span2 = spans.find((s) => s.name === 'concurrent-2');
      const span3 = spans.find((s) => s.name === 'concurrent-3');

      expect(span1?.attributes['task']).toBe(1);
      expect(span2?.attributes['task']).toBe(2);
      expect(span3?.attributes['task']).toBe(3);
    });
  });

  describe('Metadata and Attributes', () => {
    it('should handle various attribute types', async () => {
      await span('attribute-test', async (s) => {
        s.metadata({
          string: 'test',
          number: 123,
          boolean: true,
          null: null,
          undefined: undefined,
          array: [1, 2, 3],
          object: { nested: 'value' },
        });
      });

      await provider.forceFlush();

      const spans = memoryExporter.getFinishedSpans();
      expect(spans).toHaveLength(1);

      const attributes = spans[0].attributes;
      expect(attributes['string']).toBe('test');
      expect(attributes['number']).toBe(123);
      expect(attributes['boolean']).toBe(true);
      expect(attributes['null']).toBe('null');
      expect(attributes['undefined']).toBeUndefined(); // undefined values are skipped
      expect(attributes['array']).toEqual([1, 2, 3]);
      expect(attributes['object']).toBe('{"nested":"value"}');
    });

    it('should handle special metadata key', async () => {
      await span('metadata-test', async (s) => {
        s.metadata({ metadata: { special: 'data' } });
      });

      await provider.forceFlush();

      const spans = memoryExporter.getFinishedSpans();
      expect(spans).toHaveLength(1);

      const attributes = spans[0].attributes;
      expect(attributes['lilypad.metadata']).toBe('{"special":"data"}');
    });
  });

  describe('Logging Levels', () => {
    it('should create events with correct attributes for each log level', async () => {
      await span('log-test', async (s) => {
        s.debug('Debug message', { extra: 'debug-data' });
        s.info('Info message', { extra: 'info-data' });
        s.warning('Warning message', { extra: 'warning-data' });
        s.error('Error message', { extra: 'error-data' });
        s.critical('Critical message', { extra: 'critical-data' });
      });

      await provider.forceFlush();

      const spans = memoryExporter.getFinishedSpans();
      expect(spans).toHaveLength(1);

      const events = spans[0].events;
      expect(events).toHaveLength(5);

      // Check each event
      const debugEvent = events.find((e) => e.name === 'debug');
      expect(debugEvent?.attributes?.['debug.message']).toBe('Debug message');
      expect(debugEvent?.attributes?.['extra']).toBe('debug-data');

      const errorEvent = events.find((e) => e.name === 'error');
      expect(errorEvent?.attributes?.['error.message']).toBe('Error message');

      // Error and critical should set span status
      expect(spans[0].status.code).toBe(SpanStatusCode.ERROR);
      expect(spans[0].status.message).toBe('Critical message'); // Last error message
    });
  });

  describe('Context Propagation Edge Cases', () => {
    it('should handle context across async boundaries', async () => {
      await span('async-boundary-test', async (parentSpan) => {
        parentSpan.info('Parent start');

        // Multiple async operations
        await Promise.all([
          (async () => {
            await new Promise((resolve) => setTimeout(resolve, 10));
            await span('async-child-1', async (c) => {
              c.info('Child 1');
            });
          })(),
          (async () => {
            await new Promise((resolve) => setTimeout(resolve, 20));
            await span('async-child-2', async (c) => {
              c.info('Child 2');
            });
          })(),
        ]);

        parentSpan.info('Parent end');
      });

      await provider.forceFlush();

      const spans = memoryExporter.getFinishedSpans();
      expect(spans).toHaveLength(3);

      const parentSpan = spans.find((s) => s.name === 'async-boundary-test');
      const child1 = spans.find((s) => s.name === 'async-child-1');
      const child2 = spans.find((s) => s.name === 'async-child-2');

      // Both children should have the same parent
      expect(child1?.parentSpanId).toBe(parentSpan?.spanContext().spanId);
      expect(child2?.parentSpanId).toBe(parentSpan?.spanContext().spanId);
    });
  });
});
