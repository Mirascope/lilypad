import { cors } from 'hono/cors';
import { createMiddleware } from 'hono/factory';

export const corsMiddleware = createMiddleware(async (c, next) => {
  const corsMiddlewareHandler = cors({
    origin: (origin) => {
      let allowedOrigins: string[] = [];

      if (c.env.ENVIRONMENT === 'production') {
        allowedOrigins = [
          'https://mirascope.com',
          'https://www.mirascope.com',
          'https://v1.lilypad.mirascope.com',
        ];
      } else if (c.env.ENVIRONMENT === 'staging') {
        allowedOrigins = ['https://staging.lilypad.mirascope.com'];
      } else if (c.env.ENVIRONMENT === 'preview') {
        allowedOrigins = ['https://staging.lilypad.mirascope.com'];

        // Allow PR preview URLs
        if (
          origin &&
          origin.match(/^https:\/\/lilypad-pr-\d+\.mirascope\.workers\.dev$/)
        ) {
          return origin;
        }
      } else if (c.env.ENVIRONMENT === 'local') {
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

  return corsMiddlewareHandler(c, next);
});

export const securityHeadersMiddleware = createMiddleware(async (c, next) => {
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
