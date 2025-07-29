import { afterAll, afterEach, beforeAll, beforeEach } from 'bun:test';
import * as dotenv from 'dotenv';
import { sql as sqlTag } from 'drizzle-orm';
import { drizzle } from 'drizzle-orm/postgres-js';
import { migrate } from 'drizzle-orm/postgres-js/migrator';
import postgres from 'postgres';

dotenv.config({ path: '.env.local' });

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

beforeAll(async () => {
  await migrate(db, { migrationsFolder: 'db/migrations' });
});

beforeEach(async () => {
  await db.execute(sqlTag`BEGIN`);
});

afterEach(async () => {
  await db.execute(sqlTag`ROLLBACK`);
});

afterAll(async () => {
  await sql.end();
});

export const baseUser = {
  email: 'frog@example.com',
  name: 'Kermit',
} as const;
