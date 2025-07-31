import { DEFAULT_SESSION_DURATION, sessions, users } from '@/db/schema';
import { db } from '@/tests/db-setup';
import {
  createMockContext,
  mockFetchError,
  mockFetchSuccess,
} from '@/tests/worker-setup';
import { eq } from 'drizzle-orm';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { handleOAuthCallback } from './callback';
import type { OAuthProvider } from './types';

describe('handleOAuthCallback', () => {
  let mockContext: any;
  let mockProvider: OAuthProvider;
  let consoleErrorSpy: any;

  beforeEach(() => {
    vi.clearAllMocks();
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    mockContext = createMockContext({
      path: '/auth/callback',
      query: { code: 'test-code', state: 'encodedState' },
    });

    mockProvider = {
      authUrl: 'https://provider.com/oauth/authorize',
      tokenUrl: 'https://provider.com/oauth/token',
      userUrl: 'https://provider.com/api/user',
      scopes: ['read:user'],
      clientId: 'test-client-id',
      clientSecret: 'test-client-secret',
      callbackUrl: 'http://localhost:3000/auth/callback',
      mapUserData: vi.fn().mockResolvedValue({
        email: 'test@example.com',
        name: 'Test User',
      }),
    };
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  describe('OAuth error handling', () => {
    it('should handle OAuth provider error', async () => {
      mockContext = createMockContext({
        path: '/auth/callback',
        query: {
          error: 'access_denied',
          error_description: 'User denied access',
        },
      });

      await expect(
        handleOAuthCallback(mockContext, mockProvider)
      ).rejects.toThrow('OAuth Error: access_denied');
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'OAuth error:',
        'access_denied'
      );
    });

    it('should handle missing authorization code', async () => {
      mockContext = createMockContext({
        path: '/auth/callback',
        query: { state: 'encodedState' },
      });

      await expect(
        handleOAuthCallback(mockContext, mockProvider)
      ).rejects.toThrow('No authorization code received');
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'No authorization code received'
      );
    });

    it('should handle missing state parameter', async () => {
      mockContext = createMockContext({
        path: '/auth/callback',
        query: { code: 'test-code' },
      });

      await expect(
        handleOAuthCallback(mockContext, mockProvider)
      ).rejects.toThrow('No state received');
      expect(consoleErrorSpy).toHaveBeenCalledWith('No state received');
    });
  });

  describe('State validation', () => {
    it('should handle invalid base64 encoded state', async () => {
      mockContext = createMockContext({
        path: '/auth/callback',
        query: { code: 'test-code', state: 'invalid-base64!@#' },
      });

      await expect(
        handleOAuthCallback(mockContext, mockProvider)
      ).rejects.toThrow(/Failed to decode state:/);
    });

    it('should handle invalid JSON in state', async () => {
      const invalidJsonState = btoa('invalid json {');
      mockContext = createMockContext({
        path: '/auth/callback',
        query: { code: 'test-code', state: invalidJsonState },
      });

      await expect(
        handleOAuthCallback(mockContext, mockProvider)
      ).rejects.toThrow(/Failed to decode state:/);
    });

    it('should validate state parameter matches cookie', async () => {
      const stateData = {
        randomState: 'test-state-123',
        returnUrl: 'http://localhost:3000',
      };
      const encodedState = btoa(JSON.stringify(stateData));
      mockContext = createMockContext({
        path: `/auth/callback?code=test-code&state=${encodedState}`,
        headers: { Cookie: 'oauth_state=different-state; other=value' },
      });

      await expect(
        handleOAuthCallback(mockContext, mockProvider)
      ).rejects.toThrow('Invalid state parameter');
    });

    it('should handle missing cookie header', async () => {
      const stateData = {
        randomState: 'test-state-123',
        returnUrl: 'http://localhost:3000',
      };
      const encodedState = btoa(JSON.stringify(stateData));
      mockContext = createMockContext({
        path: '/auth/callback',
        query: { code: 'test-code', state: encodedState },
      });

      await expect(
        handleOAuthCallback(mockContext, mockProvider)
      ).rejects.toThrow('Invalid state parameter');
    });
  });

  describe('Token exchange', () => {
    beforeEach(() => {
      const stateData = {
        randomState: 'test-state-123',
        returnUrl: 'http://localhost:3000',
      };
      const encodedState = btoa(JSON.stringify(stateData));
      mockContext = createMockContext({
        path: '/auth/callback',
        query: { code: 'test-code', state: encodedState },
        headers: { Cookie: 'oauth_state=test-state-123; other=value' },
      });
    });

    it('should exchange code for access token successfully', async () => {
      vi.mocked(global.fetch)
        .mockResolvedValueOnce(
          mockFetchSuccess({
            access_token: 'test-access-token',
            token_type: 'Bearer',
          })
        )
        .mockResolvedValueOnce(
          mockFetchSuccess({
            id: 1,
            email: 'test@example.com',
            name: 'Test User',
          })
        );

      const response = await handleOAuthCallback(mockContext, mockProvider);

      expect(global.fetch).toHaveBeenCalledWith(
        'https://provider.com/oauth/token',
        expect.objectContaining({
          method: 'POST',
          headers: {
            Accept: 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: expect.any(URLSearchParams),
        })
      );

      const fetchCall = vi.mocked(global.fetch).mock.calls[0];
      const body = fetchCall[1]!.body as URLSearchParams;
      expect(body.get('grant_type')).toBe('authorization_code');
      expect(body.get('client_id')).toBe('test-client-id');
      expect(body.get('client_secret')).toBe('test-client-secret');
      expect(body.get('code')).toBe('test-code');
      expect(body.get('redirect_uri')).toBe(
        'http://localhost:3000/auth/callback'
      );

      // Verify user was created in database
      const [user] = await db
        .select()
        .from(users)
        .where(eq(users.email, 'test@example.com'));
      expect(user).toBeTruthy();
      expect(user.name).toBe('Test User');

      // Verify session was created
      const [session] = await db
        .select()
        .from(sessions)
        .where(eq(sessions.userId, user.id));
      expect(session).toBeTruthy();

      // Verify redirect response
      expect(response.status).toBe(302);
      const location = response.headers.get('Location');
      expect(location).toContain('success=true');
    });

    it('should handle token exchange error response', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce(
        mockFetchSuccess({
          error: 'invalid_grant',
          error_description: 'The provided authorization code is invalid',
        })
      );

      await expect(
        handleOAuthCallback(mockContext, mockProvider)
      ).rejects.toThrow('Token exchange failed: invalid_grant');
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Token exchange failed:',
        'invalid_grant'
      );
    });

    it('should handle missing access token in response', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce(
        mockFetchSuccess({ token_type: 'Bearer' })
      );

      await expect(
        handleOAuthCallback(mockContext, mockProvider)
      ).rejects.toThrow('No access token received');
      expect(consoleErrorSpy).toHaveBeenCalledWith('No access token received');
    });
  });

  describe('User data fetching', () => {
    beforeEach(() => {
      const stateData = {
        randomState: 'test-state-123',
        returnUrl: 'http://localhost:3000',
      };
      const encodedState = btoa(JSON.stringify(stateData));
      mockContext = createMockContext({
        path: '/auth/callback',
        query: { code: 'test-code', state: encodedState },
        headers: { Cookie: 'oauth_state=test-state-123' },
      });
    });

    it('should fetch user data with access token', async () => {
      vi.mocked(global.fetch)
        .mockResolvedValueOnce(
          mockFetchSuccess({ access_token: 'test-access-token' })
        )
        .mockResolvedValueOnce(
          mockFetchSuccess({ id: 1, email: 'test@example.com' })
        );

      await handleOAuthCallback(mockContext, mockProvider);

      expect(global.fetch).toHaveBeenNthCalledWith(
        2,
        'https://provider.com/api/user',
        {
          headers: {
            Authorization: 'Bearer test-access-token',
            Accept: 'application/json',
            'User-Agent': 'Mirascope/0.1',
          },
        }
      );
    });

    it('should handle failed user data fetch', async () => {
      vi.mocked(global.fetch)
        .mockResolvedValueOnce(
          mockFetchSuccess({ access_token: 'test-access-token' })
        )
        .mockResolvedValueOnce(mockFetchError(401, 'Unauthorized'));

      await expect(
        handleOAuthCallback(mockContext, mockProvider)
      ).rejects.toThrow('Failed to fetch user data');
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Failed to fetch user data:',
        401,
        'Unauthorized'
      );
    });

    it('should call mapUserData with API response and access token', async () => {
      const mockApiResponse = {
        id: 1,
        email: 'api@example.com',
        custom_field: 'value',
      };

      vi.mocked(global.fetch)
        .mockResolvedValueOnce(
          mockFetchSuccess({ access_token: 'test-access-token' })
        )
        .mockResolvedValueOnce(mockFetchSuccess(mockApiResponse));

      await handleOAuthCallback(mockContext, mockProvider);

      expect(mockProvider.mapUserData).toHaveBeenCalledWith(
        mockApiResponse,
        'test-access-token'
      );
    });
  });

  describe('User creation and session management', () => {
    beforeEach(() => {
      const stateData = {
        randomState: 'test-state-123',
        returnUrl: 'http://localhost:3000/custom',
      };
      const encodedState = btoa(JSON.stringify(stateData));
      mockContext = createMockContext({
        path: '/auth/callback',
        query: { code: 'test-code', state: encodedState },
        headers: { Cookie: 'oauth_state=test-state-123' },
      });

      vi.mocked(global.fetch)
        .mockResolvedValueOnce(
          mockFetchSuccess({ access_token: 'test-access-token' })
        )
        .mockResolvedValueOnce(mockFetchSuccess({ id: 1 }));
    });

    it('should create or update user and create session', async () => {
      const response = await handleOAuthCallback(mockContext, mockProvider);

      // Verify user was created/updated in database
      const [user] = await db
        .select()
        .from(users)
        .where(eq(users.email, 'test@example.com'));
      expect(user).toBeTruthy();
      expect(user.name).toBe('Test User');

      // Verify session was created
      const [session] = await db
        .select()
        .from(sessions)
        .where(eq(sessions.userId, user.id));
      expect(session).toBeTruthy();

      expect(response.status).toBe(302);
      const location = response.headers.get('Location');
      expect(location).toContain('http://localhost:3000/custom');
      expect(location).toContain('success=true');
      expect(location).toContain('user=');
    });

    it('should handle missing email in user info', async () => {
      mockProvider.mapUserData = vi.fn().mockResolvedValue({
        email: null,
        name: 'Test User',
      });

      const response = await handleOAuthCallback(mockContext, mockProvider);

      expect(response.status).toBe(302);
      const location = response.headers.get('Location')!;
      expect(location).toContain('error=authentication_failed');
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Error processing authentication:',
        expect.any(Error)
      );
    });

    it('should handle failed user creation', async () => {
      // Mock database error during user creation
      const dbSpy = vi.spyOn(db, 'insert').mockImplementation(() => {
        throw new Error('Database error');
      });

      const response = await handleOAuthCallback(mockContext, mockProvider);

      expect(response.status).toBe(302);
      const location = response.headers.get('Location')!;
      expect(location).toContain('error=authentication_failed');

      dbSpy.mockRestore();
    });

    it('should handle failed session creation', async () => {
      // First, let the user creation succeed
      let callCount = 0;
      const originalInsert = db.insert.bind(db);
      const dbSpy = vi.spyOn(db, 'insert').mockImplementation((query) => {
        callCount++;
        // Let the first insert (user) succeed, fail the second (session)
        if (callCount === 2) {
          throw new Error('Session creation failed');
        }
        // Return the original implementation for the first call
        return originalInsert(query);
      });

      const response = await handleOAuthCallback(mockContext, mockProvider);

      expect(response.status).toBe(302);
      const location = response.headers.get('Location')!;
      expect(location).toContain('error=authentication_failed');

      dbSpy.mockRestore();
    });

    it('should handle when createSession returns null', async () => {
      // Mock createSession to return null
      const createSessionModule = await import('@/db/operations');
      const createSessionSpy = vi
        .spyOn(createSessionModule, 'createSession')
        .mockResolvedValue(null);

      const response = await handleOAuthCallback(mockContext, mockProvider);

      expect(response.status).toBe(302);
      const location = response.headers.get('Location')!;
      expect(location).toContain('error=authentication_failed');
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Error processing authentication:',
        expect.any(Error)
      );

      createSessionSpy.mockRestore();
    });

    it('should set session cookie with correct attributes', async () => {
      const response = await handleOAuthCallback(mockContext, mockProvider);

      const setCookieHeaders = response.headers.getSetCookie();
      const sessionCookie = setCookieHeaders.find((cookie) =>
        cookie.startsWith('session=')
      );

      // Verify session was created and get its ID
      const [user] = await db
        .select()
        .from(users)
        .where(eq(users.email, 'test@example.com'));
      const [session] = await db
        .select()
        .from(sessions)
        .where(eq(sessions.userId, user.id));

      expect(sessionCookie).toContain(`session=${session.id}`);
      expect(sessionCookie).toContain('HttpOnly');
      expect(sessionCookie).toContain('Secure');
      expect(sessionCookie).toContain('SameSite=Lax');
      expect(sessionCookie).toContain(`Max-Age=${DEFAULT_SESSION_DURATION}`);
      expect(sessionCookie).toContain('Path=/');
    });

    it('should delete oauth_state cookie after successful authentication', async () => {
      const response = await handleOAuthCallback(mockContext, mockProvider);

      const setCookieHeaders = response.headers.getSetCookie();
      const deleteStateCookie = setCookieHeaders.find((cookie) =>
        cookie.startsWith('oauth_state=;')
      );

      expect(deleteStateCookie).toBeTruthy();
      expect(deleteStateCookie).toContain(
        'Expires=Thu, 01 Jan 1970 00:00:00 GMT'
      );
      expect(deleteStateCookie).toContain('HttpOnly');
      expect(deleteStateCookie).toContain('Secure');
      expect(deleteStateCookie).toContain('SameSite=Lax');
      expect(deleteStateCookie).toContain('Path=/');
    });

    it('should encode user data in redirect URL', async () => {
      const response = await handleOAuthCallback(mockContext, mockProvider);

      // Get the created user from database
      const [user] = await db
        .select()
        .from(users)
        .where(eq(users.email, 'test@example.com'));

      const location = response.headers.get('Location')!;
      const url = new URL(location);
      const encodedUser = url.searchParams.get('user')!;
      const decodedUser = JSON.parse(decodeURIComponent(encodedUser));

      expect(decodedUser).toEqual({
        id: user.id,
        email: user.email,
        name: user.name,
      });
    });

    it('should use SITE_URL when returnUrl is not provided', async () => {
      const stateData = { randomState: 'test-state-123' };
      const encodedState = btoa(JSON.stringify(stateData));
      mockContext = createMockContext({
        path: '/auth/callback',
        query: { code: 'test-code', state: encodedState },
        headers: { Cookie: 'oauth_state=test-state-123' },
      });

      // Re-mock fetch for this specific test
      vi.mocked(global.fetch)
        .mockResolvedValueOnce(
          mockFetchSuccess({ access_token: 'test-access-token' })
        )
        .mockResolvedValueOnce(mockFetchSuccess({ id: 1 }));

      const response = await handleOAuthCallback(mockContext, mockProvider);

      const location = response.headers.get('Location')!;
      expect(location).toContain('http://localhost:3000/?success=true');
    });
  });

  describe('Error handling edge cases', () => {
    beforeEach(() => {
      const stateData = {
        randomState: 'test-state-123',
        returnUrl: 'http://localhost:3000',
      };
      const encodedState = btoa(JSON.stringify(stateData));
      mockContext = createMockContext({
        path: '/auth/callback',
        query: { code: 'test-code', state: encodedState },
        headers: { Cookie: 'oauth_state=test-state-123' },
      });
    });

    it('should handle database errors during user creation', async () => {
      vi.mocked(global.fetch)
        .mockResolvedValueOnce(
          mockFetchSuccess({ access_token: 'test-access-token' })
        )
        .mockResolvedValueOnce(mockFetchSuccess({ id: 1 }));

      // Mock database error
      const dbSpy = vi.spyOn(db, 'insert').mockImplementation(() => {
        throw new Error('Database connection failed');
      });

      const response = await handleOAuthCallback(mockContext, mockProvider);

      expect(response.status).toBe(302);
      const location = response.headers.get('Location')!;
      expect(location).toContain('error=authentication_failed');
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Error processing authentication:',
        expect.any(Error)
      );

      dbSpy.mockRestore();
    });

    it('should handle network errors during token exchange', async () => {
      vi.mocked(global.fetch).mockRejectedValue(new Error('Network error'));

      await expect(
        handleOAuthCallback(mockContext, mockProvider)
      ).rejects.toThrow('Network error');
    });

    it('should handle JSON parsing errors', async () => {
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: async () => {
          throw new Error('Invalid JSON');
        },
      } as unknown as Response);

      await expect(
        handleOAuthCallback(mockContext, mockProvider)
      ).rejects.toThrow('Invalid JSON');
    });
  });
});
