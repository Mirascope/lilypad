import { sql } from 'drizzle-orm';
import { users, type NewUser, type User } from '@/db/schema';
import type { PostgresJsDatabase } from 'drizzle-orm/postgres-js';

export async function createOrUpdateUser(
  db: PostgresJsDatabase,
  userInfo: Omit<NewUser, 'id' | 'createdAt' | 'updatedAt'>
): Promise<User | null> {
  try {
    const result = await db
      .insert(users)
      .values({
        ...userInfo,
      })
      .onConflictDoUpdate({
        target: users.email,
        set: {
          name: userInfo.name,
          updatedAt: sql`CASE WHEN ${users.name} != ${userInfo.name} THEN NOW() ELSE ${users.updatedAt} END`,
        },
      })
      .returning();

    return result[0];
  } catch (error) {
    console.error('Error creating or updating user atomically:', error);
    return null;
  }
}
