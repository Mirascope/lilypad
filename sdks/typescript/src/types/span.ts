/**
 * Type definitions for span serialization
 */

export interface SerializedSpan {
  trace_id: string;
  span_id: string;
  parent_span_id: string | null;
  name: string;
  kind: string;
  start_time: number;
  end_time: number;
  type?: string;
  status: string; // Just the status code string, not an object
  session_id?: string | null; // Optional session ID from attributes
  attributes: Record<string, unknown>;
  events: Array<{
    name: string;
    timestamp: number;
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
  resource: string; // JSON string representation of resource object
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

/**
 * Type definitions for span attributes
 */
export type SpanAttributeValue = string | number | boolean;
export type SpanAttributeArray = SpanAttributeValue[];
export type SpanAttributesValue = SpanAttributeValue | SpanAttributeArray;

export interface SpanMetadata {
  [key: string]: unknown;
}

/**
 * Span limits based on OpenTelemetry specifications
 */
export const SPAN_LIMITS = {
  MAX_ATTRIBUTES_COUNT: 128,
  MAX_ATTRIBUTE_VALUE_LENGTH: 10000,
  MAX_EVENT_COUNT: 128,
  MAX_LINK_COUNT: 128,
} as const;
