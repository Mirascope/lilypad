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
    if ('count' in result && typeof result.count === 'number') {
      return result.count;
    }
    if ('rowCount' in result && typeof result.rowCount === 'number') {
      return result.rowCount;
    }
  }
  throw new Error(`Unknown result type: ${typeof result}`);
}

export function createNeonDbConnection(databaseUrl: string): NeonHttpDatabase {
  const sql = neon(databaseUrl);
  return drizzleNeon(sql);
}

export function createPostgresDbConnection(
  databaseUrl: string
): PostgresJsDatabase {
  const queryClient = postgres(databaseUrl);
  return drizzlePostgres(queryClient);
}

export function createDbConnection(databaseUrl: string): Database {
  if (databaseUrl.includes('neon.tech') || databaseUrl.includes('neon.dev')) {
    return createNeonDbConnection(databaseUrl);
  }
  return createPostgresDbConnection(databaseUrl);
}
