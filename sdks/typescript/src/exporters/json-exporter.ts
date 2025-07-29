import { ReadableSpan, SpanExporter } from '@opentelemetry/sdk-trace-base';
import { ExportResult, ExportResultCode } from '@opentelemetry/core';
import { SpanStatusCode, SpanKind } from '@opentelemetry/api';

import type { LilypadConfig } from '../types';
import type { SerializedSpan } from '../types/span';
import { logger } from '../utils/logger';
import { LilypadClient } from '../../lilypad/generated';

interface TracesQueueResponse {
  trace_status: string;
  span_count: number;
  message?: string;
  trace_ids: string[];
}

export class JSONSpanExporter implements SpanExporter {
  private readonly config: LilypadConfig;
  private readonly client: LilypadClient;
  private readonly loggedTraceIds = new Set<string>();
  private readonly MAX_LOGGED_TRACES = 1000;

  constructor(config: LilypadConfig, client: LilypadClient) {
    this.config = config;
    this.client = client;
  }

  async export(
    spans: ReadableSpan[],
    resultCallback: (result: ExportResult) => void,
  ): Promise<void> {
    logger.debug(`JSONSpanExporter.export called with ${spans?.length || 0} spans`);

    if (!spans || spans.length === 0) {
      logger.debug('No spans to export, returning success');
      resultCallback({ code: ExportResultCode.SUCCESS });
      return;
    }

    try {
      const spanData = spans.map((span) => this.spanToDict(span));
      logger.debug(`Prepared ${spanData.length} spans for export`);
      logger.debug(`First span: ${JSON.stringify(spanData[0], null, 2)}`);

      // The generated TypeScript client doesn't support body parameters for traces.create
      // So we need to make a custom request using the client's internal fetcher
      const response = await this.makeCustomTracesRequest(spanData);

      logger.debug(`Export successful, response data: ${JSON.stringify(response)}`);
      this.logTraceUrls(response);
      resultCallback({ code: ExportResultCode.SUCCESS });
    } catch (error) {
      logger.error('Error exporting spans:', error);
      logger.debug(`Error details: ${error instanceof Error ? error.stack : String(error)}`);
      resultCallback({ code: ExportResultCode.FAILED });
    }
  }

  async shutdown(): Promise<void> {
    return Promise.resolve();
  }

  async forceFlush(): Promise<void> {
    return Promise.resolve();
  }

  private spanToDict(span: ReadableSpan): SerializedSpan {
    const spanContext = span.spanContext();
    const parentSpanId = span.parentSpanId;

    const instrumentationScope = span.instrumentationLibrary;
    const scope = instrumentationScope
      ? {
          name: instrumentationScope.name,
          version: instrumentationScope.version || null,
          schema_url: instrumentationScope.schemaUrl || null,
          attributes: {},
        }
      : {
          name: null,
          version: null,
          schema_url: null,
          attributes: {},
        };

    const spanType = span.attributes?.['lilypad.type'] as string | undefined;

    const result: SerializedSpan = {
      trace_id: spanContext.traceId,
      span_id: spanContext.spanId,
      parent_span_id: parentSpanId || null,
      instrumentation_scope: scope,
      resource: JSON.stringify({
        attributes: span.resource.attributes,
        schema_url: null,
      }),
      name: span.name,
      kind: SpanKind[span.kind],
      start_time: span.startTime[0] * 1e9 + span.startTime[1],
      end_time: span.endTime[0] * 1e9 + span.endTime[1],
      type: spanType,
      attributes: (() => {
        const attrs = { ...(span.attributes || {}) };
        // Remove lilypad.type from attributes to avoid duplication with the type field
        delete attrs['lilypad.type'];
        return attrs;
      })(),
      status: SpanStatusCode[span.status.code],
      session_id: (span.attributes?.['lilypad.session_id'] as string | null) || null,
      events: span.events.map((event) => ({
        name: event.name,
        attributes: event.attributes || {},
        timestamp: event.time[0] * 1e9 + event.time[1],
      })),
      links: span.links.map((link) => ({
        context: {
          trace_id: link.context.traceId,
          span_id: link.context.spanId,
          trace_flags: link.context.traceFlags.toString(16).padStart(2, '0'),
          trace_state: link.context.traceState?.serialize(),
        },
        attributes: link.attributes || {},
      })),
    };
    return result;
  }

  private async makeCustomTracesRequest(spanData: SerializedSpan[]): Promise<TracesQueueResponse> {
    // Access the client's internal options to use the generated client's fetcher
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const clientOptions = (this.client as any)._options;

    // Get base URL and API key
    const baseUrl = (await clientOptions.baseUrl) || (await clientOptions.environment);
    const apiKey = await clientOptions.apiKey;

    // Import the core fetcher from the generated client
    const { fetcher } = await import('../../lilypad/generated/core/fetcher/index.js');

    const response = await fetcher({
      url: `${baseUrl}/projects/${encodeURIComponent(this.config.projectId)}/traces`,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
      body: spanData,
      timeoutMs: 60000,
      requestType: 'json',
      responseType: 'json',
    });

    if (!response.ok) {
      logger.error(`Server error response:`, response.error);
      throw new Error(`Export failed: ${response.error.reason}`);
    }

    return response.body as TracesQueueResponse;
  }

  private logTraceUrls(responseData: TracesQueueResponse): void {
    // Response structure: { trace_status: "queued", span_count: 1, trace_ids: [...] }
    if (!responseData?.trace_ids || !Array.isArray(responseData.trace_ids)) {
      logger.debug('No trace_ids in response');
      return;
    }

    for (const traceId of responseData.trace_ids) {
      if (this.loggedTraceIds.has(traceId)) {
        continue;
      }

      const traceUrl = `${this.config.remoteClientUrl}/projects/${this.config.projectId}/traces/${traceId}`;
      logger.info(`View trace: ${traceUrl}`);
      this.loggedTraceIds.add(traceId);

      // Prevent memory leak by limiting the size of logged trace IDs
      if (this.loggedTraceIds.size > this.MAX_LOGGED_TRACES) {
        const firstTraceId = this.loggedTraceIds.values().next().value;
        if (firstTraceId) {
          this.loggedTraceIds.delete(firstTraceId);
        }
      }
    }
  }
}
