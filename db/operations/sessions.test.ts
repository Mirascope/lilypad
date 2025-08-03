import { sessions } from '@/db/schema';
import { baseUser, db } from '@/tests/db';
import { eq } from 'drizzle-orm';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  createSession,
  deleteExpiredSessions,
  deleteSession,
  deleteUserSessions,
  sessionIsExpired,
  sessionIsValid,
} from './sessions';
import { createOrUpdateUser } from './users';

describe('session operations', () => {
  let testUserId: string;

  beforeEach(async () => {
    // Create a fresh test user for each test
    const user = await createOrUpdateUser(db, baseUser);
    testUserId = user!.id;
  });

  describe('createSession', () => {
    it('creates a new session for a user', async () => {
      const sessionId = await createSession(db, testUserId);

      expect(sessionId).toBeTruthy();
      expect(typeof sessionId).toBe('string');
      expect(sessionId!.length).toBe(64); // 32 bytes * 2 hex chars
    });

    it('creates unique session IDs', async () => {
      const sessionId1 = await createSession(db, testUserId);
      const sessionId2 = await createSession(db, testUserId);

      expect(sessionId1).not.toBe(sessionId2);
    });

    it('sets expiration date correctly', async () => {
      const beforeCreate = new Date();
      const sessionId = await createSession(db, testUserId);
      const afterCreate = new Date();

      const [session] = await db
        .select()
        .from(sessions)
        .where(eq(sessions.id, sessionId!));

      expect(session).toBeTruthy();

      // Should expire approximately 7 days from now
      const expectedExpiry = new Date(
        beforeCreate.getTime() + 7 * 24 * 60 * 60 * 1000
      );
      const actualExpiry = session.expiresAt;

      // Allow for some variance in timing
      expect(actualExpiry.getTime()).toBeGreaterThan(
        expectedExpiry.getTime() - 1000
      );
      expect(actualExpiry.getTime()).toBeLessThan(
        expectedExpiry.getTime() +
          1000 +
          (afterCreate.getTime() - beforeCreate.getTime())
      );
    });

    it('returns null when database error occurs', async () => {
      const consoleSpy = vi
        .spyOn(console, 'error')
        .mockImplementation(() => {});
      const dbSpy = vi.spyOn(db, 'insert').mockImplementation(() => {
        throw new Error('Database connection failed');
      });

      const result = await createSession(db, testUserId);

      expect(result).toBeNull();
      expect(consoleSpy).toHaveBeenCalledWith(
        'Error creating session:',
        expect.any(Error)
      );

      consoleSpy.mockRestore();
      dbSpy.mockRestore();
    });
  });

  describe('sessionIsExpired', () => {
    it('returns false for future expiration date', () => {
      const futureDate = new Date(Date.now() + 1000 * 60 * 60); // 1 hour from now
      expect(sessionIsExpired({ expiresAt: futureDate })).toBe(false);
    });

    it('returns true for past expiration date', () => {
      const pastDate = new Date(Date.now() - 1000 * 60 * 60); // 1 hour ago
      expect(sessionIsExpired({ expiresAt: pastDate })).toBe(true);
    });
  });

  describe('sessionIsValid', () => {
    it('returns true for valid unexpired session', async () => {
      const sessionId = await createSession(db, testUserId);
      const isValid = await sessionIsValid(db, sessionId!);

      expect(isValid).toBe(true);
    });

    it('returns false for non-existent session', async () => {
      const isValid = await sessionIsValid(db, 'non-existent-session-id');

      expect(isValid).toBe(false);
    });

    it('returns false and deletes expired session', async () => {
      // Create a session with past expiration
      const sessionId = 'test-expired-session';
      await db.insert(sessions).values({
        id: sessionId,
        userId: testUserId,
        expiresAt: new Date(Date.now() - 1000 * 60 * 60), // 1 hour ago
      });

      const isValid = await sessionIsValid(db, sessionId);

      expect(isValid).toBe(false);

      // Verify session was deleted
      const [deletedSession] = await db
        .select()
        .from(sessions)
        .where(eq(sessions.id, sessionId));

      expect(deletedSession).toBeUndefined();
    });

    it('returns false when database error occurs', async () => {
      const consoleSpy = vi
        .spyOn(console, 'error')
        .mockImplementation(() => {});
      const dbSpy = vi.spyOn(db, 'select').mockImplementation(() => {
        throw new Error('Database connection failed');
      });

      const result = await sessionIsValid(db, 'test-session');

      expect(result).toBe(false);
      expect(consoleSpy).toHaveBeenCalledWith(
        'Error checking session validity:',
        expect.any(Error)
      );

      consoleSpy.mockRestore();
      dbSpy.mockRestore();
    });
  });

  describe('deleteSession', () => {
    it('deletes a specific session', async () => {
      const sessionId = await createSession(db, testUserId);

      await deleteSession(db, sessionId!);

      const [deletedSession] = await db
        .select()
        .from(sessions)
        .where(eq(sessions.id, sessionId!));

      expect(deletedSession).toBeUndefined();
    });

    it('handles deletion of non-existent session gracefully', async () => {
      // Should not throw
      await expect(
        deleteSession(db, 'non-existent-session')
      ).resolves.toBeUndefined();
    });

    it('handles database error gracefully', async () => {
      const consoleSpy = vi
        .spyOn(console, 'error')
        .mockImplementation(() => {});
      const dbSpy = vi.spyOn(db, 'delete').mockImplementation(() => {
        throw new Error('Database connection failed');
      });

      await expect(deleteSession(db, 'test-session')).resolves.toBeUndefined();
      expect(consoleSpy).toHaveBeenCalledWith(
        'Error deleting session:',
        expect.any(Error)
      );

      consoleSpy.mockRestore();
      dbSpy.mockRestore();
    });
  });

  describe('deleteUserSessions', () => {
    it('deletes all sessions for a specific user', async () => {
      // Create multiple sessions for the user
      await createSession(db, testUserId);
      await createSession(db, testUserId);

      await deleteUserSessions(db, testUserId);

      const userSessions = await db
        .select()
        .from(sessions)
        .where(eq(sessions.userId, testUserId));

      expect(userSessions).toHaveLength(0);
    });

    it('only deletes sessions for the specified user', async () => {
      // Create another test user
      const otherUser = await createOrUpdateUser(db, {
        email: 'other-user@example.com',
        name: 'Other User',
      });

      await createSession(db, testUserId);
      await createSession(db, otherUser!.id);

      const totalSessions = (await db.select().from(sessions)).length;
      await deleteUserSessions(db, testUserId);
      const remainingSessions = await db.select().from(sessions);

      expect(remainingSessions).toHaveLength(totalSessions - 1);
      expect(remainingSessions[0].userId).toBe(otherUser!.id);
    });

    it('handles database error gracefully', async () => {
      const consoleSpy = vi
        .spyOn(console, 'error')
        .mockImplementation(() => {});
      const dbSpy = vi.spyOn(db, 'delete').mockImplementation(() => {
        throw new Error('Database connection failed');
      });

      await expect(deleteUserSessions(db, testUserId)).resolves.toBeUndefined();
      expect(consoleSpy).toHaveBeenCalledWith(
        'Error deleting user sessions:',
        expect.any(Error)
      );

      consoleSpy.mockRestore();
      dbSpy.mockRestore();
    });
  });

  describe('deleteExpiredSessions', () => {
    it('deletes only expired sessions', async () => {
      // Create a valid session
      const validSessionId = await createSession(db, testUserId);

      // Create an expired session
      const expiredSessionId = 'expired-session';
      await db.insert(sessions).values({
        id: expiredSessionId,
        userId: testUserId,
        expiresAt: new Date(Date.now() - 1000 * 60 * 60), // 1 hour ago
      });

      const deletedCount = await deleteExpiredSessions(db);

      expect(deletedCount).toBe(1);

      // Verify valid session still exists
      const [validSession] = await db
        .select()
        .from(sessions)
        .where(eq(sessions.id, validSessionId!));

      expect(validSession).toBeTruthy();

      // Verify expired session was deleted
      const [expiredSession] = await db
        .select()
        .from(sessions)
        .where(eq(sessions.id, expiredSessionId));

      expect(expiredSession).toBeUndefined();
    });

    it('returns correct count of deleted sessions', async () => {
      // Create multiple expired sessions
      await db.insert(sessions).values([
        {
          id: 'expired-1',
          userId: testUserId,
          expiresAt: new Date(Date.now() - 1000 * 60 * 60),
        },
        {
          id: 'expired-2',
          userId: testUserId,
          expiresAt: new Date(Date.now() - 2000 * 60 * 60),
        },
      ]);

      const deletedCount = await deleteExpiredSessions(db);

      expect(deletedCount).toBe(2);
    });

    it('returns 0 when no expired sessions exist', async () => {
      const deletedCount = await deleteExpiredSessions(db);

      expect(deletedCount).toBe(0);
    });

    it('returns 0 when database error occurs', async () => {
      const consoleSpy = vi
        .spyOn(console, 'error')
        .mockImplementation(() => {});
      const dbSpy = vi.spyOn(db, 'delete').mockImplementation(() => {
        throw new Error('Database connection failed');
      });

      const result = await deleteExpiredSessions(db);

      expect(result).toBe(0);
      expect(consoleSpy).toHaveBeenCalledWith(
        'Error deleting expired sessions:',
        expect.any(Error)
      );

      consoleSpy.mockRestore();
      dbSpy.mockRestore();
    });
  });
});
