import type { Environment } from '@/worker/environment';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createGitHubProvider } from './github';

// Mock fetch globally
global.fetch = vi.fn() as any;

describe('GitHub OAuth Provider', () => {
  let mockEnv: Environment;

  beforeEach(() => {
    vi.clearAllMocks();

    mockEnv = {
      ENVIRONMENT: 'test',
      SITE_URL: 'http://localhost:3000',
      DATABASE_URL: 'postgresql://test:test@localhost:5432/test',
      GITHUB_CLIENT_ID: 'test-github-client-id',
      GITHUB_CLIENT_SECRET: 'test-github-client-secret',
      GITHUB_CALLBACK_URL: 'http://localhost:3000/auth/github/callback',
      GOOGLE_CLIENT_ID: 'test-google-client-id',
      GOOGLE_CLIENT_SECRET: 'test-google-client-secret',
      GOOGLE_CALLBACK_URL: 'http://localhost:3000/auth/google/callback',
    };
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('createGitHubProvider', () => {
    it('should create GitHub provider with correct configuration', () => {
      const provider = createGitHubProvider(mockEnv);

      expect(provider.authUrl).toBe('https://github.com/login/oauth/authorize');
      expect(provider.tokenUrl).toBe(
        'https://github.com/login/oauth/access_token'
      );
      expect(provider.userUrl).toBe('https://api.github.com/user');
      expect(provider.scopes).toEqual(['user:email']);
      expect(provider.clientId).toBe(mockEnv.GITHUB_CLIENT_ID);
      expect(provider.clientSecret).toBe(mockEnv.GITHUB_CLIENT_SECRET);
      expect(provider.callbackUrl).toBe(mockEnv.GITHUB_CALLBACK_URL);
      expect(provider.mapUserData).toBeDefined();
    });
  });

  describe('mapUserData', () => {
    it('should map GitHub user data when email is present', async () => {
      const provider = createGitHubProvider(mockEnv);
      const mockGitHubUser = {
        id: 123456,
        login: 'testuser',
        name: 'Test User',
        email: 'test@example.com',
        avatar_url: 'https://github.com/testuser.png',
        bio: 'Test bio',
        created_at: '2020-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      const result = await provider.mapUserData(
        mockGitHubUser,
        'mock-access-token'
      );

      expect(result).toEqual({
        email: 'test@example.com',
        name: 'Test User',
      });
      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('should fetch email from emails endpoint when not in profile', async () => {
      const provider = createGitHubProvider(mockEnv);
      const mockGitHubUser = {
        id: 123456,
        login: 'testuser',
        name: 'Test User',
        email: null,
        avatar_url: 'https://github.com/testuser.png',
        bio: 'Test bio',
        created_at: '2020-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      const mockEmails = [
        {
          email: 'secondary@example.com',
          primary: false,
          verified: true,
          visibility: 'public',
        },
        {
          email: 'primary@example.com',
          primary: true,
          verified: true,
          visibility: 'public',
        },
      ];

      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockEmails,
      } as Response);

      const result = await provider.mapUserData(
        mockGitHubUser,
        'mock-access-token'
      );

      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.github.com/user/emails',
        {
          headers: {
            Authorization: 'Bearer mock-access-token',
            Accept: 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
            'User-Agent': 'MyApp/1.0',
          },
        }
      );
      expect(result).toEqual({
        email: 'primary@example.com',
        name: 'Test User',
      });
    });

    it('should handle null name in GitHub user data', async () => {
      const provider = createGitHubProvider(mockEnv);
      const mockGitHubUser = {
        id: 123456,
        login: 'testuser',
        name: null,
        email: 'test@example.com',
        avatar_url: 'https://github.com/testuser.png',
        bio: null,
        created_at: '2020-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      const result = await provider.mapUserData(
        mockGitHubUser,
        'mock-access-token'
      );

      expect(result).toEqual({
        email: 'test@example.com',
        name: null,
      });
    });

    it('should handle failed email fetch gracefully', async () => {
      const provider = createGitHubProvider(mockEnv);
      const mockGitHubUser = {
        id: 123456,
        login: 'testuser',
        name: 'Test User',
        email: null,
        avatar_url: 'https://github.com/testuser.png',
        bio: 'Test bio',
        created_at: '2020-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 401,
      } as Response);

      const result = await provider.mapUserData(
        mockGitHubUser,
        'mock-access-token'
      );

      expect(result).toEqual({
        email: null,
        name: 'Test User',
      });
    });

    it('should handle empty email array', async () => {
      const provider = createGitHubProvider(mockEnv);
      const mockGitHubUser = {
        id: 123456,
        login: 'testuser',
        name: 'Test User',
        email: null,
        avatar_url: 'https://github.com/testuser.png',
        bio: 'Test bio',
        created_at: '2020-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response);

      const result = await provider.mapUserData(
        mockGitHubUser,
        'mock-access-token'
      );

      expect(result).toEqual({
        email: null,
        name: 'Test User',
      });
    });

    it('should handle no primary email in array', async () => {
      const provider = createGitHubProvider(mockEnv);
      const mockGitHubUser = {
        id: 123456,
        login: 'testuser',
        name: 'Test User',
        email: null,
        avatar_url: 'https://github.com/testuser.png',
        bio: 'Test bio',
        created_at: '2020-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      const mockEmails = [
        {
          email: 'secondary1@example.com',
          primary: false,
          verified: true,
          visibility: 'public',
        },
        {
          email: 'secondary2@example.com',
          primary: false,
          verified: true,
          visibility: 'private',
        },
      ];

      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockEmails,
      } as Response);

      const result = await provider.mapUserData(
        mockGitHubUser,
        'mock-access-token'
      );

      expect(result).toEqual({
        email: null,
        name: 'Test User',
      });
    });
  });
});
