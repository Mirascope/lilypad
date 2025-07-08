import { describe, it, expect, beforeEach, vi } from 'vitest';
import { JSONSpanExporter } from './json-exporter';
import { ExportResultCode } from '@opentelemetry/core';
import { SpanKind, SpanStatusCode, TraceFlags } from '@opentelemetry/api';
import type { ReadableSpan } from '@opentelemetry/sdk-trace-base';
import type { LilypadConfig } from '../types';

vi.mock('../../lilypad/generated');
vi.mock('../../lilypad/generated/core/fetcher', () => ({
  fetcher: {
    fetch: vi.fn(),
  },
}));

describe('JSONSpanExporter', () => {
  let exporter: JSONSpanExporter;
  let config: LilypadConfig;
  let mockClient: any;

  beforeEach(() => {
    config = {
      apiKey: 'test-api-key',
      projectId: 'test-project-id',
      baseUrl: 'https://api.test.com',
      remoteClientUrl: 'https://test.com',
    };

    mockClient = {
      traces: {
        queue: vi.fn(),
      },
      _options: {
        baseUrl: 'https://api.test.com',
        apiKey: 'test-api-key',
      },
    };

    exporter = new JSONSpanExporter(config, mockClient);
    mockClient.traces.queue.mockReset();

    // Mock the createTracesWithBody method
    vi.spyOn(exporter as any, 'createTracesWithBody').mockResolvedValue({
      trace_status: 'queued',
      span_count: 1,
      trace_ids: ['12345678901234567890123456789012'],
    });
  });

  const createMockSpan = (overrides: Partial<ReadableSpan> = {}): ReadableSpan =>
    ({
      name: 'test-span',
      kind: SpanKind.CLIENT,
      spanContext: () => ({
        traceId: '12345678901234567890123456789012',
        spanId: '1234567890123456',
        traceFlags: TraceFlags.SAMPLED,
        traceState: undefined,
      }),
      parentSpanId: undefined,
      startTime: [1234567890, 123456789],
      endTime: [1234567891, 123456789],
      status: { code: SpanStatusCode.OK },
      attributes: { 'test.attribute': 'value' },
      links: [],
      events: [],
      duration: [1, 0],
      ended: true,
      resource: {
        attributes: {
          'service.name': 'test-service',
        },
        merge: vi.fn(),
      },
      instrumentationLibrary: {
        name: 'test-library',
        version: '1.0.0',
        schemaUrl: undefined,
      },
      droppedAttributesCount: 0,
      droppedEventsCount: 0,
      droppedLinksCount: 0,
      ...overrides,
    }) as ReadableSpan;

  describe('export', () => {
    it('should successfully export spans', async () => {
      const spans = [createMockSpan()];

      const callback = vi.fn();
      await exporter.export(spans, callback);

      expect((exporter as any).createTracesWithBody).toHaveBeenCalledWith(
        'test-project-id',
        expect.any(Array),
        expect.objectContaining({
          timeoutInSeconds: 30,
        }),
      );

      expect(callback).toHaveBeenCalledWith({ code: ExportResultCode.SUCCESS });
    });

    it('should handle empty spans array', async () => {
      const callback = vi.fn();
      await exporter.export([], callback);

      expect((exporter as any).createTracesWithBody).not.toHaveBeenCalled();
      expect(callback).toHaveBeenCalledWith({ code: ExportResultCode.SUCCESS });
    });

    it('should handle export failure', async () => {
      const spans = [createMockSpan()];
      vi.spyOn(exporter as any, 'createTracesWithBody').mockRejectedValue(
        new Error('Internal Server Error'),
      );

      const callback = vi.fn();
      await exporter.export(spans, callback);

      expect(callback).toHaveBeenCalledWith({ code: ExportResultCode.FAILED });
    });

    it('should handle network errors', async () => {
      const spans = [createMockSpan()];
      vi.spyOn(exporter as any, 'createTracesWithBody').mockRejectedValue(
        new Error('Network error'),
      );

      const callback = vi.fn();
      await exporter.export(spans, callback);

      expect(callback).toHaveBeenCalledWith({ code: ExportResultCode.FAILED });
    });
  });

  describe('spanToDict', () => {
    it('should correctly serialize span with all fields', async () => {
      const span = createMockSpan({
        events: [
          {
            name: 'test-event',
            attributes: { 'event.attr': 'value' },
            time: [1234567890, 500000000],
            droppedAttributesCount: 0,
          },
        ],
        links: [
          {
            context: {
              traceId: 'abcdef1234567890abcdef1234567890',
              spanId: 'abcdef1234567890',
              traceFlags: TraceFlags.SAMPLED,
              traceState: undefined,
            },
            attributes: { 'link.attr': 'value' },
            droppedAttributesCount: 0,
          },
        ],
      });

      const callback = vi.fn();
      await exporter.export([span], callback);

      const callArgs = (exporter as any).createTracesWithBody.mock.calls[0];
      const serializedSpan = callArgs[1][0]; // Second argument is spans array

      expect(serializedSpan).toMatchObject({
        trace_id: '12345678901234567890123456789012',
        span_id: '1234567890123456',
        name: 'test-span',
        kind: 'CLIENT',
        status: 'OK',
        events: [
          {
            name: 'test-event',
            attributes: { 'event.attr': 'value' },
            timestamp: 1234567890500000000,
          },
        ],
        links: [
          {
            context: {
              trace_id: 'abcdef1234567890abcdef1234567890',
              span_id: 'abcdef1234567890',
              trace_flags: '01',
            },
            attributes: { 'link.attr': 'value' },
          },
        ],
      });
    });
  });

  describe('logTraceUrls', () => {
    it('should prevent memory leak by limiting logged trace IDs', async () => {
      // Create more spans than MAX_LOGGED_TRACES
      const spans = [];
      for (let i = 0; i < 1100; i++) {
        spans.push(
          createMockSpan({
            spanContext: () => ({
              traceId: `trace${i}`.padEnd(32, '0'),
              spanId: '1234567890123456',
              traceFlags: TraceFlags.SAMPLED,
              traceState: undefined,
            }),
          }),
        );
      }

      vi.spyOn(exporter as any, 'createTracesWithBody').mockResolvedValue({
        trace_status: 'queued',
        span_count: spans.length,
        trace_ids: spans.map((_, i) => `trace${i}`.padEnd(32, '0')),
      });

      const callback = vi.fn();
      await exporter.export(spans, callback);

      // Access private property for testing (not ideal but necessary)
      const loggedTraceIds = (exporter as any).loggedTraceIds;
      expect(loggedTraceIds.size).toBeLessThanOrEqual(1000);
    });
  });

  describe('shutdown', () => {
    it('should resolve immediately', async () => {
      await expect(exporter.shutdown()).resolves.toBeUndefined();
    });
  });

  describe('forceFlush', () => {
    it('should resolve immediately', async () => {
      await expect(exporter.forceFlush()).resolves.toBeUndefined();
    });
  });
});
