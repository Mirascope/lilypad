import { sessionIsValid } from '@/db/operations';
import { sessions, users } from '@/db/schema';
import type { User } from '@/db/schema/users';
import type { Database } from '@/db/utils';
import type { Environment } from '@/worker/environment';
import { eq } from 'drizzle-orm';
import type { MiddlewareHandler } from 'hono';
import { getSessionFromCookie } from '../utils';

export const authSessionMiddleware: MiddlewareHandler<{
  Bindings: Environment;
  Variables: { user: User; db: Database };
}> = async (c, next) => {
  const sessionId = getSessionFromCookie(c.req.raw);

  if (!sessionId) {
    return c.json(
      {
        success: false,
        error: 'Authentication required',
      },
      401
    );
  }

  const db = c.get('db');
  const isValid = await sessionIsValid(db, sessionId);

  if (!isValid) {
    // Clear invalid session cookie
    const clearCookie = [
      'session=',
      'HttpOnly',
      'Secure',
      'SameSite=Lax',
      'Max-Age=0',
      'Path=/',
    ].join('; ');

    return c.json(
      {
        success: false,
        error: 'Invalid or expired session',
      },
      401,
      {
        'Set-Cookie': clearCookie,
      }
    );
  }

  // Get user from session
  try {
    const result = await db
      .select({
        id: users.id,
        email: users.email,
        name: users.name,
        createdAt: users.createdAt,
        updatedAt: users.updatedAt,
      })
      .from(sessions)
      .innerJoin(users, eq(sessions.userId, users.id))
      .where(eq(sessions.id, sessionId))
      .limit(1);

    if (result.length === 0) {
      return c.json(
        {
          success: false,
          error: 'User not found',
        },
        401
      );
    }

    const user = result[0];
    c.set('user', user);

    await next();
  } catch (error) {
    console.error('Error getting user from session:', error);
    return c.json(
      {
        success: false,
        error: 'Authentication error',
      },
      500
    );
  }
};
