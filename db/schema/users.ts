import { relations } from 'drizzle-orm';
import { pgTable, text, timestamp, uuid } from 'drizzle-orm/pg-core';
import { organizationMemberships } from './organization-memberships';
import { userConsents } from './user-consents';

export const users = pgTable('users', {
  id: uuid('id').primaryKey().defaultRandom(),
  email: text('email').notNull().unique(),
  name: text('name'),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
});

export const usersRelations = relations(users, ({ many }) => ({
  memberships: many(organizationMemberships),
  consents: many(userConsents),
}));

// Internal types
export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;

// Public types for API responses
export type PublicUser = Pick<User, 'id' | 'email' | 'name'>;
