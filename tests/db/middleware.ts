import type { NeonQueryFunction } from '@neondatabase/serverless';
import type { NeonHttpDatabase } from 'drizzle-orm/neon-http';
import type { PostgresJsDatabase } from 'drizzle-orm/postgres-js';
import type postgres from 'postgres';
import { vi } from 'vitest';

export type DbMocks = {
  neon: typeof import('@neondatabase/serverless').neon;
  mockNeonClient: NeonQueryFunction<boolean, boolean>;
  mockNeonDb: NeonHttpDatabase & {
    $client: NeonQueryFunction<any, any>;
  };
  drizzleNeon: typeof import('drizzle-orm/neon-http').drizzle;
  postgresDefault: typeof postgres;
  mockPostgresClient: postgres.Sql;
  mockPostgresDb: PostgresJsDatabase & {
    $client: postgres.Sql<{}>;
  };
  drizzlePostgres: typeof import('drizzle-orm/postgres-js').drizzle;
};

export const withMockDb = (testFn: (mocks: DbMocks) => Promise<void>) => {
  return async () => {
    vi.mock('@neondatabase/serverless');
    vi.mock('drizzle-orm/neon-http');
    vi.mock('drizzle-orm/postgres-js');
    vi.mock('postgres');

    const { neon } = await import('@neondatabase/serverless');
    const { drizzle: drizzleNeon } = await import('drizzle-orm/neon-http');
    const postgresDefault = (await import('postgres')).default;
    const { drizzle: drizzlePostgres } = await import(
      'drizzle-orm/postgres-js'
    );

    const mockNeonClient = {} as NeonQueryFunction<boolean, boolean>;
    vi.mocked(neon).mockClear();
    vi.mocked(neon).mockReturnValue(mockNeonClient);

    const mockNeonDb = {} as NeonHttpDatabase & {
      $client: NeonQueryFunction<any, any>;
    };
    vi.mocked(drizzleNeon).mockClear();
    vi.mocked(drizzleNeon).mockReturnValue(mockNeonDb);

    const mockPostgresClient = {} as postgres.Sql;
    vi.mocked(postgresDefault).mockClear();
    vi.mocked(postgresDefault).mockReturnValue(mockPostgresClient);

    const mockPostgresDb = {} as PostgresJsDatabase & {
      $client: postgres.Sql<{}>;
    };
    vi.mocked(drizzlePostgres).mockClear();
    vi.mocked(drizzlePostgres).mockReturnValue(mockPostgresDb);

    const mocks: DbMocks = {
      neon,
      mockNeonClient,
      mockNeonDb,
      drizzleNeon,
      postgresDefault,
      mockPostgresClient,
      mockPostgresDb,
      drizzlePostgres,
    };

    try {
      await testFn(mocks);
    } finally {
      vi.mocked(neon).mockClear();
      vi.mocked(drizzleNeon).mockClear();
      vi.mocked(postgresDefault).mockClear();
      vi.mocked(drizzlePostgres).mockClear();
    }
  };
};
