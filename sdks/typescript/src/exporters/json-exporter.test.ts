import { describe, it, expect, beforeEach, vi } from 'vitest';
import { JSONSpanExporter } from './json-exporter';
import { ExportResultCode } from '@opentelemetry/core';
import { SpanKind, SpanStatusCode, TraceFlags } from '@opentelemetry/api';
import type { ReadableSpan } from '@opentelemetry/sdk-trace-base';
import type { LilypadConfig } from '../types';
import { logger } from '../utils/logger';

vi.mock('../../lilypad/generated');
vi.mock('../../lilypad/generated/core/fetcher', () => ({
  fetcher: vi.fn(),
}));
vi.mock('../utils/logger', () => ({
  logger: {
    debug: vi.fn(),
    info: vi.fn(),
    error: vi.fn(),
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
    vi.clearAllMocks();
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

      // Mock the createTracesWithBody method for this test
      vi.spyOn(exporter as any, 'createTracesWithBody').mockResolvedValue({
        trace_status: 'queued',
        span_count: 1,
        trace_ids: ['12345678901234567890123456789012'],
      });

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

      // Mock the createTracesWithBody method for this test
      const mockCreateTracesWithBody = vi
        .spyOn(exporter as any, 'createTracesWithBody')
        .mockResolvedValue({
          trace_status: 'queued',
          span_count: 1,
          trace_ids: ['12345678901234567890123456789012'],
        });

      const callback = vi.fn();
      await exporter.export([span], callback);

      const callArgs = mockCreateTracesWithBody.mock.calls[0];
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

    it('should handle span without instrumentation library', async () => {
      const span = createMockSpan({
        instrumentationLibrary: undefined,
      });

      // Mock the createTracesWithBody method for this test
      const mockCreateTracesWithBody = vi
        .spyOn(exporter as any, 'createTracesWithBody')
        .mockResolvedValue({
          trace_status: 'queued',
          span_count: 1,
          trace_ids: ['12345678901234567890123456789012'],
        });

      const callback = vi.fn();
      await exporter.export([span], callback);

      const callArgs = mockCreateTracesWithBody.mock.calls[0];
      const serializedSpan = callArgs[1][0];

      expect(serializedSpan.instrumentation_scope).toEqual({
        name: null,
        version: null,
        schema_url: null,
        attributes: {},
      });
    });

    it('should handle span with lilypad.type attribute', async () => {
      const span = createMockSpan({
        attributes: {
          'lilypad.type': 'llm',
          'lilypad.session_id': 'session-123',
        },
      });

      // Mock the createTracesWithBody method for this test
      const mockCreateTracesWithBody = vi
        .spyOn(exporter as any, 'createTracesWithBody')
        .mockResolvedValue({
          trace_status: 'queued',
          span_count: 1,
          trace_ids: ['12345678901234567890123456789012'],
        });

      const callback = vi.fn();
      await exporter.export([span], callback);

      const callArgs = mockCreateTracesWithBody.mock.calls[0];
      const serializedSpan = callArgs[1][0];

      expect(serializedSpan.type).toBe('llm');
      expect(serializedSpan.session_id).toBe('session-123');
    });

    it('should handle links with trace state', async () => {
      const mockTraceState = {
        serialize: vi.fn().mockReturnValue('vendor1=value1,vendor2=value2'),
      };

      const span = createMockSpan({
        links: [
          {
            context: {
              traceId: 'abcdef1234567890abcdef1234567890',
              spanId: 'abcdef1234567890',
              traceFlags: TraceFlags.SAMPLED,
              traceState: mockTraceState,
            },
            attributes: {},
            droppedAttributesCount: 0,
          },
        ],
      });

      // Mock the createTracesWithBody method for this test
      const mockCreateTracesWithBody = vi
        .spyOn(exporter as any, 'createTracesWithBody')
        .mockResolvedValue({
          trace_status: 'queued',
          span_count: 1,
          trace_ids: ['12345678901234567890123456789012'],
        });

      const callback = vi.fn();
      await exporter.export([span], callback);

      const callArgs = mockCreateTracesWithBody.mock.calls[0];
      const serializedSpan = callArgs[1][0];

      expect(serializedSpan.links[0].context.trace_state).toBe('vendor1=value1,vendor2=value2');
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

    it('should log multiple trace URLs when multiple new traces', async () => {
      const loggerSpy = vi.spyOn(logger, 'info');
      const debugSpy = vi.spyOn(logger, 'debug');

      const spans = [
        createMockSpan({
          spanContext: () => ({
            traceId: 'trace1'.padEnd(32, '0'),
            spanId: '1234567890123456',
            traceFlags: TraceFlags.SAMPLED,
            traceState: undefined,
          }),
        }),
        createMockSpan({
          spanContext: () => ({
            traceId: 'trace2'.padEnd(32, '0'),
            spanId: '1234567890123456',
            traceFlags: TraceFlags.SAMPLED,
            traceState: undefined,
          }),
        }),
      ];

      vi.spyOn(exporter as any, 'createTracesWithBody').mockResolvedValue({
        trace_status: 'queued',
        span_count: 2,
        trace_ids: ['trace1'.padEnd(32, '0'), 'trace2'.padEnd(32, '0')],
      });

      const callback = vi.fn();
      await exporter.export(spans, callback);

      expect(loggerSpy).toHaveBeenCalledWith(expect.stringContaining('View 2 new traces at:'));
      expect(debugSpy).toHaveBeenCalledWith(expect.stringContaining('trace1'));
      expect(debugSpy).toHaveBeenCalledWith(expect.stringContaining('trace2'));
    });

    it('should handle response without trace_ids', async () => {
      vi.spyOn(exporter as any, 'createTracesWithBody').mockResolvedValue({
        trace_status: 'queued',
        span_count: 1,
        trace_ids: undefined,
      });

      const callback = vi.fn();
      await exporter.export([createMockSpan()], callback);

      expect(callback).toHaveBeenCalledWith({ code: ExportResultCode.SUCCESS });
    });

    it('should not log when trace_status is not queued', async () => {
      const loggerSpy = vi.spyOn(logger, 'info');

      vi.spyOn(exporter as any, 'createTracesWithBody').mockResolvedValue({
        trace_status: 'failed',
        span_count: 1,
        trace_ids: ['trace1'.padEnd(32, '0')],
      });

      const callback = vi.fn();
      await exporter.export([createMockSpan()], callback);

      expect(loggerSpy).not.toHaveBeenCalledWith(expect.stringContaining('View trace at:'));
    });
  });

  describe('createTracesWithBody', () => {
    it('should handle timeout error', async () => {
      const spans = [createMockSpan()];

      const { fetcher } = await import('../../lilypad/generated/core/fetcher');
      vi.mocked(fetcher).mockResolvedValue({
        ok: false,
        error: {
          reason: 'timeout',
        },
      } as any);

      const callback = vi.fn();
      await exporter.export(spans, callback);

      expect(callback).toHaveBeenCalledWith({ code: ExportResultCode.FAILED });
      expect(vi.mocked(logger).error).toHaveBeenCalledWith(
        expect.stringContaining('[EXPORT] ❌ Request timeout'),
      );
    });

    it('should handle unknown error', async () => {
      const spans = [createMockSpan()];

      const { fetcher } = await import('../../lilypad/generated/core/fetcher');
      vi.mocked(fetcher).mockResolvedValue({
        ok: false,
        error: {
          reason: 'unknown',
          errorMessage: 'Something went wrong',
        },
      } as any);

      const callback = vi.fn();
      await exporter.export(spans, callback);

      expect(callback).toHaveBeenCalledWith({ code: ExportResultCode.FAILED });
      expect(vi.mocked(logger).error).toHaveBeenCalledWith(
        expect.stringContaining('[EXPORT] ❌ Unknown error: Something went wrong'),
      );
    });

    it('should handle non-json error', async () => {
      const spans = [createMockSpan()];

      const { fetcher } = await import('../../lilypad/generated/core/fetcher');
      vi.mocked(fetcher).mockResolvedValue({
        ok: false,
        error: {
          reason: 'non-json',
          statusCode: 500,
          rawBody: '<html>Internal Server Error</html>',
        },
      } as any);

      const callback = vi.fn();
      await exporter.export(spans, callback);

      expect(callback).toHaveBeenCalledWith({ code: ExportResultCode.FAILED });
      expect(vi.mocked(logger).error).toHaveBeenCalledWith(
        expect.stringContaining('[EXPORT] ❌ Non-JSON response 500'),
      );
    });

    it('should handle status-code error', async () => {
      const spans = [createMockSpan()];

      const { fetcher } = await import('../../lilypad/generated/core/fetcher');
      vi.mocked(fetcher).mockResolvedValue({
        ok: false,
        error: {
          reason: 'status-code',
          statusCode: 400,
          body: { error: 'Bad Request' },
        },
      } as any);

      const callback = vi.fn();
      await exporter.export(spans, callback);

      expect(callback).toHaveBeenCalledWith({ code: ExportResultCode.FAILED });
      expect(vi.mocked(logger).error).toHaveBeenCalledWith(
        expect.stringContaining('[EXPORT] ❌ HTTP Error 400'),
      );
    });

    it('should handle fetch error with cause', async () => {
      const spans = [createMockSpan()];

      const { fetcher } = await import('../../lilypad/generated/core/fetcher');
      const fetchError = new Error('Network error');
      (fetchError as any).cause = { code: 'ECONNREFUSED' };
      vi.mocked(fetcher).mockRejectedValue(fetchError);

      const callback = vi.fn();
      await exporter.export(spans, callback);

      expect(callback).toHaveBeenCalledWith({ code: ExportResultCode.FAILED });
      expect(vi.mocked(logger).error).toHaveBeenCalledWith(
        expect.stringContaining('[EXPORT] ❌ Fetch error: Network error'),
      );
      expect(vi.mocked(logger).error).toHaveBeenCalledWith(
        expect.stringContaining('[EXPORT] ❌ Fetch error cause:'),
      );
    });

    it('should handle successful export', async () => {
      const spans = [createMockSpan()];

      const { fetcher } = await import('../../lilypad/generated/core/fetcher');
      vi.mocked(fetcher).mockResolvedValue({
        ok: true,
        body: {
          trace_status: 'queued',
          span_count: 1,
          trace_ids: ['12345678901234567890123456789012'],
        },
      } as any);

      const callback = vi.fn();
      await exporter.export(spans, callback);

      expect(callback).toHaveBeenCalledWith({ code: ExportResultCode.SUCCESS });
      expect(vi.mocked(logger).info).toHaveBeenCalledWith(
        expect.stringContaining('[EXPORT] ✅ Export successful'),
      );
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
