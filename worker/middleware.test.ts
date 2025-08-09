import { OpenAPIHono } from '@hono/zod-openapi';
import { describe, expect, it } from 'vitest';
import { corsMiddleware, securityHeadersMiddleware } from './middleware';

const testApp = new OpenAPIHono();
testApp.use('*', corsMiddleware);
testApp.use('*', securityHeadersMiddleware);
testApp.get('/test', (c) => c.json({ ok: true }));
testApp.options('/test', (c) => c.text('OK')); // Handle OPTIONS requests

describe('CORS middleware', () => {
  describe('production environment', () => {
    it('allows specific production origins', async () => {
      const allowedOrigins = [
        'https://mirascope.com',
        'https://www.mirascope.com',
        'https://v1.lilypad.mirascope.com',
      ];

      for (const origin of allowedOrigins) {
        const res = await testApp.request(
          '/test',
          {
            method: 'OPTIONS', // Preflight request to trigger CORS headers
            headers: {
              Origin: origin,
              'Access-Control-Request-Method': 'GET',
            },
          },
          { ENVIRONMENT: 'production' }
        );

        expect(res.headers.get('Access-Control-Allow-Origin')).toBe(origin);
      }
    });

    it('blocks unauthorized origins including staging/preview URLs', async () => {
      const unauthorizedOrigins = [
        'https://evil.com',
        'https://malicious.site',
        'http://localhost:3000', // localhost not allowed in production
        'https://example.com',
        'https://staging.lilypad.mirascope.com', // staging not allowed in production
        'https://lilypad-pr-123.mirascope.workers.dev', // preview not allowed in production
      ];

      for (const origin of unauthorizedOrigins) {
        const res = await testApp.request(
          '/test',
          {
            headers: { Origin: origin },
          },
          { ENVIRONMENT: 'production' }
        );

        expect(res.headers.get('Access-Control-Allow-Origin')).toBeNull();
      }
    });

    it('handles missing origin header', async () => {
      const res = await testApp.request(
        '/test',
        {},
        { ENVIRONMENT: 'production' }
      );

      expect(res.headers.get('Access-Control-Allow-Origin')).toBeNull();
    });

    it('sets exact CORS configuration', async () => {
      const res = await testApp.request(
        '/test',
        {
          method: 'OPTIONS', // Preflight request to get all CORS headers
          headers: {
            Origin: 'https://mirascope.com',
            'Access-Control-Request-Method': 'GET',
          },
        },
        { ENVIRONMENT: 'production' }
      );

      // Assert exact headers to prevent accidental removal
      expect(res.headers.get('Access-Control-Allow-Methods')).toBe(
        'GET,POST,PUT,DELETE,OPTIONS'
      );
      expect(res.headers.get('Access-Control-Allow-Headers')).toBe(
        'Content-Type,Authorization,X-Requested-With,Accept,Origin'
      );
      expect(res.headers.get('Access-Control-Allow-Credentials')).toBe('true');
      expect(res.headers.get('Access-Control-Max-Age')).toBe('86400');
    });
  });

  describe('staging environment', () => {
    it('allows staging origin only', async () => {
      const res = await testApp.request(
        '/test',
        {
          method: 'OPTIONS',
          headers: {
            Origin: 'https://staging.lilypad.mirascope.com',
            'Access-Control-Request-Method': 'GET',
          },
        },
        { ENVIRONMENT: 'staging' }
      );

      expect(res.headers.get('Access-Control-Allow-Origin')).toBe(
        'https://staging.lilypad.mirascope.com'
      );
    });

    it('blocks production origins in staging', async () => {
      const productionOrigins = [
        'https://mirascope.com',
        'https://www.mirascope.com',
        'https://v1.lilypad.mirascope.com',
      ];

      for (const origin of productionOrigins) {
        const res = await testApp.request(
          '/test',
          {
            method: 'OPTIONS',
            headers: {
              Origin: origin,
              'Access-Control-Request-Method': 'GET',
            },
          },
          { ENVIRONMENT: 'staging' }
        );

        expect(res.headers.get('Access-Control-Allow-Origin')).toBeNull();
      }
    });

    it('blocks preview origins in staging', async () => {
      const previewOrigins = [
        'https://lilypad-pr-123.mirascope.workers.dev',
        'https://lilypad-pr-456.mirascope.workers.dev',
      ];

      for (const origin of previewOrigins) {
        const res = await testApp.request(
          '/test',
          {
            method: 'OPTIONS',
            headers: {
              Origin: origin,
              'Access-Control-Request-Method': 'GET',
            },
          },
          { ENVIRONMENT: 'staging' }
        );

        expect(res.headers.get('Access-Control-Allow-Origin')).toBeNull();
      }
    });
  });

  describe('preview environment', () => {
    it('allows staging origin', async () => {
      const res = await testApp.request(
        '/test',
        {
          method: 'OPTIONS',
          headers: {
            Origin: 'https://staging.lilypad.mirascope.com',
            'Access-Control-Request-Method': 'GET',
          },
        },
        { ENVIRONMENT: 'preview' }
      );

      expect(res.headers.get('Access-Control-Allow-Origin')).toBe(
        'https://staging.lilypad.mirascope.com'
      );
    });

    it('allows PR preview URLs', async () => {
      const previewUrls = [
        'https://lilypad-pr-123.mirascope.workers.dev',
        'https://lilypad-pr-456.mirascope.workers.dev',
        'https://lilypad-pr-1.mirascope.workers.dev',
      ];

      for (const origin of previewUrls) {
        const res = await testApp.request(
          '/test',
          {
            method: 'OPTIONS',
            headers: {
              Origin: origin,
              'Access-Control-Request-Method': 'GET',
            },
          },
          { ENVIRONMENT: 'preview' }
        );

        expect(res.headers.get('Access-Control-Allow-Origin')).toBe(origin);
      }
    });

    it('blocks production origins in preview', async () => {
      const productionOrigins = [
        'https://mirascope.com',
        'https://www.mirascope.com',
        'https://v1.lilypad.mirascope.com',
      ];

      for (const origin of productionOrigins) {
        const res = await testApp.request(
          '/test',
          {
            method: 'OPTIONS',
            headers: {
              Origin: origin,
              'Access-Control-Request-Method': 'GET',
            },
          },
          { ENVIRONMENT: 'preview' }
        );

        expect(res.headers.get('Access-Control-Allow-Origin')).toBeNull();
      }
    });

    it('blocks invalid PR preview URLs', async () => {
      const invalidUrls = [
        'https://lilypad-pr-abc.mirascope.workers.dev', // non-numeric PR
        'https://lilypad-pr-.mirascope.workers.dev', // missing PR number
        'https://lilypad-pr-123.evil.com', // wrong domain
        'http://lilypad-pr-123.mirascope.workers.dev', // HTTP instead of HTTPS
      ];

      for (const origin of invalidUrls) {
        const res = await testApp.request(
          '/test',
          {
            method: 'OPTIONS',
            headers: {
              Origin: origin,
              'Access-Control-Request-Method': 'GET',
            },
          },
          { ENVIRONMENT: 'preview' }
        );

        expect(res.headers.get('Access-Control-Allow-Origin')).toBeNull();
      }
    });
  });

  describe('local environment', () => {
    it('allows localhost origins', async () => {
      const localOrigins = [
        'http://localhost:3000',
        'http://localhost:5173',
        'https://localhost:3000',
        'http://127.0.0.1:3000',
        'https://127.0.0.1:5173',
      ];

      for (const origin of localOrigins) {
        const res = await testApp.request(
          '/test',
          {
            headers: { Origin: origin },
          },
          { ENVIRONMENT: 'local' }
        );

        expect(res.headers.get('Access-Control-Allow-Origin')).toBe(origin);
      }
    });

    it('allows missing origin in local environment', async () => {
      const res = await testApp.request(
        '/test',
        {
          method: 'OPTIONS',
          headers: {
            'Access-Control-Request-Method': 'GET',
          },
        },
        { ENVIRONMENT: 'local' }
      );

      // In local environment, no origin header means CORS middleware allows it
      // This typically results in no Access-Control-Allow-Origin header or '*'
      const allowOrigin = res.headers.get('Access-Control-Allow-Origin');
      expect(allowOrigin).toBeNull(); // Hono's CORS behavior for missing origin
    });

    it('blocks non-localhost origins in local environment', async () => {
      const nonLocalOrigins = ['https://evil.com', 'https://production.com'];

      for (const origin of nonLocalOrigins) {
        const res = await testApp.request(
          '/test',
          {
            method: 'OPTIONS',
            headers: {
              Origin: origin,
              'Access-Control-Request-Method': 'GET',
            },
          },
          { ENVIRONMENT: 'local' }
        );

        // These should fall through to allowed origins check which will fail
        expect(res.headers.get('Access-Control-Allow-Origin')).toBeNull();
      }
    });
  });
});

