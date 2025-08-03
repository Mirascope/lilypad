import * as dotenv from 'dotenv';
import { drizzle } from 'drizzle-orm/postgres-js';
import { migrate } from 'drizzle-orm/postgres-js/migrator';
import postgres from 'postgres';

export default async function globalSetup() {
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
  const db = drizzle(sql);

  await migrate(db, { migrationsFolder: 'db/migrations' });

  await sql.end();
}
