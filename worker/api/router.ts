import { OpenAPIHono } from '@hono/zod-openapi';

import type { Environment } from '@/worker/environment';
import { tracesRoute, type TraceRequest, type TraceResponse } from './traces';

export const apiRouter = new OpenAPIHono<{
  Bindings: Environment;
}>();

apiRouter.openapi(tracesRoute, async (c) => {
  const traceData = await c.req.json<TraceRequest>();

  const serviceName =
    traceData.resourceSpans?.[0]?.resource?.attributes?.find(
      (attr) => attr.key === 'service.name'
    )?.value?.stringValue || 'unknown';

  let totalSpans = 0;
  traceData.resourceSpans?.forEach((rs) => {
    rs.scopeSpans?.forEach((ss) => {
      totalSpans += ss.spans?.length || 0;
    });
  });

  console.log(
    `[TRACE DEBUG] Received ${totalSpans} spans from service: ${serviceName}`
  );
  console.log(
    '[TRACE DEBUG] Full trace data:',
    JSON.stringify(traceData, null, 2)
  );

  const response: TraceResponse = {
    partialSuccess: {},
  };

  return c.json(response);
});
