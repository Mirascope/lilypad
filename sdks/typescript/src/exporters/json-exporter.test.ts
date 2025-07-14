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

      // Mock the makeCustomTracesRequest method for this test
      vi.spyOn(exporter as any, 'makeCustomTracesRequest').mockResolvedValue({
        trace_status: 'queued',
        span_count: 1,
        trace_ids: ['12345678901234567890123456789012'],
      });

      const callback = vi.fn();
      await exporter.export(spans, callback);

      expect((exporter as any).makeCustomTracesRequest).toHaveBeenCalledWith(expect.any(Array));

      expect(callback).toHaveBeenCalledWith({ code: ExportResultCode.SUCCESS });
    });

    it('should handle empty spans array', async () => {
      const callback = vi.fn();
      await exporter.export([], callback);

      expect(callback).toHaveBeenCalledWith({ code: ExportResultCode.SUCCESS });
    });

    it('should handle export failure', async () => {
      const spans = [createMockSpan()];
      vi.spyOn(exporter as any, 'makeCustomTracesRequest').mockRejectedValue(
        new Error('Internal Server Error'),
      );

      const callback = vi.fn();
      await exporter.export(spans, callback);

      expect(callback).toHaveBeenCalledWith({ code: ExportResultCode.FAILED });
    });

    it('should handle network errors', async () => {
      const spans = [createMockSpan()];
      vi.spyOn(exporter as any, 'makeCustomTracesRequest').mockRejectedValue(
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

      // Mock the makeCustomTracesRequest method for this test
      const mockMakeCustomTracesRequest = vi
        .spyOn(exporter as any, 'makeCustomTracesRequest')
        .mockResolvedValue({
          trace_status: 'queued',
          span_count: 1,
          trace_ids: ['12345678901234567890123456789012'],
        });

      const callback = vi.fn();
      await exporter.export([span], callback);

      const callArgs = mockMakeCustomTracesRequest.mock.calls[0];
      const serializedSpan = callArgs[0][0]; // First argument is spans array

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

      // Mock the makeCustomTracesRequest method for this test
      const mockMakeCustomTracesRequest = vi
        .spyOn(exporter as any, 'makeCustomTracesRequest')
        .mockResolvedValue({
          trace_status: 'queued',
          span_count: 1,
          trace_ids: ['12345678901234567890123456789012'],
        });

      const callback = vi.fn();
      await exporter.export([span], callback);

      const callArgs = mockMakeCustomTracesRequest.mock.calls[0];
      const serializedSpan = callArgs[0][0];

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

      // Mock the makeCustomTracesRequest method for this test
      const mockMakeCustomTracesRequest = vi
        .spyOn(exporter as any, 'makeCustomTracesRequest')
        .mockResolvedValue({
          trace_status: 'queued',
          span_count: 1,
          trace_ids: ['12345678901234567890123456789012'],
        });

      const callback = vi.fn();
      await exporter.export([span], callback);

      const callArgs = mockMakeCustomTracesRequest.mock.calls[0];
      const serializedSpan = callArgs[0][0];

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

      // Mock the makeCustomTracesRequest method for this test
      const mockMakeCustomTracesRequest = vi
        .spyOn(exporter as any, 'makeCustomTracesRequest')
        .mockResolvedValue({
          trace_status: 'queued',
          span_count: 1,
          trace_ids: ['12345678901234567890123456789012'],
        });

      const callback = vi.fn();
      await exporter.export([span], callback);

      const callArgs = mockMakeCustomTracesRequest.mock.calls[0];
      const serializedSpan = callArgs[0][0];

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

      vi.spyOn(exporter as any, 'makeCustomTracesRequest').mockResolvedValue({
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

      vi.spyOn(exporter as any, 'makeCustomTracesRequest').mockResolvedValue({
        trace_status: 'queued',
        span_count: 2,
        trace_ids: ['trace1'.padEnd(32, '0'), 'trace2'.padEnd(32, '0')],
      });

      const callback = vi.fn();
      await exporter.export(spans, callback);

      // Should log each trace URL individually
      expect(loggerSpy).toHaveBeenCalledWith(expect.stringContaining('View trace:'));
      expect(loggerSpy).toHaveBeenCalledWith(expect.stringContaining('trace1'));
      expect(loggerSpy).toHaveBeenCalledWith(expect.stringContaining('trace2'));
      expect(loggerSpy).toHaveBeenCalledTimes(2);
    });

    it('should handle response without trace_ids', async () => {
      vi.spyOn(exporter as any, 'makeCustomTracesRequest').mockResolvedValue({
        trace_status: 'queued',
        span_count: 1,
        trace_ids: undefined,
      });

      const callback = vi.fn();
      await exporter.export([createMockSpan()], callback);

      expect(callback).toHaveBeenCalledWith({ code: ExportResultCode.SUCCESS });
    });

    it('should log trace URLs regardless of trace_status', async () => {
      const loggerSpy = vi.spyOn(logger, 'info');

      vi.spyOn(exporter as any, 'makeCustomTracesRequest').mockResolvedValue({
        trace_status: 'failed',
        span_count: 1,
        trace_ids: ['trace1'.padEnd(32, '0')],
      });

      const callback = vi.fn();
      await exporter.export([createMockSpan()], callback);

      // The implementation logs trace URLs regardless of trace_status
      expect(loggerSpy).toHaveBeenCalledWith(expect.stringContaining('View trace:'));
      expect(loggerSpy).toHaveBeenCalledWith(expect.stringContaining('trace1'));
    });
  });

  describe('makeCustomTracesRequest', () => {
    it('should handle timeout error', async () => {
      const spans = [createMockSpan()];

      // Mock fetch to simulate timeout
      global.fetch = vi.fn().mockRejectedValue(new Error('Request timeout'));

      const callback = vi.fn();
      await exporter.export(spans, callback);

      expect(callback).toHaveBeenCalledWith({ code: ExportResultCode.FAILED });
      expect(vi.mocked(logger).error).toHaveBeenCalledWith(
        'Error exporting spans:',
        expect.any(Error),
      );
    });

    it('should handle unknown error', async () => {
      const spans = [createMockSpan()];

      // Mock fetch to return error response
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        text: vi.fn().mockResolvedValue('Something went wrong'),
      });

      const callback = vi.fn();
      await exporter.export(spans, callback);

      expect(callback).toHaveBeenCalledWith({ code: ExportResultCode.FAILED });
      expect(vi.mocked(logger).error).toHaveBeenCalledWith(
        'Error exporting spans:',
        expect.any(Error),
      );
    });

    it('should handle non-json error', async () => {
      const spans = [createMockSpan()];

      // Mock fetch to return non-JSON response
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        text: vi.fn().mockResolvedValue('<html>Internal Server Error</html>'),
      });

      const callback = vi.fn();
      await exporter.export(spans, callback);

      expect(callback).toHaveBeenCalledWith({ code: ExportResultCode.FAILED });
      expect(vi.mocked(logger).error).toHaveBeenCalledWith(
        'Server error response: <html>Internal Server Error</html>',
      );
    });

    it('should handle status-code error', async () => {
      const spans = [createMockSpan()];

      // Mock fetch to return 400 error
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        text: vi.fn().mockResolvedValue('Bad Request'),
      });

      const callback = vi.fn();
      await exporter.export(spans, callback);

      expect(callback).toHaveBeenCalledWith({ code: ExportResultCode.FAILED });
      expect(vi.mocked(logger).error).toHaveBeenCalledWith('Server error response: Bad Request');
    });

    it('should handle fetch error with cause', async () => {
      const spans = [createMockSpan()];

      // Mock fetch to throw network error
      const fetchError = new Error('Network error');
      (fetchError as any).cause = { code: 'ECONNREFUSED' };
      global.fetch = vi.fn().mockRejectedValue(fetchError);

      const callback = vi.fn();
      await exporter.export(spans, callback);

      expect(callback).toHaveBeenCalledWith({ code: ExportResultCode.FAILED });
      expect(vi.mocked(logger).error).toHaveBeenCalledWith('Error exporting spans:', fetchError);
    });

    it('should handle successful export', async () => {
      const spans = [createMockSpan()];

      // Mock fetch to return success
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: vi.fn().mockResolvedValue({
          trace_status: 'queued',
          span_count: 1,
          trace_ids: ['12345678901234567890123456789012'],
          message: 'Spans queued for processing',
        }),
      });

      const callback = vi.fn();
      await exporter.export(spans, callback);

      expect(callback).toHaveBeenCalledWith({ code: ExportResultCode.SUCCESS });

      // Check that the debug logger was called with the success message
      const debugCalls = vi.mocked(logger).debug.mock.calls;
      const successCall = debugCalls.find(
        (call) =>
          typeof call[0] === 'string' && call[0].includes('Export successful, response data:'),
      );
      expect(successCall).toBeDefined();
      expect(successCall?.[0]).toContain('Export successful, response data:');
      expect(successCall?.[0]).toContain('"trace_status":"queued"');
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
