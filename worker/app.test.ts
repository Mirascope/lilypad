import type { HealthResponse } from '@/worker/schemas';
import { describe, expect, it } from 'vitest';
import app from './app';

const testEnv = {
  ENVIRONMENT: 'test',
  DATABASE_URL: 'postgresql://test@localhost/test',
};

describe('OpenAPI documentation', () => {
  it('serves OpenAPI spec at /openapi.json', async () => {
    const res = await app.request('/openapi.json', {}, testEnv);

    expect(res.status).toBe(200);
    expect(res.headers.get('Content-Type')).toContain('application/json');

    const spec = (await res.json()) as any; // the `OpenAPIObjectConfig` type is not exported anywhere
    expect(spec.openapi).toBe('3.1.0');
    expect(spec.info.title).toBe('Lilypad API');
    expect(spec.info.description).toBe(
      'Complete API documentation for Lilypad v1'
    );

    expect(spec.servers).toEqual([
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
    ]);

    expect(spec.tags).toEqual([
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
    ]);

    expect(spec.paths).toBeDefined();
    expect(spec.paths?.['/health']).toBeDefined();
    expect(spec.paths?.['/health']?.get).toBeDefined();
    expect(spec.paths?.['/health']?.get?.summary).toBe('Health check endpoint');
  });
});

describe('Swagger UI', () => {
  it('serves Swagger UI at /docs', async () => {
    const res = await app.request('/docs', {}, testEnv);

    expect(res.status).toBe(200);
    expect(res.headers.get('Content-Type')).toContain('text/html');

    const html = await res.text();
    expect(html).toContain('SwaggerUI');
    expect(html).toContain('/openapi.json');
  });
});

describe('Health endpoint', () => {
  it('returns health status with environment', async () => {
    const res = await app.request(
      '/health',
      {},
      { ...testEnv, ENVIRONMENT: 'production' }
    );

    expect(res.status).toBe(200);
    expect(res.headers.get('Content-Type')).toContain('application/json');

    const health = (await res.json()) as HealthResponse;
    expect(health.status).toBe('ok');
    expect(health.environment).toBe('production');
    expect(health.timestamp).toMatch(
      /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/
    );
  });

  it('handles missing environment variable', async () => {
    const res = await app.request(
      '/health',
      {},
      { DATABASE_URL: testEnv.DATABASE_URL }
    ); // No ENVIRONMENT but need DATABASE_URL

    expect(res.status).toBe(200);
    const health = (await res.json()) as HealthResponse;
    expect(health.status).toBe('ok');
    expect(health.environment).toBe('unknown');
    expect(health.timestamp).toMatch(
      /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/
    );
  });
});

describe('404 handler', () => {
  it('returns 404 for unknown paths with custom message', async () => {
    const testPaths = [
      '/unknown',
      '/nonexistent',
      '/random/path',
      '/api/unknown', // Should hit 404 before router
    ];

    for (const path of testPaths) {
      const res = await app.request(path, {}, testEnv);

      expect(res.status).toBe(404);
      expect(res.headers.get('Content-Type')).toContain('text/plain');

      const text = await res.text();
      expect(text).toBe(`Lilypad - Path not found: ${path}`);
    }
  });
});

// I haven't been able to figure this out yet, so will revisit up stack
// describe('Router mounting', () => {
//   it('calls app.route with correct router paths', async () => {
//     const routeSpy = vi.spyOn(OpenAPIHono.prototype, 'route');
//     vi.resetModules();
//     await import('./app');

//     expect(routeSpy).toHaveBeenNthCalledWith(1, '/auth', authRouter);
//     expect(routeSpy).toHaveBeenNthCalledWith(2, '/api', apiRouter);

//     routeSpy.mockRestore();
//   });
// });

// describe('Middleware mounting', () => {
//   it('calls app.use with correct middleware', async () => {
//     const useSpy = vi.spyOn(OpenAPIHono.prototype, 'use');
//     vi.resetModules();
//     await import('./app');

//     expect(useSpy).toHaveBeenNthCalledWith(1, '*', corsMiddleware);
//     expect(useSpy).toHaveBeenNthCalledWith(2, '*', securityHeadersMiddleware);
//     expect(useSpy).toHaveBeenNthCalledWith(3, '*', dbMiddleware);

//     useSpy.mockRestore();
//   });
// });
