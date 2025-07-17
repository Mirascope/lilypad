import { defineConfig } from 'drizzle-kit';
import * as dotenv from 'dotenv';

dotenv.config({ path: '.env.local' });

console.log(
  '✅ drizzle.config.ts loaded DATABASE_URL:',
  process.env.DATABASE_URL
);

const url = process.env.DATABASE_URL;
if (!url) {
  throw new Error('DATABASE_URL is required for Drizzle config.');
}

export default defineConfig({
  dialect: 'postgresql',
  schema: './db/schema/*',
  out: './db/migrations',
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
});
