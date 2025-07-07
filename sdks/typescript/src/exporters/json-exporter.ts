import { ReadableSpan, SpanExporter } from '@opentelemetry/sdk-trace-base';
import { ExportResult, ExportResultCode } from '@opentelemetry/core';
import { SpanStatusCode, SpanKind } from '@opentelemetry/api';

import type { LilypadConfig } from '../types';
import type { SerializedSpan } from '../types/span';
import { logger } from '../utils/logger';
import { request } from '../utils/http-client';

export class JSONSpanExporter implements SpanExporter {
  private readonly config: LilypadConfig;
  private readonly loggedTraceIds = new Set<string>();
  private readonly MAX_LOGGED_TRACES = 1000;

  constructor(config: LilypadConfig) {
    this.config = config;
  }

  async export(
    spans: ReadableSpan[],
    resultCallback: (result: ExportResult) => void,
  ): Promise<void> {
    if (!spans || spans.length === 0) {
      resultCallback({ code: ExportResultCode.SUCCESS });
      return;
    }

    try {
      const spanData = spans.map((span) => this.spanToDict(span));

      const response = await request({
        url: `${this.config.baseUrl}/projects/${this.config.projectId}/traces`,
        method: 'POST',
        headers: {
          'X-API-Key': this.config.apiKey,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(spanData),
        timeout: 30000,
      });

      if (response.statusCode >= 200 && response.statusCode < 300) {
        const responseData = JSON.parse(response.body);
        this.logTraceUrls(responseData);
        resultCallback({ code: ExportResultCode.SUCCESS });
      } else {
        logger.error(`Failed to export spans: ${response.statusCode} ${response.body}`);
        resultCallback({ code: ExportResultCode.FAILED });
      }
    } catch (error) {
      logger.error('Error exporting spans:', error);
      resultCallback({ code: ExportResultCode.FAILED });
    }
  }

  async shutdown(): Promise<void> {
    // Nothing to clean up
    return Promise.resolve();
  }

  async forceFlush(): Promise<void> {
    // No buffering, so nothing to flush
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

    const result: SerializedSpan = {
      trace_id: spanContext.traceId,
      span_id: spanContext.spanId,
      parent_span_id: parentSpanId || null,
      instrumentation_scope: scope,
      resource: {
        attributes: span.resource.attributes,
        schema_url: null,
      },
      name: span.name,
      kind: SpanKind[span.kind],
      start_time: String(span.startTime[0] * 1e9 + span.startTime[1]), // Convert to nanoseconds string
      end_time: String(span.endTime[0] * 1e9 + span.endTime[1]), // Convert to nanoseconds string
      attributes: span.attributes || {},
      status: {
        status_code: SpanStatusCode[span.status.code],
        description: span.status.message,
      },
      events: span.events.map((event) => ({
        name: event.name,
        attributes: event.attributes || {},
        timestamp: String(event.time[0] * 1e9 + event.time[1]), // Convert to nanoseconds string
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

  private logTraceUrls(responseData: {
    trace_status?: string;
    span_count?: number;
    trace_ids?: string[];
  }): void {
    if (
      responseData.trace_status === 'queued' &&
      responseData.span_count &&
      responseData.span_count > 0
    ) {
      const uniqueTraceIds = [...new Set(responseData.trace_ids || [])];
      const newTraceIds = uniqueTraceIds.filter((tid) => !this.loggedTraceIds.has(tid));

      if (newTraceIds.length > 0) {
        newTraceIds.forEach((tid) => this.addLoggedTraceId(tid));

        if (newTraceIds.length === 1) {
          logger.info(
            `View trace at: ${this.config.remoteClientUrl}/projects/${this.config.projectId}/traces/${newTraceIds[0]}`,
          );
        } else {
          logger.info(
            `View ${newTraceIds.length} new traces at: ${this.config.remoteClientUrl}/projects/${this.config.projectId}/traces`,
          );
          newTraceIds.forEach((traceId) => {
            logger.debug(
              `  - ${this.config.remoteClientUrl}/projects/${this.config.projectId}/traces/${traceId}`,
            );
          });
        }
      }
    }
  }

  private addLoggedTraceId(traceId: string): void {
    // Prevent unbounded growth by removing oldest entries
    if (this.loggedTraceIds.size >= this.MAX_LOGGED_TRACES) {
      const firstId = this.loggedTraceIds.values().next().value;
      if (firstId) {
        this.loggedTraceIds.delete(firstId);
      }
    }
    this.loggedTraceIds.add(traceId);
  }
}
