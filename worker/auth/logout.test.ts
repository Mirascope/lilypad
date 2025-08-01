import { createOrUpdateUser, createSession } from '@/db/operations';
import { sessions } from '@/db/schema';
import { baseUser, db } from '@/tests/db-setup';
import { createMockContext } from '@/tests/worker-setup';
import { eq } from 'drizzle-orm';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { handleLogout } from './logout';
import * as utils from './utils';

vi.mock('./utils');

describe('handleLogout', () => {
  let mockContext: any;
  let testUserId: string;
  let testSessionId: string;

  beforeEach(async () => {
    vi.clearAllMocks();

    // Create test user and session
    const user = await createOrUpdateUser(db, baseUser);
    testUserId = user!.id;
    testSessionId = (await createSession(db, testUserId)) || 'test-session';

    mockContext = createMockContext({
      path: '/auth/logout',
    });
  });

  it('should successfully logout with valid session', async () => {
    vi.mocked(utils.getSessionFromCookie).mockReturnValue(testSessionId);

    await handleLogout(mockContext);

    expect(utils.getSessionFromCookie).toHaveBeenCalledWith(
      mockContext.req.raw
    );

    // Verify session was deleted from database
    const deletedSession = await db
      .select()
      .from(sessions)
      .where(eq(sessions.id, testSessionId))
      .limit(1);

    expect(deletedSession).toHaveLength(0);

    expect(mockContext.json).toHaveBeenCalledWith(
      {
        success: true,
        message: 'Logged out successfully',
      },
      200,
      {
        'Set-Cookie':
          'session=; HttpOnly; Secure; SameSite=Lax; Max-Age=0; Path=/',
      }
    );
  });

  it('should return 400 when no session found', async () => {
    vi.mocked(utils.getSessionFromCookie).mockReturnValue(null);

    await handleLogout(mockContext);

    expect(utils.getSessionFromCookie).toHaveBeenCalledWith(
      mockContext.req.raw
    );
    expect(mockContext.json).toHaveBeenCalledWith(
      {
        success: false,
        error: 'No active session found',
      },
      400
    );
  });

  it('should handle database errors gracefully', async () => {
    vi.mocked(utils.getSessionFromCookie).mockReturnValue(testSessionId);

    // Mock database error
    const dbSpy = vi.spyOn(db, 'delete').mockImplementation(() => {
      throw new Error('Database error');
    });

    const consoleErrorSpy = vi
      .spyOn(console, 'error')
      .mockImplementation(() => {});

    await handleLogout(mockContext);

    expect(consoleErrorSpy).toHaveBeenCalledWith(
      'Error deleting session:',
      expect.any(Error)
    );

    // Since deleteSession swallows the error, logout still succeeds
    expect(mockContext.json).toHaveBeenCalledWith(
      {
        success: true,
        message: 'Logged out successfully',
      },
      200,
      {
        'Set-Cookie':
          'session=; HttpOnly; Secure; SameSite=Lax; Max-Age=0; Path=/',
      }
    );

    consoleErrorSpy.mockRestore();
    dbSpy.mockRestore();
  });

  it('should handle unexpected errors gracefully', async () => {
    vi.mocked(utils.getSessionFromCookie).mockImplementation(() => {
      throw new Error('Unexpected error');
    });

    const consoleErrorSpy = vi
      .spyOn(console, 'error')
      .mockImplementation(() => {});

    await handleLogout(mockContext);

    expect(consoleErrorSpy).toHaveBeenCalledWith(
      'Error during logout:',
      expect.any(Error)
    );
    expect(mockContext.json).toHaveBeenCalledWith(
      {
        success: false,
        error: 'Logout failed',
      },
      500
    );

    consoleErrorSpy.mockRestore();
  });

  it('should get database from context', async () => {
    vi.mocked(utils.getSessionFromCookie).mockReturnValue(testSessionId);

    await handleLogout(mockContext);

    expect(mockContext.get).toHaveBeenCalledWith('db');
  });

  it('should clear cookie with correct attributes', async () => {
    vi.mocked(utils.getSessionFromCookie).mockReturnValue(testSessionId);

    await handleLogout(mockContext);

    const setCookieHeader = mockContext.json.mock.calls[0][2]['Set-Cookie'];

    expect(setCookieHeader).toContain('session=');
    expect(setCookieHeader).toContain('HttpOnly');
    expect(setCookieHeader).toContain('Secure');
    expect(setCookieHeader).toContain('SameSite=Lax');
    expect(setCookieHeader).toContain('Max-Age=0');
    expect(setCookieHeader).toContain('Path=/');
  });

  it('should handle non-existent session ID', async () => {
    const nonExistentSessionId = 'non-existent-session-id';
    vi.mocked(utils.getSessionFromCookie).mockReturnValue(nonExistentSessionId);

    await handleLogout(mockContext);

    // Should still return success even if session doesn't exist
    expect(mockContext.json).toHaveBeenCalledWith(
      {
        success: true,
        message: 'Logged out successfully',
      },
      200,
      {
        'Set-Cookie':
          'session=; HttpOnly; Secure; SameSite=Lax; Max-Age=0; Path=/',
      }
    );
  });
});
