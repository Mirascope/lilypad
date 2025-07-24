import { relations } from 'drizzle-orm';
import { integer, pgTable, serial, text, timestamp } from 'drizzle-orm/pg-core';
import { users } from './users';

export const userConsents = pgTable('user_consents', {
  id: serial('id').primaryKey(),
  userId: integer('user_id')
    .references(() => users.id)
    .notNull(),
  privacyPolicyVersion: text('privacy_policy_version'),
  privacyPolicyAcceptedAt: timestamp('privacy_policy_accepted_at'),
  termsOfServiceVersion: text('terms_of_service_version'),
  termsOfServiceAcceptedAt: timestamp('terms_of_service_accepted_at'),
  createdAt: timestamp('created_at').defaultNow(),
});

export const userConsentsRelations = relations(userConsents, ({ one }) => ({
  user: one(users, {
    fields: [userConsents.userId],
    references: [users.id],
  }),
}));

// Internal types
export type UserConsent = typeof userConsents.$inferSelect;
export type NewUserConsent = typeof userConsents.$inferInsert;

// Public types
export type ConsentStatus = {
  hasValidPrivacyPolicy: boolean;
  hasValidTermsOfService: boolean;
  lastPrivacyPolicyVersion?: string;
  lastTermsOfServiceVersion?: string;
  lastPrivacyPolicyAcceptedAt?: Date;
  lastTermsOfServiceAcceptedAt?: Date;
};
