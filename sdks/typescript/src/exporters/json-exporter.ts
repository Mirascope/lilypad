import { ReadableSpan, SpanExporter } from '@opentelemetry/sdk-trace-base';
import { ExportResult, ExportResultCode } from '@opentelemetry/core';
import { SpanStatusCode, SpanKind } from '@opentelemetry/api';

import type { LilypadConfig } from '../types';
import type { SerializedSpan } from '../types/span';
import { logger } from '../utils/logger';
import { LilypadClient } from '../../lilypad/generated';
import type { TracesQueueResponse } from '../../lilypad/generated/api/types';

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

      // Use the custom traces create method with body
      const response = await this.createTracesWithBody(this.config.projectId, spanData, {
        timeoutInSeconds: 30,
      });

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
      attributes: span.attributes || {},
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

  private async createTracesWithBody(
    projectUuid: string,
    spanData: SerializedSpan[],
    requestOptions?: LilypadClient.RequestOptions,
  ): Promise<TracesQueueResponse> {
    // Access the client's internal options and make a custom request
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const clientOptions = (this.client as any)._options;
    const { fetcher } = await import('../../lilypad/generated/core/fetcher');

    // Get base URL - prefer baseUrl over environment
    const baseUrl = (await clientOptions.baseUrl) || (await clientOptions.environment);
    const fullUrl = `${baseUrl}/projects/${encodeURIComponent(projectUuid)}/traces`;

    logger.info(`[EXPORT] Exporting to URL: ${fullUrl}`);
    logger.info(`[EXPORT] Using API Key: ${(await clientOptions.apiKey) ? '[REDACTED]' : 'None'}`);
    logger.info(`[EXPORT] Sending ${spanData.length} spans`);
    logger.debug(`[EXPORT] Request body: ${JSON.stringify(spanData, null, 2)}`);

    // Log the exact timestamp for correlation with server logs
    const exportTimestamp = new Date().toISOString();
    logger.info(`[EXPORT] Export timestamp: ${exportTimestamp}`);

    let response;
    try {
      response = await fetcher<TracesQueueResponse>({
        url: fullUrl,
        method: 'POST',
        headers: {
          'X-API-Key': await clientOptions.apiKey,
          'Content-Type': 'application/json',
          ...(requestOptions?.headers || {}),
        },
        body: spanData,
        requestType: 'json',
        timeoutMs: (requestOptions?.timeoutInSeconds || 30) * 1000,
        maxRetries: requestOptions?.maxRetries,
        abortSignal: requestOptions?.abortSignal,
      });
    } catch (fetchError) {
      logger.error(
        `[EXPORT] ❌ Fetch error: ${fetchError instanceof Error ? fetchError.message : String(fetchError)}`,
      );
      if (fetchError instanceof Error && 'cause' in fetchError) {
        logger.error(`[EXPORT] ❌ Fetch error cause: ${JSON.stringify(fetchError.cause)}`);
      }
      throw fetchError;
    }

    if (response.ok) {
      logger.info(`[EXPORT] ✅ Export successful - Response: ${JSON.stringify(response.body)}`);
      return response.body;
    }

    // Handle errors similar to the generated client
    if (response.error.reason === 'status-code') {
      logger.error(
        `[EXPORT] ❌ HTTP Error ${response.error.statusCode}: ${JSON.stringify(response.error.body)}`,
      );
      throw new Error(
        `Failed to export spans: ${response.error.statusCode} ${JSON.stringify(response.error.body)}`,
      );
    }

    switch (response.error.reason) {
      case 'timeout':
        logger.error('[EXPORT] ❌ Request timeout');
        throw new Error('Timeout exceeded when calling POST /projects/{project_uuid}/traces.');
      case 'unknown':
        logger.error(`[EXPORT] ❌ Unknown error: ${response.error.errorMessage}`);
        throw new Error(response.error.errorMessage);
      case 'non-json':
        logger.error(
          `[EXPORT] ❌ Non-JSON response ${response.error.statusCode}: ${response.error.rawBody}`,
        );
        throw new Error(
          `Failed to export spans: ${response.error.statusCode} ${response.error.rawBody}`,
        );
    }
  }

  private logTraceUrls(responseData: TracesQueueResponse): void {
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
