import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';

export function createDbConnection(databaseUrl: string) {
  const queryClient = postgres(databaseUrl);
  return drizzle(queryClient);
}
