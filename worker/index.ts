import { swaggerUI } from '@hono/swagger-ui';
import { OpenAPIHono } from '@hono/zod-openapi';
import { cors } from 'hono/cors';

import { dbMiddleware } from '@/db/middleware';
import { deleteExpiredSessions } from '@/db/operations';
import { createDbConnection } from '@/db/utils';
import { apiRouter } from '@/worker/api';
import { authRouter } from '@/worker/auth';
import type { Environment } from '@/worker/environment';

const app = new OpenAPIHono<{ Bindings: Environment }>();

app.use('*', async (c, next) => {
  const corsMiddleware = cors({
    origin: (origin) => {
      const allowedOrigins = [
        'https://mirascope.com',
        'https://www.mirascope.com',
        'https://lilypad.mirascope.com',
        'https://v1.lilypad.mirascope.com',
      ];

      if (c.env.ENVIRONMENT === 'local') {
        if (
          !origin ||
          origin.includes('localhost') ||
          origin.includes('127.0.0.1')
        ) {
          return origin;
        }
      }

      return allowedOrigins.includes(origin || '') ? origin : null;
    },
    allowHeaders: [
      'Content-Type',
      'Authorization',
      'X-Requested-With',
      'Accept',
      'Origin',
    ],
    allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    credentials: true,
    maxAge: 86400,
  });

  return corsMiddleware(c, next);
});

app.use('*', async (c, next) => {
  c.header('X-Content-Type-Options', 'nosniff');
  c.header('X-Frame-Options', 'DENY');
  c.header('X-XSS-Protection', '1; mode=block');
  c.header('Referrer-Policy', 'strict-origin-when-cross-origin');

  if (c.req.url.startsWith('https://')) {
    c.header(
      'Strict-Transport-Security',
      'max-age=31536000; includeSubDomains'
    );
  }

  await next();
});

app.use('*', dbMiddleware);

app.doc('/openapi.json', {
  openapi: '3.0.0',
  info: {
    title: 'Lilypad API',
    version: '1.0.0-alpha.0',
    description: 'Complete API documentation for Lilypad v1',
  },
  servers: [
    {
      url: 'https://v1.lilypad.mirascope.com',
      description: 'Production server',
    },
    {
      url: 'https://staging.lilypad.mirascope.com',
      description: 'Staging server',
    },
    {
      url: 'http://localhost:3000',
      description: 'Local development server',
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
  ],
  // components: {
  //   securitySchemes: {
  //     cookieAuth: {
  //       type: 'apiKey',
  //       in: 'cookie',
  //       name: 'session',
  //       description: 'Session cookie authentication',
  //     },
  //   },
  // },
});

app.route('/auth', authRouter);
app.route('/api', apiRouter);

app.get('/health', (c) => {
  return c.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    environment: c.env.ENVIRONMENT || 'unknown',
  });
});

app.get('/docs', swaggerUI({ url: '/openapi.json' }));

app.notFound((c) => {
  return c.text(`Lilypad - Path not found: ${c.req.path}`, 404);
});

export default {
  fetch: app.fetch,

  async scheduled(
    controller: ScheduledController,
    env: Environment
  ): Promise<void> {
    console.log(`Running scheduled job: ${controller.cron}`);
    switch (controller.cron) {
      case '0 0 * * 7': // Weekly on Sunday at midnight
        const db = createDbConnection(env.DATABASE_URL);
        await deleteExpiredSessions(db);
        break;
      default:
        console.warn(`Unknown cron job: ${controller.cron}`);
    }
    console.log(`Completed scheduled job: ${controller.cron}`);
  },
};
