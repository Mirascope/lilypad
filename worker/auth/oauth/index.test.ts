import { describe, expect, it, vi } from 'vitest';
import { handleOAuthCallback as callbackHandleOAuthCallback } from './callback';
import {
  createGitHubProvider,
  createGoogleProvider,
  handleOAuthCallback,
  handleOAuthProxyCallback,
  initiateOAuth,
} from './index';
import { initiateOAuth as initiateInitiateOAuth } from './initiate';
import {
  createGitHubProvider as providersCreateGitHubProvider,
  createGoogleProvider as providersCreateGoogleProvider,
} from './providers';
import { handleOAuthProxyCallback as proxyHandleOAuthProxyCallback } from './proxy-callback';

vi.mock('./callback', () => ({
  handleOAuthCallback: vi.fn(),
}));

vi.mock('./initiate', () => ({
  initiateOAuth: vi.fn(),
}));

vi.mock('./providers', () => ({
  createGitHubProvider: vi.fn(),
  createGoogleProvider: vi.fn(),
}));

vi.mock('./proxy-callback', () => ({
  handleOAuthProxyCallback: vi.fn(),
}));

describe('auth/oauth/index.ts exports', () => {
  it('should re-export handleOAuthCallback from ./callback', () => {
    expect(handleOAuthCallback).toBeDefined();
    expect(handleOAuthCallback).toBe(callbackHandleOAuthCallback);
  });

  it('should re-export initiateOAuth from ./initiate', () => {
    expect(initiateOAuth).toBeDefined();
    expect(initiateOAuth).toBe(initiateInitiateOAuth);
  });

  it('should re-export createGitHubProvider from ./providers', () => {
    expect(createGitHubProvider).toBeDefined();
    expect(createGitHubProvider).toBe(providersCreateGitHubProvider);
  });

  it('should re-export createGoogleProvider from ./providers', () => {
    expect(createGoogleProvider).toBeDefined();
    expect(createGoogleProvider).toBe(providersCreateGoogleProvider);
  });

  it('should re-export handleOAuthProxyCallback from ./proxy-callback', () => {
    expect(handleOAuthProxyCallback).toBeDefined();
    expect(handleOAuthProxyCallback).toBe(proxyHandleOAuthProxyCallback);
  });

  it('should export all functions as mock functions', () => {
    expect(vi.isMockFunction(handleOAuthCallback)).toBe(true);
    expect(vi.isMockFunction(initiateOAuth)).toBe(true);
    expect(vi.isMockFunction(createGitHubProvider)).toBe(true);
    expect(vi.isMockFunction(createGoogleProvider)).toBe(true);
    expect(vi.isMockFunction(handleOAuthProxyCallback)).toBe(true);
  });

  it('should maintain same references as the source modules', () => {
    expect(handleOAuthCallback).toStrictEqual(callbackHandleOAuthCallback);
    expect(initiateOAuth).toStrictEqual(initiateInitiateOAuth);
    expect(createGitHubProvider).toStrictEqual(providersCreateGitHubProvider);
    expect(createGoogleProvider).toStrictEqual(providersCreateGoogleProvider);
    expect(handleOAuthProxyCallback).toStrictEqual(
      proxyHandleOAuthProxyCallback
    );
  });
});
