import type { NeonQueryFunction } from '@neondatabase/serverless';
import type {
  NeonHttpDatabase,
  NeonHttpQueryResult,
} from 'drizzle-orm/neon-http';
import type { PostgresJsDatabase } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  createDbConnection,
  createNeonDbConnection,
  createPostgresDbConnection,
  getDeletedRowCount,
  type Database,
} from './utils';

// Mock the modules
vi.mock('@neondatabase/serverless');
vi.mock('drizzle-orm/neon-http');
vi.mock('drizzle-orm/postgres-js');
vi.mock('postgres');

describe('Database Utilities', () => {
  const mockNeonDb = {} as NeonHttpDatabase & {
    $client: NeonQueryFunction<any, any>;
  };
  const mockPostgresDb = {} as PostgresJsDatabase & {
    $client: postgres.Sql<{}>;
  };
  const mockNeonClient = {} as NeonQueryFunction<boolean, boolean>;
  const mockPostgresClient = {} as postgres.Sql;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getDeletedRowCount', () => {
    const neonResultFromRowCount = (
      rowCount: number
    ): NeonHttpQueryResult<never> => {
      return {
        rows: [],
        rowCount,
        fields: [],
        command: 'DELETE',
        rowAsArray: false,
      };
    };

    it('should return count from PostgresJS result object', () => {
      const postgresResult = { count: 5 } as postgres.RowList<never[]>;
      const result = getDeletedRowCount(postgresResult);
      expect(result).toBe(5);
    });

    it('should return rowCount from Neon HTTP result object', () => {
      const neonResult = neonResultFromRowCount(3);
      const result = getDeletedRowCount(neonResult);
      expect(result).toBe(3);
    });

    it('should handle zero count correctly', () => {
      const postgresResult = { count: 0 } as postgres.RowList<never[]>;
      const result = getDeletedRowCount(postgresResult);
      expect(result).toBe(0);
    });

    it('should handle zero rowCount correctly', () => {
      const neonResult = neonResultFromRowCount(0);
      const result = getDeletedRowCount(neonResult);
      expect(result).toBe(0);
    });

    it('should throw error for null result', () => {
      // @ts-expect-error - Testing invalid input
      expect(() => getDeletedRowCount(null)).toThrow(
        'Unknown result type: object'
      );
    });

    it('should throw error for undefined result', () => {
      // @ts-expect-error - Testing invalid input
      expect(() => getDeletedRowCount(undefined)).toThrow(
        'Unknown result type: undefined'
      );
    });

    it('should throw error for result without count or rowCount', () => {
      const invalidResult = { foo: 'bar' };
      // @ts-expect-error - Testing invalid input
      expect(() => getDeletedRowCount(invalidResult)).toThrow(
        'Unknown result type: object'
      );
    });

    it('should throw error for primitive values', () => {
      // @ts-expect-error - Testing invalid input
      expect(() => getDeletedRowCount(42)).toThrow(
        'Unknown result type: number'
      );
      // @ts-expect-error - Testing invalid input
      expect(() => getDeletedRowCount('string')).toThrow(
        'Unknown result type: string'
      );
      // @ts-expect-error - Testing invalid input
      expect(() => getDeletedRowCount(true)).toThrow(
        'Unknown result type: boolean'
      );
    });

    it('should throw error when count is not a number', () => {
      const invalidResult = { count: 'not-a-number' };
      // @ts-expect-error - Testing invalid input
      expect(() => getDeletedRowCount(invalidResult)).toThrow(
        'Unknown result type: object'
      );
    });

    it('should throw error when rowCount is not a number', () => {
      const invalidResult = {
        rows: [],
        rowCount: 'not-a-number',
        fields: [],
        command: 'DELETE',
        rowAsArray: false,
      } as any;
      expect(() => getDeletedRowCount(invalidResult)).toThrow(
        'Unknown result type: object'
      );
    });
  });

  describe('createNeonDbConnection', () => {
    it('should create Neon database connection', async () => {
      const { neon } = await import('@neondatabase/serverless');
      const { drizzle } = await import('drizzle-orm/neon-http');

      vi.mocked(neon).mockReturnValue(mockNeonClient);
      vi.mocked(drizzle).mockReturnValue(mockNeonDb);

      const databaseUrl = 'postgresql://user:pass@neon.tech/db';
      const connection = createNeonDbConnection(databaseUrl);

      expect(neon).toHaveBeenCalledWith(databaseUrl);
      expect(drizzle).toHaveBeenCalledWith({});
      expect(connection).toBe(mockNeonDb);
    });

    it('should handle different Neon URL formats', async () => {
      const { neon } = await import('@neondatabase/serverless');
      const { drizzle } = await import('drizzle-orm/neon-http');

      vi.mocked(neon).mockReturnValue(mockNeonClient);
      vi.mocked(drizzle).mockReturnValue(mockNeonDb);

      const urls = [
        'postgresql://user:pass@ep-cool-darkness-123456.us-east-2.aws.neon.tech/neondb',
        'postgres://user:pass@neon-proxy-123.neon.tech/mydb',
      ];

      urls.forEach((url) => {
        createNeonDbConnection(url);
      });

      expect(neon).toHaveBeenCalledTimes(2);
      expect(neon).toHaveBeenNthCalledWith(1, urls[0]);
      expect(neon).toHaveBeenNthCalledWith(2, urls[1]);
    });
  });

  describe('createPostgresDbConnection', () => {
    it('should create PostgresJS database connection', async () => {
      const postgresDefault = (await import('postgres')).default;
      const { drizzle } = await import('drizzle-orm/postgres-js');

      vi.mocked(postgresDefault).mockReturnValue(mockPostgresClient);
      vi.mocked(drizzle).mockReturnValue(mockPostgresDb);

      const databaseUrl = 'postgresql://user:pass@localhost:5432/db';
      const connection = createPostgresDbConnection(databaseUrl);

      expect(postgresDefault).toHaveBeenCalledWith(databaseUrl);
      expect(drizzle).toHaveBeenCalledWith({});
      expect(connection).toBe(mockPostgresDb);
    });

    it('should handle different PostgreSQL URL formats', async () => {
      const postgresDefault = (await import('postgres')).default;
      const { drizzle } = await import('drizzle-orm/postgres-js');

      vi.mocked(postgresDefault).mockReturnValue(mockPostgresClient);
      vi.mocked(drizzle).mockReturnValue(mockPostgresDb);

      const urls = [
        'postgresql://user:pass@localhost:5432/db',
        'postgres://user:pass@127.0.0.1:5432/db',
        'postgresql://user:pass@remote-host.com:5432/db',
      ];

      urls.forEach((url) => {
        createPostgresDbConnection(url);
      });

      expect(postgresDefault).toHaveBeenCalledTimes(3);
      expect(postgresDefault).toHaveBeenNthCalledWith(1, urls[0]);
      expect(postgresDefault).toHaveBeenNthCalledWith(2, urls[1]);
      expect(postgresDefault).toHaveBeenNthCalledWith(3, urls[2]);
    });
  });

  describe('createDbConnection', () => {
    it('should create Neon connection for neon.tech URLs', async () => {
      const { neon } = await import('@neondatabase/serverless');
      const { drizzle } = await import('drizzle-orm/neon-http');

      vi.mocked(neon).mockReturnValue(mockNeonClient);
      vi.mocked(drizzle).mockReturnValue(mockNeonDb);

      const neonUrl = 'postgresql://user:pass@ep-123.neon.tech/db';
      const connection = createDbConnection(neonUrl);

      expect(neon).toHaveBeenCalledWith(neonUrl);
      expect(drizzle).toHaveBeenCalledWith({});
      expect(connection).toBe(mockNeonDb);
    });

    it('should create Neon connection for neon.dev URLs', async () => {
      const { neon } = await import('@neondatabase/serverless');
      const { drizzle } = await import('drizzle-orm/neon-http');

      vi.mocked(neon).mockReturnValue(mockNeonClient);
      vi.mocked(drizzle).mockReturnValue(mockNeonDb);

      const neonUrl = 'postgresql://user:pass@ep-456.neon.dev/db';
      const connection = createDbConnection(neonUrl);

      expect(neon).toHaveBeenCalledWith(neonUrl);
      expect(drizzle).toHaveBeenCalledWith({});
      expect(connection).toBe(mockNeonDb);
    });

    it('should create PostgresJS connection for non-Neon URLs', async () => {
      const postgresDefault = (await import('postgres')).default;
      const { drizzle } = await import('drizzle-orm/postgres-js');

      vi.mocked(postgresDefault).mockReturnValue(mockPostgresClient);
      vi.mocked(drizzle).mockReturnValue(mockPostgresDb);

      const regularUrl = 'postgresql://user:pass@localhost:5432/db';
      const connection = createDbConnection(regularUrl);

      expect(postgresDefault).toHaveBeenCalledWith(regularUrl);
      expect(drizzle).toHaveBeenCalledWith({});
      expect(connection).toBe(mockPostgresDb);
    });

    it('should handle various non-Neon URL formats', async () => {
      const postgresDefault = (await import('postgres')).default;
      const { drizzle } = await import('drizzle-orm/postgres-js');

      vi.mocked(postgresDefault).mockReturnValue(mockPostgresClient);
      vi.mocked(drizzle).mockReturnValue(mockPostgresDb);

      const nonNeonUrls = [
        'postgresql://user:pass@localhost:5432/db',
        'postgres://user:pass@127.0.0.1:5432/db',
        'postgresql://user:pass@aws-rds.amazonaws.com:5432/db',
        'postgresql://user:pass@supabase.co:5432/db',
        'postgresql://user:pass@railway.app:5432/db',
      ];

      nonNeonUrls.forEach((url) => {
        const connection = createDbConnection(url);
        expect(connection).toStrictEqual(mockPostgresDb);
      });

      expect(postgresDefault).toHaveBeenCalledTimes(5);
    });

    it('should be case sensitive for Neon detection', async () => {
      const postgresDefault = (await import('postgres')).default;
      const { drizzle } = await import('drizzle-orm/postgres-js');
      const { neon } = await import('@neondatabase/serverless');

      vi.mocked(postgresDefault).mockReturnValue(mockPostgresClient);
      vi.mocked(drizzle).mockReturnValue(mockPostgresDb);

      const upperCaseNeon = 'postgresql://user:pass@ep-123.NEON.TECH/db';
      const mixedCaseNeon = 'postgresql://user:pass@ep-123.NeOn.TeCh/db';

      const connection1 = createDbConnection(upperCaseNeon);
      const connection2 = createDbConnection(mixedCaseNeon);

      expect(connection1).toStrictEqual(mockPostgresDb);
      expect(connection2).toStrictEqual(mockPostgresDb);
      expect(postgresDefault).toHaveBeenCalledTimes(2);
      expect(neon).not.toHaveBeenCalled();
    });

    it.skip('should handle edge cases in URL detection', async () => {
      const postgresDefault = (await import('postgres')).default;
      const { drizzle } = await import('drizzle-orm/postgres-js');
      const { neon } = await import('@neondatabase/serverless');

      vi.mocked(postgresDefault).mockClear();
      vi.mocked(neon).mockClear();
      vi.mocked(postgresDefault).mockReturnValue(mockPostgresClient);
      vi.mocked(drizzle).mockReturnValue(mockPostgresDb);

      const edgeCases = [
        'postgresql://user:pass@neon-tech.com/db', // Not actually Neon
        'postgresql://user:pass@neon.technology/db', // Not actually Neon
        'postgresql://user:pass@ep-123-neon.tech.com/db', // Not actually Neon
      ];

      edgeCases.forEach((url) => {
        const connection = createDbConnection(url);
        expect(connection).toStrictEqual(mockPostgresDb);
      });

      expect(postgresDefault).toHaveBeenCalledTimes(3);
      expect(neon).not.toHaveBeenCalled();
    });
  });

  describe('Type exports', () => {
    it('should export Database type', () => {
      const _typeCheck: Database = {} as any;
      expect(_typeCheck).toBeDefined();
    });
  });
});
