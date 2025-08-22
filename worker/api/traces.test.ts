import type { TraceRequest, TraceResponse } from '@/worker/api/traces';
import app from '@/worker/app';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const testEnv = {
  ENVIRONMENT: 'test',
  DATABASE_URL: 'postgresql://test@localhost/test',
};

describe('OpenTelemetry Traces Endpoint', () => {
  let consoleLogSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleLogSpy.mockRestore();
  });

  describe('POST /api/v1/traces', () => {
    it('should accept valid OTLP trace data and return success response', async () => {
      const traceData: TraceRequest = {
        resourceSpans: [
          {
            resource: {
              attributes: [
                { key: 'service.name', value: { stringValue: 'test-service' } },
                { key: 'service.version', value: { stringValue: '1.0.0' } },
              ],
            },
            scopeSpans: [
              {
                scope: {
                  name: 'opentelemetry.instrumentation.test',
                  version: '0.1.0',
                },
                spans: [
                  {
                    traceId: '5b8aa5a2d2c872e8321cf37308d69df2',
                    spanId: '051581bf3cb55c13',
                    name: 'test-operation',
                    kind: 2,
                    startTimeUnixNano: '1734567890000000000',
                    endTimeUnixNano: '1734567891000000000',
                    attributes: [
                      { key: 'http.method', value: { stringValue: 'GET' } },
                      { key: 'http.status_code', value: { intValue: '200' } },
                    ],
                    status: {
                      code: 0,
                      message: 'OK',
                    },
                  },
                ],
              },
            ],
          },
        ],
      };

      const res = await app.request(
        '/api/v1/traces',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(traceData),
        },
        testEnv
      );

      expect(res.status).toBe(200);
      expect(res.headers.get('Content-Type')).toContain('application/json');

      const response = (await res.json()) as TraceResponse;
      expect(response).toEqual({
        partialSuccess: {},
      });

      expect(consoleLogSpy).toHaveBeenCalledWith(
        '[TRACE DEBUG] Received 1 spans from service: test-service'
      );
      expect(consoleLogSpy).toHaveBeenCalledWith(
        '[TRACE DEBUG] Full trace data:',
        expect.any(String)
      );
    });

    it('should handle multiple spans and resource spans', async () => {
      const traceData: TraceRequest = {
        resourceSpans: [
          {
            scopeSpans: [
              {
                spans: [
                  {
                    traceId: 'trace1',
                    spanId: 'span1',
                    name: 'operation1',
                    startTimeUnixNano: '1',
                    endTimeUnixNano: '2',
                  },
                  {
                    traceId: 'trace1',
                    spanId: 'span2',
                    name: 'operation2',
                    startTimeUnixNano: '3',
                    endTimeUnixNano: '4',
                  },
                ],
              },
              {
                spans: [
                  {
                    traceId: 'trace2',
                    spanId: 'span3',
                    name: 'operation3',
                    startTimeUnixNano: '5',
                    endTimeUnixNano: '6',
                  },
                ],
              },
            ],
          },
        ],
      };

      const res = await app.request(
        '/api/v1/traces',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(traceData),
        },
        testEnv
      );

      expect(res.status).toBe(200);
      const response = (await res.json()) as TraceResponse;
      expect(response.partialSuccess).toBeDefined();

      expect(consoleLogSpy).toHaveBeenCalledWith(
        '[TRACE DEBUG] Received 3 spans from service: unknown'
      );
    });

    it('should handle traces without service name', async () => {
      const traceData: TraceRequest = {
        resourceSpans: [
          {
            scopeSpans: [
              {
                spans: [
                  {
                    traceId: 'abc123',
                    spanId: 'def456',
                    name: 'test-span',
                    startTimeUnixNano: '1000',
                    endTimeUnixNano: '2000',
                  },
                ],
              },
            ],
          },
        ],
      };

      const res = await app.request(
        '/api/v1/traces',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(traceData),
        },
        testEnv
      );

      expect(res.status).toBe(200);
      expect(consoleLogSpy).toHaveBeenCalledWith(
        '[TRACE DEBUG] Received 1 spans from service: unknown'
      );
    });

    it('should handle empty resource spans', async () => {
      const traceData: TraceRequest = {
        resourceSpans: [],
      };

      const res = await app.request(
        '/api/v1/traces',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(traceData),
        },
        testEnv
      );

      expect(res.status).toBe(200);
      const response = (await res.json()) as TraceResponse;
      expect(response.partialSuccess).toBeDefined();

      expect(consoleLogSpy).toHaveBeenCalledWith(
        '[TRACE DEBUG] Received 0 spans from service: unknown'
      );
    });

    it('should handle partial success response fields', async () => {
      const traceData: TraceRequest = {
        resourceSpans: [
          {
            scopeSpans: [
              {
                spans: [
                  {
                    traceId: 'test-trace',
                    spanId: 'test-span',
                    name: 'test',
                    startTimeUnixNano: '1',
                    endTimeUnixNano: '2',
                  },
                ],
              },
            ],
          },
        ],
      };

      const res = await app.request(
        '/api/v1/traces',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(traceData),
        },
        testEnv
      );

      expect(res.status).toBe(200);
      const response = (await res.json()) as TraceResponse;

      expect(response).toHaveProperty('partialSuccess');
      expect(response.partialSuccess).toEqual({});
      expect(response.partialSuccess?.rejectedSpans).toBeUndefined();
      expect(response.partialSuccess?.errorMessage).toBeUndefined();
    });

    it('should reject invalid trace data', async () => {
      const invalidData = {
        resourceSpans: [
          {
            scopeSpans: [
              {
                spans: [
                  {
                    spanId: 'missing-traceId',
                    name: 'test',
                    startTimeUnixNano: '1',
                    endTimeUnixNano: '2',
                  },
                ],
              },
            ],
          },
        ],
      };

      const res = await app.request(
        '/api/v1/traces',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(invalidData),
        },
        testEnv
      );

      expect(res.status).toBe(400);
    });

    it('should handle malformed JSON', async () => {
      const res = await app.request(
        '/api/v1/traces',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: 'not-valid-json',
        },
        testEnv
      );

      expect(res.status).toBe(400);
    });

    it('should extract service name from resource attributes', async () => {
      const traceData: TraceRequest = {
        resourceSpans: [
          {
            resource: {
              attributes: [
                { key: 'other.attribute', value: { stringValue: 'value' } },
                { key: 'service.name', value: { stringValue: 'my-service' } },
                {
                  key: 'service.namespace',
                  value: { stringValue: 'production' },
                },
              ],
            },
            scopeSpans: [
              {
                spans: [
                  {
                    traceId: 'trace1',
                    spanId: 'span1',
                    name: 'operation',
                    startTimeUnixNano: '1',
                    endTimeUnixNano: '2',
                  },
                ],
              },
            ],
          },
        ],
      };

      const res = await app.request(
        '/api/v1/traces',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(traceData),
        },
        testEnv
      );

      expect(res.status).toBe(200);
      expect(consoleLogSpy).toHaveBeenCalledWith(
        '[TRACE DEBUG] Received 1 spans from service: my-service'
      );
    });

    it('should handle complex attribute values', async () => {
      const traceData: TraceRequest = {
        resourceSpans: [
          {
            resource: {
              attributes: [
                {
                  key: 'service.name',
                  value: { stringValue: 'complex-service' },
                },
                { key: 'int.value', value: { intValue: '12345' } },
                { key: 'double.value', value: { doubleValue: 123.45 } },
                { key: 'bool.value', value: { boolValue: true } },
                {
                  key: 'array.value',
                  value: {
                    arrayValue: {
                      values: [
                        { stringValue: 'item1' },
                        { stringValue: 'item2' },
                      ],
                    },
                  },
                },
              ],
            },
            scopeSpans: [
              {
                spans: [
                  {
                    traceId: 'complex-trace',
                    spanId: 'complex-span',
                    name: 'complex-operation',
                    startTimeUnixNano: '1000',
                    endTimeUnixNano: '2000',
                  },
                ],
              },
            ],
          },
        ],
      };

      const res = await app.request(
        '/api/v1/traces',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(traceData),
        },
        testEnv
      );

      expect(res.status).toBe(200);
      expect(consoleLogSpy).toHaveBeenCalledWith(
        '[TRACE DEBUG] Received 1 spans from service: complex-service'
      );
    });
  });

  describe('OpenAPI Documentation', () => {
    it('should include traces endpoint in OpenAPI spec', async () => {
      const res = await app.request('/openapi.json', {}, testEnv);
      expect(res.status).toBe(200);

      const spec = (await res.json()) as any;
      expect(spec.paths['/api/v1/traces']).toBeDefined();
      expect(spec.paths['/api/v1/traces'].post).toBeDefined();
      expect(spec.paths['/api/v1/traces'].post.tags).toContain('Telemetry');
      expect(spec.paths['/api/v1/traces'].post.summary).toBe(
        'Debug endpoint for OpenTelemetry traces'
      );
    });

    it('should define Telemetry tag in OpenAPI spec', async () => {
      const res = await app.request('/openapi.json', {}, testEnv);
      const spec = (await res.json()) as any;

      const telemetryTag = spec.tags.find(
        (tag: any) => tag.name === 'Telemetry'
      );
      expect(telemetryTag).toBeDefined();
      expect(telemetryTag.description).toContain('OpenTelemetry');
    });
  });
});
