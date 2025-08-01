import { describe, expect, it, vi } from 'vitest';
import { createGitHubProvider as githubCreateGitHubProvider } from './github';
import { createGoogleProvider as googleCreateGoogleProvider } from './google';
import { createGitHubProvider, createGoogleProvider } from './index';

vi.mock('./github', () => ({
  createGitHubProvider: vi.fn(),
}));

vi.mock('./google', () => ({
  createGoogleProvider: vi.fn(),
}));

describe('auth/oauth/providers/index.ts exports', () => {
  it('should re-export createGitHubProvider from ./github', () => {
    expect(createGitHubProvider).toBeDefined();
    expect(createGitHubProvider).toBe(githubCreateGitHubProvider);
  });

  it('should re-export createGoogleProvider from ./google', () => {
    expect(createGoogleProvider).toBeDefined();
    expect(createGoogleProvider).toBe(googleCreateGoogleProvider);
  });

  it('should export the same function references as the source modules', () => {
    expect(createGitHubProvider).toStrictEqual(githubCreateGitHubProvider);
    expect(createGoogleProvider).toStrictEqual(googleCreateGoogleProvider);
  });

  it('should export both functions as mock functions', () => {
    expect(vi.isMockFunction(createGitHubProvider)).toBe(true);
    expect(vi.isMockFunction(createGoogleProvider)).toBe(true);
  });

  it('should be callable', () => {
    const mockEnv = { GITHUB_CLIENT_ID: 'test' };

    createGitHubProvider(mockEnv as any);
    expect(createGitHubProvider).toHaveBeenCalledWith(mockEnv);

    createGoogleProvider(mockEnv as any);
    expect(createGoogleProvider).toHaveBeenCalledWith(mockEnv);
  });
});
