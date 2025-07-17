import type { Context } from 'hono';
import type { Environment } from '@/worker/environment';
import type { User } from '@/db/schema';
import type { PostgresJsDatabase } from 'drizzle-orm/postgres-js';

export async function handleMe(
  c: Context<{
    Bindings: Environment;
    Variables: { db: PostgresJsDatabase; user: User };
  }>
): Promise<Response> {
  try {
    const user = c.get('user');
    return c.json({
      success: true,
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
      },
    });
  } catch (error) {
    console.error('Error in handleMe:', error);
    return c.json(
      {
        success: false,
        error: 'Internal server error',
      },
      500
    );
  }
}
