import * as dotenv from 'dotenv';
import { sql as sqlTag } from 'drizzle-orm';
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import { afterEach, beforeEach } from 'vitest';

dotenv.config({ path: '.env.local', override: true });

if (process.env.TEST_DATABASE_URL === undefined) {
  throw new Error(
    'TEST_DATABASE_URL is undefined. Make sure to set it in the environment'
  );
}

const sql = postgres(process.env.TEST_DATABASE_URL, {
  max: 1,
  prepare: false,
});
export const db = drizzle(sql);

beforeEach(async () => {
  await db.execute(sqlTag`BEGIN`);
});

afterEach(async () => {
  await db.execute(sqlTag`ROLLBACK`);
});

export const baseUser = {
  email: 'frog@example.com',
  name: 'Kermit',
} as const;
