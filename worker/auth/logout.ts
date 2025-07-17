import type { Environment } from '@/worker/environment';
import { deleteSession } from '@/db/operations';
import { getSessionFromCookie } from './utils';
import type { Context } from 'hono';
import type { PostgresJsDatabase } from 'drizzle-orm/postgres-js';

export async function handleLogout(
  c: Context<{ Bindings: Environment; Variables: { db: PostgresJsDatabase } }>
): Promise<Response> {
  try {
    const sessionId = getSessionFromCookie(c.req.raw);

    if (!sessionId) {
      return c.json(
        {
          success: false,
          error: 'No active session found',
        },
        400
      );
    }

    const db = c.get('db');
    await deleteSession(db, sessionId);

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
        success: true,
        message: 'Logged out successfully',
      },
      200,
      {
        'Set-Cookie': clearCookie,
      }
    );
  } catch (error) {
    console.error('Error during logout:', error);
    return c.json(
      {
        success: false,
        error: 'Logout failed',
      },
      500
    );
  }
}
