/**
 * Type definitions for span serialization
 */

export interface SerializedSpan {
  trace_id: string;
  span_id: string;
  parent_span_id: string | null;
  name: string;
  kind: string;
  start_time: string;
  end_time: string;
  status: {
    status_code: string;
    description?: string;
  };
  attributes: Record<string, unknown>;
  events: Array<{
    name: string;
    timestamp: string;
    attributes: Record<string, unknown>;
  }>;
  links: Array<{
    context: {
      trace_id: string;
      span_id: string;
      trace_flags: string;
      trace_state?: string;
    };
    attributes: Record<string, unknown>;
  }>;
  resource: {
    attributes: Record<string, unknown>;
    schema_url?: string | null;
  };
  instrumentation_scope: {
    name: string | null;
    version: string | null;
    schema_url: string | null;
    attributes: Record<string, unknown>;
  };
  dropped_attributes_count?: number;
  dropped_events_count?: number;
  dropped_links_count?: number;
}

export interface SpanExportPayload {
  project_id: string;
  spans: SerializedSpan[];
}
