import type { User } from '@/db/schema';
import type { Database } from '@/db/utils';
import type { Environment } from '@/worker/environment';
import type { Context } from 'hono';

export function handleMe(
  c: Context<{
    Bindings: Environment;
    Variables: { db: Database; user: User };
  }>
) {
  try {
    const user = c.get('user');
    return c.json(
      {
        success: true as const,
        user: {
          id: user.id,
          email: user.email,
          name: user.name,
        },
      },
      200
    );
  } catch (error) {
    console.error('Error in handleMe:', error);
    return c.json(
      {
        success: false as const,
        error: 'Internal server error',
      },
      500
    );
  }
}
