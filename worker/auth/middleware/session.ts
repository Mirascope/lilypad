import type { MiddlewareHandler } from 'hono';
import { sessionIsValid } from '@/db/operations';
import { eq } from 'drizzle-orm';
import { sessions } from '@/db/schema';
import { users } from '@/db/schema/users';
import type { User } from '@/db/schema/users';
import type { Environment } from '@/worker/environment';
import type { PostgresJsDatabase } from 'drizzle-orm/postgres-js';

function extractSessionId(request: Request): string | null {
  const cookieHeader = request.headers.get('Cookie');

  if (!cookieHeader) {
    return null;
  }

  const cookies = cookieHeader.split(';');
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'session') {
      return value || null;
    }
  }
  return null;
}

export const authSessionMiddleware: MiddlewareHandler<{
  Bindings: Environment;
  Variables: { user: User; db: PostgresJsDatabase };
}> = async (c, next) => {
  const sessionId = extractSessionId(c.req.raw);

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
