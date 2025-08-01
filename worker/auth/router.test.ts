import type { Environment } from '@/worker/environment';
import { Hono } from 'hono';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import * as logout from './logout';
import * as me from './me';
import * as middleware from './middleware';
import * as oauth from './oauth';
import * as initiateModule from './oauth/initiate';
import { authRouter } from './router';

// Mock all dependencies
vi.mock('./logout');
vi.mock('./me');
vi.mock('./middleware');
vi.mock('./oauth');
vi.mock('./oauth/initiate');

describe('authRouter', () => {
  let mockEnv: Environment;
  let mockDb: any;
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

    mockDb = { db: 'mock' };

    // Mock middleware to pass through
    vi.mocked(middleware.authSessionMiddleware).mockImplementation(
      async (_c, next) => next()
    );

    // Create a test app with the auth router
    mockApp = authRouter;

    // Helper function to make requests
    mockRequest = async (path: string, options: any = {}) => {
      const url = `http://localhost:3000${path}`;
      const method = options.method || 'GET';
      const headers = options.headers || {};
      const body = options.body;

      const req = new Request(url, { method, headers, body });

      return mockApp.fetch(req, mockEnv, {
        waitUntil: () => {},
        passThroughOnException: () => {},
        db: mockDb,
      });
    };
  });

  describe('GitHub OAuth routes', () => {
    it('should handle GET /github to initiate OAuth', async () => {
      const mockProvider = { name: 'github' };
      const mockResponse = new Response(null, { status: 302 });

      vi.mocked(oauth.createGitHubProvider).mockReturnValue(
        mockProvider as any
      );
      vi.mocked(initiateModule.initiateOAuth).mockResolvedValue(mockResponse);

      const response = await mockRequest('/github');

      expect(oauth.createGitHubProvider).toHaveBeenCalledWith(mockEnv);
      expect(initiateModule.initiateOAuth).toHaveBeenCalledWith(
        mockProvider,
        'http://localhost:3000'
      );
      expect(response).toBe(mockResponse);
    });

    it('should handle GET /github/callback', async () => {
      const mockProvider = { name: 'github' };
      const mockResponse = new Response(null, { status: 302 });

      vi.mocked(oauth.createGitHubProvider).mockReturnValue(
        mockProvider as any
      );
      vi.mocked(oauth.handleOAuthCallback).mockResolvedValue(mockResponse);

      const response = await mockRequest(
        '/github/callback?code=test&state=test'
      );

      expect(oauth.createGitHubProvider).toHaveBeenCalledWith(mockEnv);
      expect(oauth.handleOAuthCallback).toHaveBeenCalledWith(
        expect.objectContaining({
          req: expect.objectContaining({
            url: 'http://localhost:3000/github/callback?code=test&state=test',
          }),
          env: mockEnv,
          get: expect.any(Function),
        }),
        mockProvider
      );
      expect(response).toBe(mockResponse);
    });

    it('should handle GET /github/proxy-callback', async () => {
      const mockResponse = new Response(null, { status: 302 });

      vi.mocked(oauth.handleOAuthProxyCallback).mockResolvedValue(mockResponse);

      const response = await mockRequest(
        '/github/proxy-callback?code=test&state=test'
      );

      expect(oauth.handleOAuthProxyCallback).toHaveBeenCalledWith(
        expect.objectContaining({
          req: expect.objectContaining({
            url: 'http://localhost:3000/github/proxy-callback?code=test&state=test',
          }),
          env: mockEnv,
        }),
        'github'
      );
      expect(response).toBe(mockResponse);
    });
  });

  describe('Google OAuth routes', () => {
    it('should handle GET /google to initiate OAuth', async () => {
      const mockProvider = { name: 'google' };
      const mockResponse = new Response(null, { status: 302 });

      vi.mocked(oauth.createGoogleProvider).mockReturnValue(
        mockProvider as any
      );
      vi.mocked(initiateModule.initiateOAuth).mockResolvedValue(mockResponse);

      const response = await mockRequest('/google');

      expect(oauth.createGoogleProvider).toHaveBeenCalledWith(mockEnv);
      expect(initiateModule.initiateOAuth).toHaveBeenCalledWith(
        mockProvider,
        'http://localhost:3000'
      );
      expect(response).toBe(mockResponse);
    });

    it('should handle GET /google/callback', async () => {
      const mockProvider = { name: 'google' };
      const mockResponse = new Response(null, { status: 302 });

      vi.mocked(oauth.createGoogleProvider).mockReturnValue(
        mockProvider as any
      );
      vi.mocked(oauth.handleOAuthCallback).mockResolvedValue(mockResponse);

      const response = await mockRequest(
        '/google/callback?code=test&state=test'
      );

      expect(oauth.createGoogleProvider).toHaveBeenCalledWith(mockEnv);
      expect(oauth.handleOAuthCallback).toHaveBeenCalledWith(
        expect.objectContaining({
          req: expect.objectContaining({
            url: 'http://localhost:3000/google/callback?code=test&state=test',
          }),
          env: mockEnv,
          get: expect.any(Function),
        }),
        mockProvider
      );
      expect(response).toBe(mockResponse);
    });

    it('should handle GET /google/proxy-callback', async () => {
      const mockResponse = new Response(null, { status: 302 });

      vi.mocked(oauth.handleOAuthProxyCallback).mockResolvedValue(mockResponse);

      const response = await mockRequest(
        '/google/proxy-callback?code=test&state=test'
      );

      expect(oauth.handleOAuthProxyCallback).toHaveBeenCalledWith(
        expect.objectContaining({
          req: expect.objectContaining({
            url: 'http://localhost:3000/google/proxy-callback?code=test&state=test',
          }),
          env: mockEnv,
        }),
        'google'
      );
      expect(response).toBe(mockResponse);
    });
  });

  describe('Auth management routes', () => {
    it('should handle POST /logout', async () => {
      const mockResponse = { success: true };

      vi.mocked(logout.handleLogout).mockResolvedValue(mockResponse as any);

      const response = await mockRequest('/logout', { method: 'POST' });

      expect(logout.handleLogout).toHaveBeenCalledWith(
        expect.objectContaining({
          req: expect.objectContaining({
            method: 'POST',
          }),
          env: mockEnv,
          get: expect.any(Function),
        })
      );
      expect(response).toBe(mockResponse);
    });

    it('should handle GET /me with auth middleware', async () => {
      const mockResponse = { user: { id: '123' } };
      let middlewareCalled = false;

      vi.mocked(middleware.authSessionMiddleware).mockImplementation(
        async (_c, next) => {
          middlewareCalled = true;
          return next();
        }
      );

      vi.mocked(me.handleMe).mockResolvedValue(mockResponse as any);

      const response = await mockRequest('/me');

      expect(middlewareCalled).toBe(true);
      expect(me.handleMe).toHaveBeenCalledWith(
        expect.objectContaining({
          req: expect.objectContaining({
            method: 'GET',
          }),
          env: mockEnv,
          get: expect.any(Function),
        })
      );
      expect(response).toBe(mockResponse);
    });
  });

  describe('Context handling', () => {
    it('should provide database access through context.get("db")', async () => {
      let capturedDb: any = null;

      // Create a modified test app that includes db middleware
      const testApp = new Hono<{
        Bindings: Environment;
        Variables: { db: any };
      }>();

      // Add middleware to set the db in context
      testApp.use('*', async (c, next) => {
        c.set('db', mockDb);
        await next();
      });

      // Mount the auth router
      testApp.route('/auth', authRouter);

      vi.mocked(oauth.handleOAuthCallback).mockImplementation(async (c) => {
        capturedDb = c.get('db');
        return new Response('ok');
      });

      vi.mocked(oauth.createGitHubProvider).mockReturnValue({} as any);

      const req = new Request(
        'http://localhost:3000/auth/github/callback?code=test&state=test'
      );
      await testApp.fetch(req, mockEnv);

      expect(oauth.handleOAuthCallback).toHaveBeenCalled();
      expect(capturedDb).toBeDefined();
      expect(capturedDb).toBe(mockDb);
    });

    it('should extract origin from request URL correctly', async () => {
      vi.mocked(initiateModule.initiateOAuth).mockImplementation(
        async (_provider, currentUrl) => {
          expect(currentUrl).toBe('http://localhost:3000');
          return new Response('ok');
        }
      );

      vi.mocked(oauth.createGitHubProvider).mockReturnValue({} as any);

      await mockRequest('/github');

      expect(initiateModule.initiateOAuth).toHaveBeenCalled();
    });

    it('should handle requests from different origins', async () => {
      vi.mocked(initiateModule.initiateOAuth).mockImplementation(
        async (_provider, currentUrl) => {
          expect(currentUrl).toBe('https://example.com:8080');
          return new Response('ok');
        }
      );

      vi.mocked(oauth.createGitHubProvider).mockReturnValue({} as any);

      const req = new Request('https://example.com:8080/github');
      await mockApp.fetch(req, mockEnv, {
        waitUntil: () => {},
        passThroughOnException: () => {},
        db: mockDb,
      });

      expect(initiateModule.initiateOAuth).toHaveBeenCalled();
    });
  });

  describe('Error handling', () => {
    it('should handle errors in OAuth initiation', async () => {
      vi.mocked(oauth.createGitHubProvider).mockImplementation(() => {
        throw new Error('Provider creation failed');
      });

      const response = await mockRequest('/github');
      // Hono catches errors and returns 500 by default
      expect(response.status).toBe(500);
    });

    it('should handle errors in OAuth callback', async () => {
      vi.mocked(oauth.handleOAuthCallback).mockRejectedValue(
        new Error('Callback failed')
      );
      vi.mocked(oauth.createGitHubProvider).mockReturnValue({} as any);

      const response = await mockRequest('/github/callback');
      expect(response.status).toBe(500);
    });

    it('should handle errors in logout', async () => {
      vi.mocked(logout.handleLogout).mockRejectedValue(
        new Error('Logout failed')
      );

      const response = await mockRequest('/logout', { method: 'POST' });
      expect(response.status).toBe(500);
    });

    it('should handle errors in /me endpoint', async () => {
      vi.mocked(me.handleMe).mockRejectedValue(new Error('User fetch failed'));

      const response = await mockRequest('/me');
      expect(response.status).toBe(500);
    });
  });

  describe('Route not found', () => {
    it('should return 404 for unknown routes', async () => {
      const response = await mockRequest('/unknown-route');
      expect(response.status).toBe(404);
    });

    it('should return 404 for wrong HTTP methods', async () => {
      const response = await mockRequest('/github', { method: 'POST' });
      expect(response.status).toBe(404);
    });
  });
});
