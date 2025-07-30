import { createOrUpdateUser, createSession } from '@/db/operations';
import type { User } from '@/db/schema';
import type { Database } from '@/db/utils';
import { baseUser, db } from '@/tests/db-setup';
import { handleLogout } from '@/worker/auth/logout';
import { handleMe } from '@/worker/auth/me';
import {
  LogoutErrorResponseSchema,
  LogoutSuccessResponseSchema,
  MeErrorResponseSchema,
  MeSuccessResponseSchema,
} from '@/worker/auth/schemas';
import type { Environment } from '@/worker/environment';
import type { Context } from 'hono';
import { beforeEach, describe, expect, it } from 'vitest';

// Type definitions for test responses
interface ApiResponse {
  success: boolean;
  error?: string;
  message?: string;
  user?: any;
}

describe('Auth Endpoints Integration Tests', () => {
  let testUser: User | null;
  let sessionToken: string;
  let mockEnv: Environment;

  beforeEach(async () => {
    // Create test user
    testUser = await createOrUpdateUser(db, baseUser);
    expect(testUser).toBeTruthy();

    // Create test session
    if (testUser) {
      const session = await createSession(db, testUser.id);
      sessionToken = session || '';
    }

    mockEnv = {
      DATABASE_URL: process.env.TEST_DATABASE_URL || '',
      ENVIRONMENT: 'test',
      GITHUB_CLIENT_ID: 'test-github-client',
      GITHUB_CLIENT_SECRET: 'test-github-secret',
      GITHUB_CALLBACK_URL: 'http://localhost:3000/auth/github/callback',
      GOOGLE_CLIENT_ID: 'test-google-client',
      GOOGLE_CLIENT_SECRET: 'test-google-secret',
      GOOGLE_CALLBACK_URL: 'http://localhost:3000/auth/google/callback',
      SITE_URL: 'http://localhost:3000',
    };
  });

  describe('handleMe with Zod validation', () => {
    it('returns response that matches MeSuccessResponseSchema', async () => {
      const mockContext = {
        get: (key: string) => {
          if (key === 'user') return testUser;
          return undefined;
        },
        json: (object: any, status?: number) => {
          return new Response(JSON.stringify(object), {
            status: status || 200,
            headers: { 'Content-Type': 'application/json' },
          });
        },
        env: mockEnv,
        var: {
          db,
          user: testUser,
        },
      } as unknown as Context<{
        Bindings: Environment;
        Variables: { db: Database; user: User };
      }>;

      const response = await handleMe(mockContext);
      const responseData = await response.json();

      // Validate response against schema
      const validation = MeSuccessResponseSchema.safeParse(responseData);

      expect(validation.success).toBe(true);
      if (validation.success) {
        expect(validation.data.success).toBe(true);
        expect(validation.data.user.id).toBe(testUser!.id);
        expect(validation.data.user.email).toBe(testUser!.email);
        expect(validation.data.user.name).toBe(testUser!.name);
      }
    });

    it('returns error response that matches MeErrorResponseSchema when error occurs', async () => {
      const mockContext = {
        get: (_key: string) => {
          throw new Error('Database error');
        },
        json: (object: any, status?: number) => {
          return new Response(JSON.stringify(object), {
            status: status || 200,
            headers: { 'Content-Type': 'application/json' },
          });
        },
        env: mockEnv,
        var: {
          db,
          user: testUser,
        },
      } as unknown as Context<{
        Bindings: Environment;
        Variables: { db: Database; user: User };
      }>;

      const response = await handleMe(mockContext);
      const responseData = await response.json();

      // Validate error response against schema
      const validation = MeErrorResponseSchema.safeParse(responseData);

      expect(validation.success).toBe(true);
      if (validation.success) {
        expect(validation.data.success).toBe(false);
        expect(validation.data.error).toBe('Internal server error');
      }
      expect(response.status).toBe(500);
    });
  });

  describe('handleLogout with Zod validation', () => {
    it('returns response that matches LogoutSuccessResponseSchema', async () => {
      const headers = new Headers();
      const mockRequest = new Request('http://localhost/auth/logout', {
        headers: {
          Cookie: `session=${sessionToken}`,
        },
      });
      const mockContext = {
        req: {
          raw: mockRequest,
          header: (name: string) => {
            if (name.toLowerCase() === 'cookie')
              return `session=${sessionToken}`;
            return null;
          },
        },
        header: (name: string, value: string) => {
          headers.set(name, value);
        },
        json: (object: any, status?: number) => {
          return new Response(JSON.stringify(object), {
            status: status || 200,
            headers: { 'Content-Type': 'application/json' },
          });
        },
        env: mockEnv,
        var: {
          db,
        },
        get: (key: string) => {
          if (key === 'db') return db;
          return undefined;
        },
      } as unknown as Context<{
        Bindings: Environment;
        Variables: { db: Database };
      }>;

      const response = await handleLogout(mockContext);
      const responseData = await response.json();

      // Validate response against schema
      const validation = LogoutSuccessResponseSchema.safeParse(responseData);

      expect(validation.success).toBe(true);
      if (validation.success) {
        expect(validation.data.success).toBe(true);
        expect(validation.data.message).toBe('Logged out successfully');
      }
    });

    it('returns error response that matches LogoutErrorResponseSchema when no session', async () => {
      const headers = new Headers();
      const mockRequest = new Request('http://localhost/auth/logout');
      const mockContext = {
        req: {
          raw: mockRequest,
          header: (_name: string) => null, // No cookie
        },
        header: (name: string, value: string) => {
          headers.set(name, value);
        },
        json: (object: any, status?: number) => {
          return new Response(JSON.stringify(object), {
            status: status || 200,
            headers: { 'Content-Type': 'application/json' },
          });
        },
        env: mockEnv,
        var: {
          db,
        },
        get: (key: string) => {
          if (key === 'db') return db;
          return undefined;
        },
      } as unknown as Context<{
        Bindings: Environment;
        Variables: { db: Database };
      }>;

      const response = await handleLogout(mockContext);
      const responseData = await response.json();

      // Validate error response against schema
      const validation = LogoutErrorResponseSchema.safeParse(responseData);

      expect(validation.success).toBe(true);
      if (validation.success) {
        expect(validation.data.success).toBe(false);
        expect(validation.data.error).toBe('No active session found');
      }
      expect(response.status).toBe(400);
    });

    it('handles database errors correctly', async () => {
      const headers = new Headers();
      const mockRequest = new Request('http://localhost/auth/logout', {
        headers: {
          Cookie: `session=${sessionToken}`,
        },
      });
      const mockContext = {
        req: {
          raw: mockRequest,
          header: (name: string) => {
            if (name === 'cookie') return `session=${sessionToken}`;
            return null;
          },
        },
        header: (name: string, value: string) => {
          headers.set(name, value);
        },
        json: (object: any, status?: number) => {
          return new Response(JSON.stringify(object), {
            status: status || 200,
            headers: { 'Content-Type': 'application/json' },
          });
        },
        env: mockEnv,
        var: {
          db: {
            delete: () => {
              throw new Error('Database connection failed');
            },
          } as Partial<Database> as Database,
        },
      } as unknown as Context<{
        Bindings: Environment;
        Variables: { db: Database };
      }>;

      const response = await handleLogout(mockContext);
      const responseData = await response.json();

      // Validate error response against schema
      const validation = LogoutErrorResponseSchema.safeParse(responseData);

      expect(validation.success).toBe(true);
      if (validation.success) {
        expect(validation.data.success).toBe(false);
        expect(validation.data.error).toBe('Logout failed');
      }
      expect(response.status).toBe(500);
    });
  });

  describe('Response Type Safety', () => {
    it('ensures all success responses have consistent structure', async () => {
      // Test that all success responses follow the pattern:
      // { success: true, ... }
      const mockContext = {
        get: (key: string) => {
          if (key === 'user') return testUser;
          return undefined;
        },
        json: (object: any, status?: number) => {
          return new Response(JSON.stringify(object), {
            status: status || 200,
            headers: { 'Content-Type': 'application/json' },
          });
        },
        env: mockEnv,
        var: {
          db,
          user: testUser,
        },
      } as unknown as Context<{
        Bindings: Environment;
        Variables: { db: Database; user: User };
      }>;

      const meResponse = await handleMe(mockContext);
      const meData = await meResponse.json();

      expect(meData).toHaveProperty('success');
      expect(typeof (meData as ApiResponse).success).toBe('boolean');
    });

    it('ensures all error responses have consistent structure', async () => {
      // Test that all error responses follow the pattern:
      // { success: false, error: string }
      const mockContext = {
        get: (_key: string) => {
          throw new Error('Test error');
        },
        json: (object: any, status?: number) => {
          return new Response(JSON.stringify(object), {
            status: status || 200,
            headers: { 'Content-Type': 'application/json' },
          });
        },
        env: mockEnv,
        var: {
          db,
          user: testUser,
        },
      } as unknown as Context<{
        Bindings: Environment;
        Variables: { db: Database; user: User };
      }>;

      const response = await handleMe(mockContext);
      const responseData = await response.json();

      expect(responseData).toHaveProperty('success');
      expect((responseData as ApiResponse).success).toBe(false);
      expect(responseData).toHaveProperty('error');
      expect(typeof (responseData as ApiResponse).error).toBe('string');
    });
  });
});
