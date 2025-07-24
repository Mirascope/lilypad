import { neon } from '@neondatabase/serverless';
import {
  drizzle as drizzleNeon,
  type NeonHttpDatabase,
  type NeonHttpQueryResult,
} from 'drizzle-orm/neon-http';
import {
  drizzle as drizzlePostgres,
  type PostgresJsDatabase,
} from 'drizzle-orm/postgres-js';
import postgres from 'postgres';

export type Database = PostgresJsDatabase | NeonHttpDatabase;

export function getDeletedRowCount(
  result: NeonHttpQueryResult<never> | postgres.RowList<never[]>
): number {
  if (typeof result === 'object' && result !== null) {
    // PostgresJS returns { count: number }
    if ('count' in result && typeof result.count === 'number') {
      return result.count;
    }
    // Neon HTTP may return { rowCount: number } or similar
    if ('rowCount' in result && typeof result.rowCount === 'number') {
      return result.rowCount;
    }
  }
  return 0;
}

export function createDbConnection(databaseUrl: string): Database {
  if (databaseUrl.includes('neon.tech') || databaseUrl.includes('neon.dev')) {
    const sql = neon(databaseUrl);
    return drizzleNeon(sql);
  }
  const queryClient = postgres(databaseUrl);
  return drizzlePostgres(queryClient);
}
