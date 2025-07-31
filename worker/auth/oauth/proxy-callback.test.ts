import type { Database } from '@/db/utils';
import { createMockContext } from '@/tests/worker-setup';
import type { Environment } from '@/worker/environment';
import type { Context } from 'hono';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { handleOAuthProxyCallback } from './proxy-callback';

describe('handleOAuthProxyCallback', () => {
  let mockContext: Context<{
    Bindings: Environment;
    Variables: { db: Database };
  }>;
  let consoleLogSpy: any;
  let consoleErrorSpy: any;

  beforeEach(() => {
    vi.clearAllMocks();
    consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    mockContext = createMockContext({
      path: '/auth/github/proxy-callback?code=test-code&state=encodedState',
      env: {
        SITE_URL: 'http://staging.lilypad.mirascope.com',
        ENVIRONMENT: 'staging',
        DATABASE_URL: 'postgresql://test',
        GITHUB_CLIENT_ID: 'test-github-id',
        GITHUB_CLIENT_SECRET: 'test-github-secret',
        GITHUB_CALLBACK_URL:
          'http://staging.lilypad.mirascope.com/auth/github/proxy-callback',
        GOOGLE_CLIENT_ID: 'test-google-id',
        GOOGLE_CLIENT_SECRET: 'test-google-secret',
        GOOGLE_CALLBACK_URL:
          'http://staging.lilypad.mirascope.com/auth/google/proxy-callback',
      },
    }) as any;
  });

  afterEach(() => {
    consoleLogSpy.mockRestore();
    consoleErrorSpy.mockRestore();
  });

  describe('OAuth error handling', () => {
    it('should handle OAuth provider error with description', async () => {
      mockContext = createMockContext({
        path: '/auth/github/proxy-callback?error=access_denied&error_description=User%20denied%20access',
        env: mockContext.env,
      }) as any;

      await expect(
        handleOAuthProxyCallback(mockContext, 'github')
      ).rejects.toThrow('OAuth Error: access_denied - User denied access');
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'OAuth error from provider:',
        'access_denied',
        'User denied access'
      );
    });

    it('should handle OAuth provider error without description', async () => {
      mockContext = createMockContext({
        path: '/auth/github/proxy-callback?error=invalid_scope',
        env: mockContext.env,
      }) as any;

      await expect(
        handleOAuthProxyCallback(mockContext, 'github')
      ).rejects.toThrow('OAuth Error: invalid_scope - ');
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'OAuth error from provider:',
        'invalid_scope',
        null
      );
    });

    it('should handle missing state parameter', async () => {
      mockContext = createMockContext({
        path: '/auth/github/proxy-callback?code=test-code',
        env: mockContext.env,
      }) as any;

      await expect(
        handleOAuthProxyCallback(mockContext, 'github')
      ).rejects.toThrow('No state parameter received');
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'No state parameter received'
      );
    });

    it('should handle missing authorization code after state validation', async () => {
      const stateData = {
        randomState: 'test-state',
        returnUrl: 'https://lilypad-pr-123.mirascope.workers.dev',
      };
      const encodedState = btoa(JSON.stringify(stateData));
      mockContext = createMockContext({
        path: `/auth/github/proxy-callback?state=${encodedState}`,
        env: mockContext.env,
      }) as any;

      await expect(
        handleOAuthProxyCallback(mockContext, 'github')
      ).rejects.toThrow('No authorization code received');
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'No authorization code received'
      );
    });
  });

  describe('State decoding and validation', () => {
    it('should handle invalid base64 encoded state', async () => {
      mockContext = createMockContext({
        path: '/auth/github/proxy-callback?code=test-code&state=invalid-base64!@#',
        env: mockContext.env,
      }) as any;

      await expect(
        handleOAuthProxyCallback(mockContext, 'github')
      ).rejects.toThrow('Invalid state parameter - unable to decode');
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Failed to decode state:',
        expect.any(Error)
      );
    });

    it('should handle invalid JSON in state', async () => {
      const invalidJsonState = btoa('invalid json {');
      mockContext = createMockContext({
        path: `/auth/github/proxy-callback?code=test-code&state=${invalidJsonState}`,
        env: mockContext.env,
      }) as any;

      await expect(
        handleOAuthProxyCallback(mockContext, 'github')
      ).rejects.toThrow('Invalid state parameter - unable to decode');
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Failed to decode state:',
        expect.any(Error)
      );
    });

    it('should handle missing returnUrl in state', async () => {
      const stateData = { randomState: 'test-state' };
      const encodedState = btoa(JSON.stringify(stateData));
      mockContext = createMockContext({
        path: `/auth/github/proxy-callback?code=test-code&state=${encodedState}`,
        env: mockContext.env,
      }) as any;

      await expect(
        handleOAuthProxyCallback(mockContext, 'github')
      ).rejects.toThrow('No return URL found in state');
    });
  });

  describe('Preview URL validation', () => {
    it('should accept valid PR preview URLs', async () => {
      const testCases = [
        'https://lilypad-pr-1.mirascope.workers.dev',
        'https://lilypad-pr-999.mirascope.workers.dev',
        'https://lilypad-pr-12345.mirascope.workers.dev',
      ];

      for (const returnUrl of testCases) {
        const stateData = { randomState: 'test-state', returnUrl };
        const encodedState = btoa(JSON.stringify(stateData));
        mockContext = createMockContext({
          path: `/auth/github/proxy-callback?code=test-code&state=${encodedState}`,
          env: mockContext.env,
        }) as any;

        const response = await handleOAuthProxyCallback(mockContext, 'github');

        expect(response.status).toBe(302);
        const location = response.headers.get('Location');
        expect(location).toContain(returnUrl);
      }
    });

    it('should accept staging URL', async () => {
      const stateData = {
        randomState: 'test-state',
        returnUrl: 'https://staging.lilypad.mirascope.com',
      };
      const encodedState = btoa(JSON.stringify(stateData));
      mockContext = createMockContext({
        path: `/auth/github/proxy-callback?code=test-code&state=${encodedState}`,
        env: mockContext.env,
      }) as any;

      const response = await handleOAuthProxyCallback(mockContext, 'github');

      expect(response.status).toBe(302);
      const location = response.headers.get('Location');
      expect(location).toContain('https://staging.lilypad.mirascope.com');
    });

    it('should reject invalid preview URLs', async () => {
      const invalidUrls = [
        'https://evil-site.com',
        'https://lilypad-pr.mirascope.workers.dev',
        'https://lilypad-pr-abc.mirascope.workers.dev',
        'https://lilypad-pr-123.evil.com',
        'https://pr-123.mirascope.workers.dev',
        'https://lilypad-pr-123.mirascope.com',
        'https://staging.lilypad.evil.com',
      ];

      for (const returnUrl of invalidUrls) {
        const stateData = { randomState: 'test-state', returnUrl };
        const encodedState = btoa(JSON.stringify(stateData));
        mockContext = createMockContext({
          path: `/auth/github/proxy-callback?code=test-code&state=${encodedState}`,
          env: mockContext.env,
        }) as any;

        await expect(
          handleOAuthProxyCallback(mockContext, 'github')
        ).rejects.toThrow('Invalid return URL');
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          'Invalid return URL:',
          returnUrl
        );
      }
    });

    it('should handle malformed URLs in returnUrl', async () => {
      const stateData = {
        randomState: 'test-state',
        returnUrl: 'not-a-valid-url',
      };
      const encodedState = btoa(JSON.stringify(stateData));
      mockContext = createMockContext({
        path: `/auth/github/proxy-callback?code=test-code&state=${encodedState}`,
        env: mockContext.env,
      }) as any;

      await expect(
        handleOAuthProxyCallback(mockContext, 'github')
      ).rejects.toThrow('Invalid return URL');
    });
  });

  describe('Successful proxy redirect', () => {
    it('should proxy to GitHub callback with correct parameters', async () => {
      const stateData = {
        randomState: 'test-state-123',
        returnUrl: 'https://lilypad-pr-456.mirascope.workers.dev',
      };
      const encodedState = btoa(JSON.stringify(stateData));
      mockContext = createMockContext({
        path: `/auth/github/proxy-callback?code=test-auth-code&state=${encodedState}`,
        env: mockContext.env,
      }) as any;

      const response = await handleOAuthProxyCallback(mockContext, 'github');

      expect(response.status).toBe(302);

      const location = response.headers.get('Location')!;
      const locationUrl = new URL(location);

      expect(locationUrl.origin).toBe(
        'https://lilypad-pr-456.mirascope.workers.dev'
      );
      expect(locationUrl.pathname).toBe('/auth/github/callback');
      expect(locationUrl.searchParams.get('code')).toBe('test-auth-code');
      expect(locationUrl.searchParams.get('state')).toBe(encodedState);

      expect(consoleLogSpy).toHaveBeenCalledWith(
        'Proxying OAuth callback from staging to preview:',
        expect.objectContaining({
          from: mockContext.req.url,
          to: location,
        })
      );
    });

    it('should proxy to Google callback with correct parameters', async () => {
      const stateData = {
        randomState: 'test-state-456',
        returnUrl: 'https://staging.lilypad.mirascope.com',
      };
      const encodedState = btoa(JSON.stringify(stateData));
      mockContext = createMockContext({
        path: `/auth/google/proxy-callback?code=google-auth-code&state=${encodedState}`,
        env: mockContext.env,
      }) as any;

      const response = await handleOAuthProxyCallback(mockContext, 'google');

      expect(response.status).toBe(302);

      const location = response.headers.get('Location')!;
      const locationUrl = new URL(location);

      expect(locationUrl.origin).toBe('https://staging.lilypad.mirascope.com');
      expect(locationUrl.pathname).toBe('/auth/google/callback');
      expect(locationUrl.searchParams.get('code')).toBe('google-auth-code');
      expect(locationUrl.searchParams.get('state')).toBe(encodedState);
    });

    it('should handle lowercase provider names', async () => {
      const stateData = {
        randomState: 'test-state',
        returnUrl: 'https://lilypad-pr-789.mirascope.workers.dev',
      };
      const encodedState = btoa(JSON.stringify(stateData));
      mockContext = createMockContext({
        path: `/auth/github/proxy-callback?code=test-code&state=${encodedState}`,
        env: mockContext.env,
      }) as any;

      const response = await handleOAuthProxyCallback(mockContext, 'GITHUB');

      const location = response.headers.get('Location')!;
      expect(location).toContain('/auth/github/callback');
    });

    it('should set oauth_state cookie with correct attributes', async () => {
      const stateData = {
        randomState: 'cookie-test-state',
        returnUrl: 'https://lilypad-pr-100.mirascope.workers.dev',
      };
      const encodedState = btoa(JSON.stringify(stateData));
      mockContext = createMockContext({
        path: `/auth/github/proxy-callback?code=test-code&state=${encodedState}`,
        env: mockContext.env,
      }) as any;

      const response = await handleOAuthProxyCallback(mockContext, 'github');

      const setCookie = response.headers.get('Set-Cookie');
      expect(setCookie).toBe(
        'oauth_state=cookie-test-state; HttpOnly; Secure; SameSite=Lax; Max-Age=600; Path=/'
      );
    });

    it('should preserve special characters in code parameter', async () => {
      const stateData = {
        randomState: 'test-state',
        returnUrl: 'https://lilypad-pr-200.mirascope.workers.dev',
      };
      const encodedState = btoa(JSON.stringify(stateData));
      const specialCode = 'code-with-special+chars/=&';
      mockContext = createMockContext({
        path: `/auth/github/proxy-callback?code=${encodeURIComponent(specialCode)}&state=${encodedState}`,
        env: mockContext.env,
      }) as any;

      const response = await handleOAuthProxyCallback(mockContext, 'github');

      const location = response.headers.get('Location')!;
      const locationUrl = new URL(location);
      expect(locationUrl.searchParams.get('code')).toBe(specialCode);
    });
  });

  describe('Edge cases', () => {
    it('should handle returnUrl with query parameters', async () => {
      const stateData = {
        randomState: 'test-state',
        returnUrl:
          'https://lilypad-pr-300.mirascope.workers.dev?existing=param',
      };
      const encodedState = btoa(JSON.stringify(stateData));
      mockContext = createMockContext({
        path: `/auth/github/proxy-callback?code=test-code&state=${encodedState}`,
        env: mockContext.env,
      }) as any;

      const response = await handleOAuthProxyCallback(mockContext, 'github');

      const location = response.headers.get('Location')!;
      const locationUrl = new URL(location);
      // Query params from the returnUrl are not preserved when constructing the callback URL
      expect(locationUrl.searchParams.get('existing')).toBe(null);
      expect(locationUrl.searchParams.get('code')).toBe('test-code');
      expect(locationUrl.searchParams.get('state')).toBe(encodedState);
      expect(locationUrl.origin).toBe(
        'https://lilypad-pr-300.mirascope.workers.dev'
      );
    });

    it('should handle returnUrl with hash fragment', async () => {
      const stateData = {
        randomState: 'test-state',
        returnUrl: 'https://lilypad-pr-400.mirascope.workers.dev#section',
      };
      const encodedState = btoa(JSON.stringify(stateData));
      mockContext = createMockContext({
        path: `/auth/github/proxy-callback?code=test-code&state=${encodedState}`,
        env: mockContext.env,
      }) as any;

      const response = await handleOAuthProxyCallback(mockContext, 'github');

      const location = response.headers.get('Location')!;
      // Hash fragments are not preserved when constructing the callback URL
      expect(location).not.toContain('#section');
      expect(location).toContain(
        'https://lilypad-pr-400.mirascope.workers.dev/auth/github/callback'
      );
    });

    it('should handle very long state values', async () => {
      const longData = 'x'.repeat(1000);
      const stateData = {
        randomState: longData,
        returnUrl: 'https://lilypad-pr-500.mirascope.workers.dev',
      };
      const encodedState = btoa(JSON.stringify(stateData));
      mockContext = createMockContext({
        path: `/auth/github/proxy-callback?code=test-code&state=${encodedState}`,
        env: mockContext.env,
      }) as any;

      const response = await handleOAuthProxyCallback(mockContext, 'github');

      expect(response.status).toBe(302);
      const setCookie = response.headers.get('Set-Cookie');
      expect(setCookie).toContain(`oauth_state=${longData}`);
    });
  });
});
