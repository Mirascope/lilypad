import type { Environment } from '@/worker/environment';
import { OpenAPIHono } from '@hono/zod-openapi';
import { describe, expect, it } from 'vitest';
import {
  githubCallbackRoute,
  githubOAuthRoute,
  githubProxyCallbackRoute,
  googleCallbackRoute,
  googleOAuthRoute,
  googleProxyCallbackRoute,
  logoutRoute,
  meRoute,
} from './routes';
import {
  LogoutErrorResponseSchema,
  LogoutSuccessResponseSchema,
  MeErrorResponseSchema,
  MeSuccessResponseSchema,
  OAuthCallbackQuerySchema,
} from './schemas';

describe('Auth Routes OpenAPI Documentation', () => {
  describe('Route Definitions', () => {
    it('should have correct OpenAPI definition for /auth/me route', () => {
      expect(meRoute).toBeDefined();
      expect(meRoute.method).toBe('get');
      expect(meRoute.path).toBe('/me');
      expect(meRoute.tags).toEqual(['Authentication']);
      expect(meRoute.summary).toBe('Get current user');
      expect(meRoute.description).toContain(
        'Returns information about the currently authenticated user'
      );
      expect(meRoute.security).toEqual([{ cookieAuth: [] }]);
    });

    it('should have correct OpenAPI definition for /auth/logout route', () => {
      expect(logoutRoute).toBeDefined();
      expect(logoutRoute.method).toBe('post');
      expect(logoutRoute.path).toBe('/logout');
      expect(logoutRoute.tags).toEqual(['Authentication']);
      expect(logoutRoute.summary).toBe('Logout user');
      expect(logoutRoute.description).toContain(
        'Logs out the current authenticated user'
      );
    });

    it('should have correct OpenAPI definition for OAuth initiation routes', () => {
      expect(githubOAuthRoute).toBeDefined();
      expect(githubOAuthRoute.method).toBe('get');
      expect(githubOAuthRoute.path).toBe('/github');
      expect(githubOAuthRoute.tags).toEqual(['Authentication']);
      expect(githubOAuthRoute.summary).toBe('Initiate GitHub OAuth');

      expect(googleOAuthRoute).toBeDefined();
      expect(googleOAuthRoute.method).toBe('get');
      expect(googleOAuthRoute.path).toBe('/google');
      expect(googleOAuthRoute.tags).toEqual(['Authentication']);
      expect(googleOAuthRoute.summary).toBe('Initiate Google OAuth');
    });

    it('should have correct OpenAPI definition for OAuth callback routes', () => {
      expect(githubCallbackRoute).toBeDefined();
      expect(githubCallbackRoute.method).toBe('get');
      expect(githubCallbackRoute.path).toBe('/github/callback');
      expect(githubCallbackRoute.request?.query).toBe(OAuthCallbackQuerySchema);

      expect(googleCallbackRoute).toBeDefined();
      expect(googleCallbackRoute.method).toBe('get');
      expect(googleCallbackRoute.path).toBe('/google/callback');
      expect(googleCallbackRoute.request?.query).toBe(OAuthCallbackQuerySchema);
    });

    it('should have correct OpenAPI definition for proxy callback routes', () => {
      expect(githubProxyCallbackRoute).toBeDefined();
      expect(githubProxyCallbackRoute.method).toBe('get');
      expect(githubProxyCallbackRoute.path).toBe('/github/proxy-callback');
      expect(githubProxyCallbackRoute.request?.query).toBe(
        OAuthCallbackQuerySchema
      );

      expect(googleProxyCallbackRoute).toBeDefined();
      expect(googleProxyCallbackRoute.method).toBe('get');
      expect(googleProxyCallbackRoute.path).toBe('/google/proxy-callback');
      expect(googleProxyCallbackRoute.request?.query).toBe(
        OAuthCallbackQuerySchema
      );
    });
  });

  describe('Response Schema Definitions', () => {
    it('should have correct response schemas for /auth/me', () => {
      const responses = meRoute.responses;

      expect(responses[200]).toBeDefined();
      expect(responses[200].description).toBe(
        'Successfully retrieved user information'
      );
      expect(responses[200].content?.['application/json']?.schema).toBe(
        MeSuccessResponseSchema
      );

      expect(responses[401]).toBeDefined();
      expect(responses[401].description).toBe(
        'Authentication required or invalid session'
      );
      expect(responses[401].content?.['application/json']?.schema).toBe(
        MeErrorResponseSchema
      );

      expect(responses[500]).toBeDefined();
      expect(responses[500].description).toBe('Internal server error');
      expect(responses[500].content?.['application/json']?.schema).toBe(
        MeErrorResponseSchema
      );
    });

    it('should have correct response schemas for /auth/logout', () => {
      const responses = logoutRoute.responses;

      expect(responses[200]).toBeDefined();
      expect(responses[200].description).toBe('Successfully logged out');
      expect(responses[200].content?.['application/json']?.schema).toBe(
        LogoutSuccessResponseSchema
      );
      expect(responses[200].headers?.['Set-Cookie']).toBeDefined();

      expect(responses[400]).toBeDefined();
      expect(responses[400].description).toBe('No active session found');
      expect(responses[400].content?.['application/json']?.schema).toBe(
        LogoutErrorResponseSchema
      );

      expect(responses[500]).toBeDefined();
      expect(responses[500].description).toBe(
        'Logout failed due to server error'
      );
      expect(responses[500].content?.['application/json']?.schema).toBe(
        LogoutErrorResponseSchema
      );
    });

    it('should have correct redirect responses for OAuth routes', () => {
      const githubResponses = githubOAuthRoute.responses;
      expect(githubResponses[302]).toBeDefined();
      expect(githubResponses[302].description).toBe(
        'Redirect to GitHub OAuth authorization page'
      );
      expect(githubResponses[302].headers?.Location).toBeDefined();
      expect(githubResponses[302].headers?.['Set-Cookie']).toBeDefined();

      const googleResponses = googleOAuthRoute.responses;
      expect(googleResponses[302]).toBeDefined();
      expect(googleResponses[302].description).toBe(
        'Redirect to Google OAuth authorization page'
      );
      expect(googleResponses[302].headers?.Location).toBeDefined();
      expect(googleResponses[302].headers?.['Set-Cookie']).toBeDefined();
    });
  });

  describe('OpenAPI Spec Generation', () => {
    it('should generate valid OpenAPI spec with all routes', () => {
      const app = new OpenAPIHono<{ Bindings: Environment }>();

      app.openapi(meRoute, () => null as any);
      app.openapi(logoutRoute, () => null as any);
      app.openapi(githubOAuthRoute, () => null as any);
      app.openapi(googleOAuthRoute, () => null as any);
      app.openapi(githubCallbackRoute, () => null as any);
      app.openapi(googleCallbackRoute, () => null as any);
      app.openapi(githubProxyCallbackRoute, () => null as any);
      app.openapi(googleProxyCallbackRoute, () => null as any);

      const doc = app.getOpenAPIDocument({
        openapi: '3.1.0',
        info: {
          title: 'Auth API',
          version: '1.0.0',
        },
      });

      expect(doc.paths['/me']).toBeDefined();
      expect(doc.paths['/logout']).toBeDefined();
      expect(doc.paths['/github']).toBeDefined();
      expect(doc.paths['/google']).toBeDefined();
      expect(doc.paths['/github/callback']).toBeDefined();
      expect(doc.paths['/google/callback']).toBeDefined();
      expect(doc.paths['/github/proxy-callback']).toBeDefined();
      expect(doc.paths['/google/proxy-callback']).toBeDefined();

      if (doc.tags) {
        expect(doc.tags).toContainEqual({ name: 'Authentication' });
      }
    });
  });

  describe('Schema Validation', () => {
    it('should have valid success response schemas for /auth/me', () => {
      const successData = {
        success: true,
        user: {
          id: '550e8400-e29b-41d4-a716-446655440000',
          email: 'test@example.com',
          name: 'Test User',
        },
      };

      const validation = MeSuccessResponseSchema.safeParse(successData);
      expect(validation.success).toBe(true);
    });

    it('should have valid error response schemas for /auth/me', () => {
      const errorData = {
        success: false,
        error: 'Authentication required',
      };

      const validation = MeErrorResponseSchema.safeParse(errorData);
      expect(validation.success).toBe(true);
    });

    it('should have valid success response schemas for /auth/logout', () => {
      const successData = {
        success: true,
        message: 'Logged out successfully',
      };

      const validation = LogoutSuccessResponseSchema.safeParse(successData);
      expect(validation.success).toBe(true);
    });

    it('should have valid error response schemas for /auth/logout', () => {
      const errorData = {
        success: false,
        error: 'No active session found',
      };

      const validation = LogoutErrorResponseSchema.safeParse(errorData);
      expect(validation.success).toBe(true);
    });

    it('should validate OAuth callback query parameters', () => {
      const validQuery = {
        code: 'test-code',
        state: 'test-state',
      };

      const validation = OAuthCallbackQuerySchema.safeParse(validQuery);
      expect(validation.success).toBe(true);

      const errorQuery = {
        error: 'access_denied',
        error_description: 'User denied access',
        state: 'test-state',
      };

      const errorValidation = OAuthCallbackQuerySchema.safeParse(errorQuery);
      expect(errorValidation.success).toBe(true);
    });
  });
});
