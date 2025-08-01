import type { Environment } from '@/worker/environment';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createGoogleProvider } from './google';

describe('Google OAuth Provider', () => {
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

  describe('createGoogleProvider', () => {
    it('should create Google provider with correct configuration', () => {
      const provider = createGoogleProvider(mockEnv);

      expect(provider.authUrl).toBe(
        'https://accounts.google.com/o/oauth2/v2/auth'
      );
      expect(provider.tokenUrl).toBe('https://oauth2.googleapis.com/token');
      expect(provider.userUrl).toBe(
        'https://www.googleapis.com/oauth2/v1/userinfo'
      );
      expect(provider.scopes).toEqual(['openid', 'email', 'profile']);
      expect(provider.clientId).toBe(mockEnv.GOOGLE_CLIENT_ID);
      expect(provider.clientSecret).toBe(mockEnv.GOOGLE_CLIENT_SECRET);
      expect(provider.callbackUrl).toBe(mockEnv.GOOGLE_CALLBACK_URL);
      expect(provider.mapUserData).toBeDefined();
    });
  });

  describe('mapUserData', () => {
    it('should map Google user data correctly', async () => {
      const provider = createGoogleProvider(mockEnv);
      const mockGoogleUser = {
        id: '1234567890',
        email: 'test@example.com',
        verified_email: true,
        name: 'Test User',
        given_name: 'Test',
        family_name: 'User',
        picture: 'https://lh3.googleusercontent.com/test',
        locale: 'en',
      };

      const result = await provider.mapUserData(
        mockGoogleUser,
        'mock-access-token'
      );

      expect(result).toEqual({
        email: 'test@example.com',
        name: 'Test User',
      });
    });

    it('should handle different locale values', async () => {
      const provider = createGoogleProvider(mockEnv);
      const mockGoogleUser = {
        id: '1234567890',
        email: 'test@example.com',
        verified_email: true,
        name: 'テストユーザー',
        given_name: 'テスト',
        family_name: 'ユーザー',
        picture: 'https://lh3.googleusercontent.com/test',
        locale: 'ja',
      };

      const result = await provider.mapUserData(
        mockGoogleUser,
        'mock-access-token'
      );

      expect(result).toEqual({
        email: 'test@example.com',
        name: 'テストユーザー',
      });
    });

    it('should handle unverified email', async () => {
      const provider = createGoogleProvider(mockEnv);
      const mockGoogleUser = {
        id: '1234567890',
        email: 'unverified@example.com',
        verified_email: false,
        name: 'Unverified User',
        given_name: 'Unverified',
        family_name: 'User',
        picture: 'https://lh3.googleusercontent.com/test',
        locale: 'en',
      };

      const result = await provider.mapUserData(
        mockGoogleUser,
        'mock-access-token'
      );

      expect(result).toEqual({
        email: 'unverified@example.com',
        name: 'Unverified User',
      });
    });

    it('should not use the access token parameter', async () => {
      const provider = createGoogleProvider(mockEnv);
      const mockGoogleUser = {
        id: '1234567890',
        email: 'test@example.com',
        verified_email: true,
        name: 'Test User',
        given_name: 'Test',
        family_name: 'User',
        picture: 'https://lh3.googleusercontent.com/test',
        locale: 'en',
      };

      // Test with different access tokens
      const result1 = await provider.mapUserData(mockGoogleUser, 'token1');
      const result2 = await provider.mapUserData(mockGoogleUser, 'token2');
      const result3 = await provider.mapUserData(mockGoogleUser, '');

      expect(result1).toEqual(result2);
      expect(result2).toEqual(result3);
      expect(result1).toEqual({
        email: 'test@example.com',
        name: 'Test User',
      });
    });
  });
});
