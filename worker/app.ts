import { dbMiddleware } from '@/db/middleware';
import { apiRouter } from '@/worker/api';
import { authRouter } from '@/worker/auth';
import type { Environment } from '@/worker/environment';
import { corsMiddleware, securityHeadersMiddleware } from '@/worker/middleware';
import { healthRoute } from '@/worker/routes';
import { swaggerUI } from '@hono/swagger-ui';
import { OpenAPIHono } from '@hono/zod-openapi';

const app = new OpenAPIHono<{ Bindings: Environment }>();

app.use('*', corsMiddleware);
app.use('*', securityHeadersMiddleware);
app.use('*', dbMiddleware);

app.doc('/openapi.json', {
  openapi: '3.1.0',
  info: {
    title: 'Lilypad API',
    version: '1.0.0-alpha.0',
    description: 'Complete API documentation for Lilypad v1',
  },
  servers: [
    {
      url: 'https://v1.lilypad.mirascope.com',
      description: 'Production server',
      'x-fern-server-name': 'production',
    },
    {
      url: 'https://staging.lilypad.mirascope.com',
      description: 'Staging server',
      'x-fern-server-name': 'staging',
    },
    {
      url: 'http://localhost:3000',
      description: 'Local development server',
      'x-fern-server-name': 'local',
    },
  ],
  tags: [
    {
      name: 'Authentication',
      description: 'OAuth authentication and session management',
    },
    {
      name: 'API',
      description: 'Core API endpoints',
    },
    {
      name: 'Telemetry',
      description: 'OpenTelemetry trace collection endpoints (debug)',
    },
  ],
});

app.get('/docs', swaggerUI({ url: '/openapi.json' }));

app.route('/auth', authRouter);
app.route('/api', apiRouter);

app.openapi(healthRoute, (c) => {
  return c.json({
    status: 'ok' as const,
    timestamp: new Date().toISOString(),
    environment: c.env.ENVIRONMENT || 'unknown',
  });
});

app.notFound((c) => {
  return c.text(`Lilypad - Path not found: ${c.req.path}`, 404);
});

export default app;
