import { createRoute, z } from '@hono/zod-openapi';

const KeyValueSchema = z.object({
  key: z.string(),
  value: z.object({
    stringValue: z.string().optional(),
    intValue: z.string().optional(),
    doubleValue: z.number().optional(),
    boolValue: z.boolean().optional(),
    arrayValue: z.any().optional(),
    kvlistValue: z.any().optional(),
  }),
});

const ResourceSchema = z.object({
  attributes: z.array(KeyValueSchema).optional(),
  droppedAttributesCount: z.number().optional(),
});

const SpanStatusSchema = z.object({
  code: z.number().optional(),
  message: z.string().optional(),
});

const SpanSchema = z.object({
  traceId: z.string(),
  spanId: z.string(),
  parentSpanId: z.string().optional(),
  name: z.string(),
  kind: z.number().optional(),
  startTimeUnixNano: z.string(),
  endTimeUnixNano: z.string(),
  attributes: z.array(KeyValueSchema).optional(),
  droppedAttributesCount: z.number().optional(),
  events: z.array(z.any()).optional(),
  droppedEventsCount: z.number().optional(),
  status: SpanStatusSchema.optional(),
  links: z.array(z.any()).optional(),
  droppedLinksCount: z.number().optional(),
});

const InstrumentationScopeSchema = z.object({
  name: z.string(),
  version: z.string().optional(),
  attributes: z.array(KeyValueSchema).optional(),
  droppedAttributesCount: z.number().optional(),
});

const ScopeSpansSchema = z.object({
  scope: InstrumentationScopeSchema.optional(),
  spans: z.array(SpanSchema),
  schemaUrl: z.string().optional(),
});

const ResourceSpansSchema = z.object({
  resource: ResourceSchema.optional(),
  scopeSpans: z.array(ScopeSpansSchema),
  schemaUrl: z.string().optional(),
});

export const TraceRequestSchema = z.object({
  resourceSpans: z.array(ResourceSpansSchema),
});

export const TraceResponseSchema = z.object({
  partialSuccess: z
    .object({
      rejectedSpans: z.number().optional(),
      errorMessage: z.string().optional(),
    })
    .optional(),
});

export type TraceRequest = z.infer<typeof TraceRequestSchema>;
export type TraceResponse = z.infer<typeof TraceResponseSchema>;

export const tracesRoute = createRoute({
  method: 'post',
  path: '/v1/traces',
  tags: ['Telemetry'],
  summary: 'Debug endpoint for OpenTelemetry traces',
  description:
    'Temporary endpoint to receive and log OpenTelemetry trace data for debugging purposes. This endpoint follows the OTLP/HTTP specification.',
  request: {
    body: {
      content: {
        'application/json': {
          schema: TraceRequestSchema,
        },
      },
    },
  },
  responses: {
    200: {
      content: {
        'application/json': {
          schema: TraceResponseSchema,
        },
      },
      description: 'Trace export acknowledged',
    },
    400: {
      description: 'Invalid request format',
    },
    500: {
      description: 'Internal server error',
    },
  },
});
