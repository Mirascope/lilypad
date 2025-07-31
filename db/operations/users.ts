import { users, type NewUser, type User } from '@/db/schema';
import type { Database } from '@/db/types';
import { eq, ne } from 'drizzle-orm';

export async function createOrUpdateUser(
  db: Database,
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
          updatedAt: new Date(),
        },
        where: ne(users.name, userInfo.name ?? ''),
      })
      .returning();

    if (result.length === 0) {
      const [existingUser] = await db
        .select()
        .from(users)
        .where(eq(users.email, userInfo.email))
        .limit(1);

      return existingUser;
    }

    return result[0];
  } catch (error) {
    console.error('Error creating or updating user atomically:', error);
    return null;
  }
}