describe('Security headers middleware', () => {
  it('sets all required security headers for HTTPS requests', async () => {
    const res = await testApp.request(
      'https://example.com/test',
      {},
      { ENVIRONMENT: 'production' }
    );

    // Assert exact security headers to prevent accidental removal
    expect(res.headers.get('X-Content-Type-Options')).toBe('nosniff');
    expect(res.headers.get('X-Frame-Options')).toBe('DENY');
    expect(res.headers.get('X-XSS-Protection')).toBe('1; mode=block');
    expect(res.headers.get('Referrer-Policy')).toBe(
      'strict-origin-when-cross-origin'
    );
    expect(res.headers.get('Strict-Transport-Security')).toBe(
      'max-age=31536000; includeSubDomains'
    );
  });

  it('sets security headers for HTTP requests (no HSTS)', async () => {
    const res = await testApp.request(
      'http://example.com/test',
      {},
      { ENVIRONMENT: 'production' }
    );

    // Basic security headers should be present
    expect(res.headers.get('X-Content-Type-Options')).toBe('nosniff');
    expect(res.headers.get('X-Frame-Options')).toBe('DENY');
    expect(res.headers.get('X-XSS-Protection')).toBe('1; mode=block');
    expect(res.headers.get('Referrer-Policy')).toBe(
      'strict-origin-when-cross-origin'
    );

    // HSTS should NOT be present for HTTP requests
    expect(res.headers.get('Strict-Transport-Security')).toBeNull();
  });

  it('calls next middleware in chain', async () => {
    const res = await testApp.request(
      '/test',
      {},
      { ENVIRONMENT: 'production' }
    );

    // Verify the request reached our test endpoint
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data).toEqual({ ok: true });
  });
});
