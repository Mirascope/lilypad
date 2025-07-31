import { createOrUpdateUser, createSession } from '@/db/operations';
import type { User } from '@/db/schema';
import { baseUser, db } from '@/tests/db-setup';
import { createMockContext } from '@/tests/worker-setup';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { authSessionMiddleware } from './session';

describe('authSessionMiddleware', () => {
  let mockContext: any;
  let mockNext: any;
  let testUser: User;
  let testSessionId: string;

  beforeEach(async () => {
    vi.clearAllMocks();

    // Create test user and session
    testUser = (await createOrUpdateUser(db, baseUser))!;
    testSessionId = (await createSession(db, testUser.id))!;

    mockNext = vi.fn();
    mockContext = createMockContext({
      path: '/auth/me',
    });
  });

  describe('extractSessionId', () => {
    it('should extract session ID from cookie', async () => {
      mockContext = createMockContext({
        path: '/auth/me',
        headers: { Cookie: `session=${testSessionId}` },
      });

      await authSessionMiddleware(mockContext, mockNext);

      expect(mockNext).toHaveBeenCalled();
      expect(mockContext.set).toHaveBeenCalledWith(
        'user',
        expect.objectContaining({
          id: testUser.id,
          email: testUser.email,
          name: testUser.name,
        })
      );
    });

    it('should handle multiple cookies', async () => {
      mockContext = createMockContext({
        path: '/auth/me',
        headers: {
          Cookie: `other=value; session=${testSessionId}; another=value2`,
        },
      });

      await authSessionMiddleware(mockContext, mockNext);

      expect(mockNext).toHaveBeenCalled();
      expect(mockContext.set).toHaveBeenCalledWith(
        'user',
        expect.objectContaining({
          id: testUser.id,
          email: testUser.email,
          name: testUser.name,
        })
      );
    });

    it('should handle cookies with spaces', async () => {
      mockContext = createMockContext({
        path: '/auth/me',
        headers: {
          Cookie: `other=value;  session=${testSessionId};  another=value2`,
        },
      });

      await authSessionMiddleware(mockContext, mockNext);

      expect(mockNext).toHaveBeenCalled();
      expect(mockContext.set).toHaveBeenCalledWith(
        'user',
        expect.objectContaining({
          id: testUser.id,
          email: testUser.email,
          name: testUser.name,
        })
      );
    });
  });

  describe('authentication flow', () => {
    it('should return 401 when no cookie header', async () => {
      mockContext = createMockContext({
        path: '/auth/me',
      });

      await authSessionMiddleware(mockContext, mockNext);

      expect(mockContext.json).toHaveBeenCalledWith(
        {
          success: false,
          error: 'Authentication required',
        },
        401
      );
      expect(mockNext).not.toHaveBeenCalled();
    });

    it('should return 401 when no session cookie', async () => {
      mockContext = createMockContext({
        path: '/auth/me',
        headers: { Cookie: 'other=value' },
      });

      await authSessionMiddleware(mockContext, mockNext);

      expect(mockContext.json).toHaveBeenCalledWith(
        {
          success: false,
          error: 'Authentication required',
        },
        401
      );
      expect(mockNext).not.toHaveBeenCalled();
    });

    it('should return 401 with clear cookie when session is invalid', async () => {
      mockContext = createMockContext({
        path: '/auth/me',
        headers: { Cookie: 'session=invalid-session' },
      });

      await authSessionMiddleware(mockContext, mockNext);

      expect(mockContext.json).toHaveBeenCalledWith(
        {
          success: false,
          error: 'Invalid or expired session',
        },
        401,
        {
          'Set-Cookie':
            'session=; HttpOnly; Secure; SameSite=Lax; Max-Age=0; Path=/',
        }
      );
      expect(mockNext).not.toHaveBeenCalled();
    });

    it('should successfully authenticate and set user', async () => {
      mockContext = createMockContext({
        path: '/auth/me',
        headers: { Cookie: `session=${testSessionId}` },
      });

      await authSessionMiddleware(mockContext, mockNext);

      expect(mockContext.set).toHaveBeenCalledWith(
        'user',
        expect.objectContaining({
          id: testUser.id,
          email: testUser.email,
          name: testUser.name,
          createdAt: expect.any(Date),
          updatedAt: expect.any(Date),
        })
      );
      expect(mockNext).toHaveBeenCalled();
      expect(mockContext.json).not.toHaveBeenCalled();
    });

    it('should return 401 when user not found in database', async () => {
      // Mock the user query to return empty result after sessionIsValid passes
      mockContext = createMockContext({
        path: '/auth/me',
        headers: { Cookie: `session=${testSessionId}` },
      });

      // Mock select to return valid session but no user
      let callCount = 0;
      const originalSelect = db.select.bind(db);
      const dbSpy = vi.spyOn(db, 'select').mockImplementation((...args) => {
        callCount++;
        // First call is sessionIsValid - let it pass
        if (callCount === 1) {
          return originalSelect(...args);
        }
        // Second call is the user query - return empty result
        return {
          from: vi.fn().mockReturnThis(),
          innerJoin: vi.fn().mockReturnThis(),
          where: vi.fn().mockReturnThis(),
          limit: vi.fn().mockResolvedValue([]), // Empty result - no user found
        } as any;
      });

      await authSessionMiddleware(mockContext, mockNext);

      expect(mockContext.json).toHaveBeenCalledWith(
        {
          success: false,
          error: 'User not found',
        },
        401
      );
      expect(mockNext).not.toHaveBeenCalled();

      dbSpy.mockRestore();
    });

    it('should handle database errors', async () => {
      mockContext = createMockContext({
        path: '/auth/me',
        headers: { Cookie: `session=${testSessionId}` },
      });

      // Mock database error at the sessionIsValid check
      const dbSpy = vi.spyOn(db, 'select').mockImplementation(() => {
        throw new Error('Database error');
      });

      const consoleErrorSpy = vi
        .spyOn(console, 'error')
        .mockImplementation(() => {});

      await authSessionMiddleware(mockContext, mockNext);

      // When sessionIsValid fails, it returns false and the middleware treats it as invalid session
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Error checking session validity:',
        expect.any(Error)
      );
      expect(mockContext.json).toHaveBeenCalledWith(
        {
          success: false,
          error: 'Invalid or expired session',
        },
        401,
        {
          'Set-Cookie':
            'session=; HttpOnly; Secure; SameSite=Lax; Max-Age=0; Path=/',
        }
      );
      expect(mockNext).not.toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
      dbSpy.mockRestore();
    });

    it('should get database from context', async () => {
      mockContext = createMockContext({
        path: '/auth/me',
        headers: { Cookie: `session=${testSessionId}` },
      });

      await authSessionMiddleware(mockContext, mockNext);

      expect(mockContext.get).toHaveBeenCalledWith('db');
    });
  });

  describe('edge cases', () => {
    it('should handle errors after user is set', async () => {
      mockContext = createMockContext({
        path: '/auth/me',
        headers: { Cookie: `session=${testSessionId}` },
      });

      // Mock next() to throw an error after user is set
      mockNext = vi.fn().mockRejectedValue(new Error('Next middleware error'));

      const consoleErrorSpy = vi
        .spyOn(console, 'error')
        .mockImplementation(() => {});

      await authSessionMiddleware(mockContext, mockNext);

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Error getting user from session:',
        expect.any(Error)
      );
      expect(mockContext.json).toHaveBeenCalledWith(
        {
          success: false,
          error: 'Authentication error',
        },
        500
      );

      consoleErrorSpy.mockRestore();
    });

    it('should handle empty session cookie value', async () => {
      mockContext = createMockContext({
        path: '/auth/me',
        headers: { Cookie: 'session=' },
      });

      await authSessionMiddleware(mockContext, mockNext);

      expect(mockContext.json).toHaveBeenCalledWith(
        {
          success: false,
          error: 'Authentication required',
        },
        401
      );
    });

    it('should handle malformed cookie', async () => {
      mockContext = createMockContext({
        path: '/auth/me',
        headers: { Cookie: 'session' },
      });

      await authSessionMiddleware(mockContext, mockNext);

      expect(mockContext.json).toHaveBeenCalledWith(
        {
          success: false,
          error: 'Authentication required',
        },
        401
      );
    });

    it('should handle session cookie with spaces in name', async () => {
      mockContext = createMockContext({
        path: '/auth/me',
        headers: { Cookie: 'session =valid-session' },
      });

      await authSessionMiddleware(mockContext, mockNext);

      expect(mockContext.json).toHaveBeenCalledWith(
        {
          success: false,
          error: 'Authentication required',
        },
        401
      );
    });
  });
});
