import { beforeEach, describe, expect, it, vi } from 'vitest';
import { initiateOAuth } from './initiate';
import type { OAuthProvider } from './types';

// Mock crypto.randomUUID
const mockRandomUUID = vi.fn(() => 'mock-uuid-12345');
vi.stubGlobal('crypto', {
  randomUUID: mockRandomUUID,
});

describe('initiateOAuth', () => {
  let mockProvider: OAuthProvider;

  beforeEach(() => {
    vi.clearAllMocks();

    mockProvider = {
      authUrl: 'https://example.com/oauth/authorize',
      tokenUrl: 'https://example.com/oauth/token',
      userUrl: 'https://example.com/api/user',
      scopes: ['read:user', 'user:email'],
      clientId: 'test-client-id',
      clientSecret: 'test-client-secret',
      callbackUrl: 'https://example.com/auth/callback',
      mapUserData: vi.fn(),
    };
  });

  it('should create a redirect response with correct OAuth parameters', async () => {
    const currentUrl = 'https://myapp.com/some/path';

    const response = await initiateOAuth(mockProvider, currentUrl);

    expect(response.status).toBe(302);

    const location = response.headers.get('Location');
    expect(location).toBeTruthy();

    const locationUrl = new URL(location!);
    expect(locationUrl.origin + locationUrl.pathname).toBe(
      'https://example.com/oauth/authorize'
    );
    expect(locationUrl.searchParams.get('response_type')).toBe('code');
    expect(locationUrl.searchParams.get('client_id')).toBe('test-client-id');
    expect(locationUrl.searchParams.get('redirect_uri')).toBe(
      'https://example.com/auth/callback'
    );
    expect(locationUrl.searchParams.get('scope')).toBe('read:user user:email');

    const state = locationUrl.searchParams.get('state');
    expect(state).toBeTruthy();
  });

  it('should encode state with randomState and returnUrl', async () => {
    const currentUrl = 'https://myapp.com/dashboard?tab=settings';

    const response = await initiateOAuth(mockProvider, currentUrl);

    const location = response.headers.get('Location')!;
    const locationUrl = new URL(location);
    const encodedState = locationUrl.searchParams.get('state')!;

    const decodedState = JSON.parse(atob(encodedState));
    expect(decodedState).toEqual({
      randomState: 'mock-uuid-12345',
      returnUrl: currentUrl,
    });
  });

  it('should set secure HTTP-only cookie with OAuth state', async () => {
    const currentUrl = 'https://myapp.com';

    const response = await initiateOAuth(mockProvider, currentUrl);

    const setCookie = response.headers.get('Set-Cookie');
    expect(setCookie).toBe(
      'oauth_state=mock-uuid-12345; HttpOnly; Secure; SameSite=Lax; Max-Age=600; Path=/'
    );
  });

  it('should handle empty scopes array', async () => {
    mockProvider.scopes = [];
    const currentUrl = 'https://myapp.com';

    const response = await initiateOAuth(mockProvider, currentUrl);

    const location = response.headers.get('Location')!;
    const locationUrl = new URL(location);
    expect(locationUrl.searchParams.get('scope')).toBe('');
  });

  it('should handle single scope', async () => {
    mockProvider.scopes = ['read:user'];
    const currentUrl = 'https://myapp.com';

    const response = await initiateOAuth(mockProvider, currentUrl);

    const location = response.headers.get('Location')!;
    const locationUrl = new URL(location);
    expect(locationUrl.searchParams.get('scope')).toBe('read:user');
  });

  it('should handle special characters in currentUrl', async () => {
    const currentUrl =
      'https://myapp.com/path?query=hello world&foo=bar#section';

    const response = await initiateOAuth(mockProvider, currentUrl);

    const location = response.headers.get('Location')!;
    const locationUrl = new URL(location);
    const encodedState = locationUrl.searchParams.get('state')!;

    const decodedState = JSON.parse(atob(encodedState));
    expect(decodedState.returnUrl).toBe(currentUrl);
  });

  it('should preserve existing query parameters in auth URL', async () => {
    mockProvider.authUrl = 'https://example.com/oauth/authorize?custom=param';
    const currentUrl = 'https://myapp.com';

    const response = await initiateOAuth(mockProvider, currentUrl);

    const location = response.headers.get('Location')!;
    const locationUrl = new URL(location);
    expect(locationUrl.searchParams.get('custom')).toBe('param');
    expect(locationUrl.searchParams.get('response_type')).toBe('code');
  });

  it('should generate unique state for each call', async () => {
    const currentUrl = 'https://myapp.com';

    mockRandomUUID.mockReturnValueOnce('uuid-1').mockReturnValueOnce('uuid-2');

    const response1 = await initiateOAuth(mockProvider, currentUrl);
    const response2 = await initiateOAuth(mockProvider, currentUrl);

    const cookie1 = response1.headers.get('Set-Cookie')!;
    const cookie2 = response2.headers.get('Set-Cookie')!;

    expect(cookie1).toContain('oauth_state=uuid-1');
    expect(cookie2).toContain('oauth_state=uuid-2');
  });
});
