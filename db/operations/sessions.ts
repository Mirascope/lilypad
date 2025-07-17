import { eq, lt } from 'drizzle-orm';
import {
  sessions,
  DEFAULT_SESSION_DURATION,
  type NewSession,
} from '@/db/schema';
import type { PostgresJsDatabase } from 'drizzle-orm/postgres-js';

function generateSessionId(): string {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return Array.from(array, (byte) => byte.toString(16).padStart(2, '0')).join(
    ''
  );
}

export function sessionIsExpired(session: { expiresAt: Date }): boolean {
  return new Date() > session.expiresAt;
}

export async function createSession(
  db: PostgresJsDatabase,
  userId: number
): Promise<string | null> {
  try {
    const sessionId = generateSessionId();
    const expiresAt = new Date(Date.now() + DEFAULT_SESSION_DURATION); // 7 days

    const newSession: NewSession = {
      id: sessionId,
      userId,
      expiresAt,
    };

    await db.insert(sessions).values(newSession);

    return sessionId;
  } catch (error) {
    console.error('Error creating session:', error);
    return null;
  }
}

export async function deleteSession(
  db: PostgresJsDatabase,
  sessionId: string
): Promise<void> {
  try {
    await db.delete(sessions).where(eq(sessions.id, sessionId));
  } catch (error) {
    console.error('Error deleting session:', error);
  }
}

export async function deleteUserSessions(
  db: PostgresJsDatabase,
  userId: number
): Promise<void> {
  try {
    await db.delete(sessions).where(eq(sessions.userId, userId));
  } catch (error) {
    console.error('Error deleting user sessions:', error);
  }
}

export async function deleteExpiredSessions(
  db: PostgresJsDatabase
): Promise<number> {
  try {
    const result = await db
      .delete(sessions)
      .where(lt(sessions.expiresAt, new Date()));
    return result.count || 0;
  } catch (error) {
    console.error('Error deleting expired sessions:', error);
    return 0;
  }
}

export async function sessionIsValid(
  db: PostgresJsDatabase,
  sessionId: string
): Promise<boolean> {
  try {
    const [session] = await db
      .select()
      .from(sessions)
      .where(eq(sessions.id, sessionId))
      .limit(1);

    if (!session) {
      return false;
    }

    if (sessionIsExpired(session)) {
      // Delete expired session
      await deleteSession(db, sessionId);
      return false;
    }

    return true;
  } catch (error) {
    console.error('Error checking session validity:', error);
    return false;
  }
}
