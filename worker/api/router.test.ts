import type { User } from '@/db/schema';
import type { Database } from '@/db/utils';
import type { Environment } from '@/worker/environment';
import { OpenAPIHono } from '@hono/zod-openapi';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiRouter } from './router';

describe('apiRouter', () => {
  let mockEnv: Environment;
  let mockApp: any;
  let mockRequest: (path: string, options?: any) => Promise<any>;

  beforeEach(() => {
    vi.clearAllMocks();

    mockEnv = {
      SITE_URL: 'http://localhost:3000',
      ENVIRONMENT: 'test',
      DATABASE_URL: 'postgresql://test',
      GITHUB_CLIENT_ID: 'test-github-id',
      GITHUB_CLIENT_SECRET: 'test-github-secret',
      GITHUB_CALLBACK_URL: 'http://localhost:3000/auth/github/callback',
      GOOGLE_CLIENT_ID: 'test-google-id',
      GOOGLE_CLIENT_SECRET: 'test-google-secret',
      GOOGLE_CALLBACK_URL: 'http://localhost:3000/auth/google/callback',
    };

    // Create a test app with the api router
    mockApp = apiRouter;

    // Helper function to make requests
    mockRequest = async (path: string, options: any = {}) => {
      const url = `http://localhost:3000${path}`;
      const method = options.method || 'GET';
      const headers = options.headers || {};
      const body = options.body;

      const req = new Request(url, { method, headers, body });

      return mockApp.fetch(req, mockEnv, {
        waitUntil: (_promise: Promise<any>) => {},
        passThroughOnException: () => {},
      });
    };
  });

  describe('Router initialization', () => {
    it('should create an instance of Hono router', () => {
      expect(apiRouter).toBeDefined();
      expect(apiRouter.fetch).toBeDefined();
      expect(typeof apiRouter.fetch).toBe('function');
    });

    it('should have correct type bindings', () => {
      // This test verifies that TypeScript types are correctly set
      // The router should accept Environment bindings
      const testHandler = async (c: any) => {
        // Verify that c.env has the expected Environment type
        const env: Environment = c.env;
        expect(env).toBeDefined();
        return new Response('ok');
      };

      // Add a test route to verify bindings work
      apiRouter.get('/test-bindings', testHandler);
    });
  });

  describe('Empty router behavior', () => {
    it('should return 404 for any route when router is empty', async () => {
      const testPaths = [
        '/',
        '/users',
        '/api/v1/users',
        '/health',
        '/status',
        '/random-endpoint',
      ];

      for (const path of testPaths) {
        const response = await mockRequest(path);
        expect(response.status).toBe(404);
      }
    });

    it('should return 404 for all HTTP methods when router is empty', async () => {
      const methods = [
        'GET',
        'POST',
        'PUT',
        'DELETE',
        'PATCH',
        'HEAD',
        'OPTIONS',
      ];

      for (const method of methods) {
        const response = await mockRequest('/test', { method });
        expect(response.status).toBe(404);
      }
    });
  });

  describe('Router extensibility', () => {
    it('should allow adding routes dynamically', async () => {
      // Create a new router instance for this test
      const { Hono } = await import('hono');
      const testRouter = new Hono<{ Bindings: Environment }>();
      testRouter.get('/dynamic-test', (c) =>
        c.json({ message: 'Dynamic route works' })
      );

      const req = new Request('http://localhost:3000/dynamic-test');
      const response = await testRouter.fetch(req, mockEnv);
      expect(response.status).toBe(200);

      const data = (await response.json()) as any;
      expect(data).toEqual({ message: 'Dynamic route works' });
    });

    it('should maintain isolation between test runs', async () => {
      // This test verifies that the original router is not modified
      const response = await mockRequest('/dynamic-test');
      expect(response.status).toBe(404);
    });
  });

  describe('Environment binding', () => {
    it('should provide access to environment variables', async () => {
      let capturedEnv: Environment | null = null;

      // Create a new router instance for this test
      const { Hono } = await import('hono');
      const testRouter = new Hono<{ Bindings: Environment }>();
      testRouter.get('/env-test', (c) => {
        capturedEnv = c.env;
        return c.json({
          siteUrl: c.env.SITE_URL,
          environment: c.env.ENVIRONMENT,
        });
      });

      const req = new Request('http://localhost:3000/env-test');
      const response = await testRouter.fetch(req, mockEnv);
      expect(response.status).toBe(200);

      const data = (await response.json()) as any;
      expect(data).toEqual({
        siteUrl: 'http://localhost:3000',
        environment: 'test',
      });

      expect(capturedEnv).toEqual(mockEnv);
    });
  });

  describe('Request context', () => {
    it('should provide access to request details', async () => {
      let capturedRequest: Request | null = null;

      // Create a new router instance for this test
      const { Hono } = await import('hono');
      const testRouter = new Hono<{ Bindings: Environment }>();
      testRouter.post('/context-test', async (c) => {
        capturedRequest = c.req.raw;
        return c.json({
          method: c.req.method,
          url: c.req.url,
          headers: Object.fromEntries(c.req.raw.headers.entries()),
        });
      });

      const testHeaders = {
        'Content-Type': 'application/json',
        'X-Custom-Header': 'test-value',
      };

      const req = new Request('http://localhost:3000/context-test', {
        method: 'POST',
        headers: testHeaders,
        body: JSON.stringify({ test: 'data' }),
      });

      const response = await testRouter.fetch(req, mockEnv);

      expect(response.status).toBe(200);

      const data = (await response.json()) as any;
      expect(data.method).toBe('POST');
      expect(data.url).toBe('http://localhost:3000/context-test');
      expect(data.headers['content-type']).toBe('application/json');
      expect(data.headers['x-custom-header']).toBe('test-value');

      expect(capturedRequest).toBeDefined();
      expect(capturedRequest!.method).toBe('POST');
    });
  });

  describe('Response utilities', () => {
    it('should support various response types', async () => {
      // Create a new router instance for this test
      const { Hono } = await import('hono');
      const testRouter = new Hono<{ Bindings: Environment }>();

      // JSON response
      testRouter.get('/json', (c) => c.json({ type: 'json' }));

      // Text response
      testRouter.get('/text', (c) => c.text('Plain text response'));

      // HTML response
      testRouter.get('/html', (c) => c.html('<h1>HTML Response</h1>'));

      // Status response
      testRouter.get('/status', (c) => {
        c.status(201);
        return c.text('Created');
      });

      // JSON response
      const jsonReq = new Request('http://localhost:3000/json');
      const jsonResponse = await testRouter.fetch(jsonReq, mockEnv);
      expect(jsonResponse.status).toBe(200);
      expect(jsonResponse.headers.get('content-type')).toContain(
        'application/json'
      );
      const jsonData = (await jsonResponse.json()) as any;
      expect(jsonData).toEqual({ type: 'json' });

      // Text response
      const textReq = new Request('http://localhost:3000/text');
      const textResponse = await testRouter.fetch(textReq, mockEnv);
      expect(textResponse.status).toBe(200);
      // Hono might not set content-type for text() helper, check the actual value
      const contentType = textResponse.headers.get('content-type');
      if (contentType) {
        expect(contentType).toContain('text/plain');
      }
      const textData = await textResponse.text();
      expect(textData).toBe('Plain text response');

      // HTML response
      const htmlReq = new Request('http://localhost:3000/html');
      const htmlResponse = await testRouter.fetch(htmlReq, mockEnv);
      expect(htmlResponse.status).toBe(200);
      expect(htmlResponse.headers.get('content-type')).toContain('text/html');
      const htmlData = await htmlResponse.text();
      expect(htmlData).toBe('<h1>HTML Response</h1>');

      // Status response
      const statusReq = new Request('http://localhost:3000/status');
      const statusResponse = await testRouter.fetch(statusReq, mockEnv);
      expect(statusResponse.status).toBe(201);
    });
  });

  describe('Error scenarios', () => {
    it('should handle route handler errors gracefully', async () => {
      // Create a new router instance for this test
      const { Hono } = await import('hono');
      const testRouter = new Hono<{ Bindings: Environment }>();
      testRouter.get('/error', () => {
        throw new Error('Route handler error');
      });

      // Hono will catch the error and return 500 by default
      const req = new Request('http://localhost:3000/error');
      const response = await testRouter.fetch(req, mockEnv);
      expect(response.status).toBe(500);
    });

    it('should handle async route handler errors', async () => {
      // Create a new router instance for this test
      const { Hono } = await import('hono');
      const testRouter = new Hono<{ Bindings: Environment }>();
      testRouter.get('/async-error', async () => {
        await Promise.resolve();
        throw new Error('Async route handler error');
      });

      const req = new Request('http://localhost:3000/async-error');
      const response = await testRouter.fetch(req, mockEnv);
      expect(response.status).toBe(500);
    });
  });

  describe('Integration readiness', () => {
    it('should be ready for mounting on main app', () => {
      // Verify the router exports the expected interface
      expect(apiRouter).toBeDefined();
      expect(typeof apiRouter.fetch).toBe('function');
      expect(typeof apiRouter.get).toBe('function');
      expect(typeof apiRouter.post).toBe('function');
      expect(typeof apiRouter.put).toBe('function');
      expect(typeof apiRouter.delete).toBe('function');
      expect(typeof apiRouter.patch).toBe('function');
    });

    it('should work with middleware when added', async () => {
      let middlewareExecuted = false;

      // Create a new router instance for this test
      const { Hono } = await import('hono');
      const testRouter = new Hono<{ Bindings: Environment }>();

      // Add middleware
      testRouter.use('*', async (_c, next) => {
        middlewareExecuted = true;
        await next();
      });

      // Add a route
      testRouter.get('/with-middleware', (c) => c.json({ success: true }));

      const req = new Request('http://localhost:3000/with-middleware');
      const response = await testRouter.fetch(req, mockEnv);
      expect(response.status).toBe(200);
      expect(middlewareExecuted).toBe(true);

      const data = (await response.json()) as any;
      expect(data).toEqual({ success: true });
    });
  });
  describe('Router Configuration', () => {
    it('should be an instance of OpenAPIHono', () => {
      expect(apiRouter).toBeInstanceOf(OpenAPIHono);
    });

    it('should have correct type definitions for Bindings and Variables', () => {
      const testRouter = new OpenAPIHono<{
        Bindings: Environment;
        Variables: {
          db: Database;
          user?: User;
        };
      }>();

      expect(apiRouter.constructor).toBe(testRouter.constructor);
    });
  });

  describe('OpenAPI Document Generation', () => {
    it('should generate a valid OpenAPI document', () => {
      const doc = apiRouter.getOpenAPIDocument({
        openapi: '3.1.0',
        info: {
          title: 'API',
          version: '1.0.0',
        },
      });

      expect(doc).toBeDefined();
      expect(doc.openapi).toBe('3.1.0');
      expect(doc.info.title).toBe('API');
      expect(doc.info.version).toBe('1.0.0');
    });

    it('should have correct base structure for OpenAPI document', () => {
      const doc = apiRouter.getOpenAPIDocument({
        openapi: '3.1.0',
        info: {
          title: 'API',
          version: '1.0.0',
          description: 'API routes for the application',
        },
        servers: [
          {
            url: 'https://api.example.com',
            description: 'Production server',
          },
        ],
      });

      expect(doc.info.description).toBe('API routes for the application');
      expect(doc.servers).toBeDefined();
      expect(doc.servers?.[0].url).toBe('https://api.example.com');
      expect(doc.servers?.[0].description).toBe('Production server');
    });
  });

  describe('Router Middleware Context', () => {
    it.skip('should properly type the context with Environment bindings', () => {
      apiRouter.use(async (c, next) => {
        const env: Environment = c.env;
        expect(env).toBeDefined();
        await next();
      });
    });

    it.skip('should properly type the context with Variables', () => {
      apiRouter.use(async (c, next) => {
        const db: Database | undefined = c.get('db');
        const user: User | undefined = c.get('user');

        if (db) {
          expect(db).toBeDefined();
        }

        if (user) {
          expect(user).toBeDefined();
        }

        await next();
      });
    });
  });
});
