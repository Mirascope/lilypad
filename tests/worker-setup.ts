import { afterEach, vi } from 'vitest';
import { db } from './db-setup';

// Mock Cloudflare Worker environment
export const mockEnv = {
  ENVIRONMENT: 'test',
  SITE_URL: 'http://localhost:3000',
  DATABASE_URL: process.env.TEST_DATABASE_URL!,
  GITHUB_CLIENT_ID: 'test-github-client-id',
  GITHUB_CLIENT_SECRET: 'test-github-client-secret',
  GITHUB_CALLBACK_URL: 'http://localhost:3000/auth/github/callback',
  GOOGLE_CLIENT_ID: 'test-google-client-id',
  GOOGLE_CLIENT_SECRET: 'test-google-client-secret',
  GOOGLE_CALLBACK_URL: 'http://localhost:3000/auth/google/callback',
};

// Mock fetch globally for external APIs only
global.fetch = vi.fn() as any;

// Reset mocks after each test
afterEach(() => {
  vi.clearAllMocks();
  vi.resetAllMocks();
});

// Mock Hono Context with real database
export const createMockContext = (overrides?: any) => {
  const headers = new Headers(overrides?.headers || {});

  // Handle path with query parameters
  let url = 'http://localhost:3000' + (overrides?.path || '/');
  if (overrides?.query) {
    const params = new URLSearchParams(overrides.query);
    url += '?' + params.toString();
  }

  const request = new Request(url, {
    method: overrides?.method || 'GET',
    headers,
    body: overrides?.body,
  });

  const context = {
    req: {
      ...request,
      url: request.url,
      header: (name: string) => headers.get(name),
      json: () => request.json(),
      text: () => request.text(),
      param: (key: string) => overrides?.params?.[key],
      query: (key: string) => overrides?.query?.[key],
      raw: request,
    },
    env: { ...mockEnv, ...overrides?.env },
    json: vi.fn((data: any, status?: number) => ({
      body: JSON.stringify(data),
      status: status || 200,
      headers: { 'Content-Type': 'application/json' },
    })),
    text: vi.fn((text: string, status?: number) => ({
      body: text,
      status: status || 200,
      headers: { 'Content-Type': 'text/plain' },
    })),
    header: vi.fn(),
    status: vi.fn(),
    redirect: vi.fn((url: string, status?: number) => ({
      status: status || 302,
      headers: { Location: url },
    })),
    set: vi.fn(),
    get: vi.fn(),
    var: {
      db: db, // Use real database connection
      ...overrides?.var,
    },
    ...overrides,
  };

  // Setup get/set to work with var
  context.set = vi.fn((key: string, value: any) => {
    context.var[key] = value;
  });
  context.get = vi.fn((key: string) => {
    // Return real db when 'db' is requested
    if (key === 'db') return db;
    return context.var[key];
  });

  return context;
};

// Mock OAuth responses
export const mockGitHubTokenResponse = {
  access_token: 'mock-github-access-token',
  token_type: 'bearer',
  scope: 'user:email',
};

export const mockGitHubUserResponse = {
  id: 123456,
  login: 'testuser',
  name: 'Test User',
  email: 'test@example.com',
  avatar_url: 'https://github.com/testuser.png',
};

export const mockGitHubEmailsResponse = [
  {
    email: 'test@example.com',
    primary: true,
    verified: true,
    visibility: 'public',
  },
];

export const mockGoogleTokenResponse = {
  access_token: 'mock-google-access-token',
  token_type: 'Bearer',
  expires_in: 3600,
  refresh_token: 'mock-google-refresh-token',
  scope: 'openid email profile',
  id_token: 'mock-google-id-token',
};

export const mockGoogleUserInfoResponse = {
  sub: '1234567890',
  name: 'Test User',
  given_name: 'Test',
  family_name: 'User',
  picture: 'https://lh3.googleusercontent.com/test',
  email: 'test@example.com',
  email_verified: true,
  locale: 'en',
};

// Helper to mock successful fetch responses
export const mockFetchSuccess = (data: any, options?: any): Response => {
  return {
    ok: true,
    status: 200,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
    headers: new Headers(options?.headers || {}),
    ...options,
  } as Response;
};

// Helper to mock failed fetch responses
export const mockFetchError = (status: number, message: string): Response => {
  return {
    ok: false,
    status,
    statusText: message,
    json: () => Promise.resolve({ error: message }),
    text: () => Promise.resolve(message),
    headers: new Headers(),
  } as Response;
};
