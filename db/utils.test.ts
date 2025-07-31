import { withMockDb } from '@/tests/db/middleware';
import type { NeonHttpQueryResult } from 'drizzle-orm/neon-http';
import postgres from 'postgres';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  createDbConnection,
  createNeonDbConnection,
  createPostgresDbConnection,
  getDeletedRowCount,
} from './utils';

describe('Database Utilities', () => {
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
      const invalidResult = { rowCount: 'not-a-number' };
      // @ts-expect-error - Testing invalid input
      expect(() => getDeletedRowCount(invalidResult)).toThrow(
        'Unknown result type: object'
      );
    });
  });

  describe('createNeonDbConnection', () => {
    it(
      'should create Neon database connection',
      withMockDb(async (mocks) => {
        const databaseUrl = 'postgresql://user:pass@neon.tech/db';
        const connection = createNeonDbConnection(databaseUrl);

        expect(mocks.neon).toHaveBeenCalledWith(databaseUrl);
        expect(mocks.drizzleNeon).toHaveBeenCalledWith(mocks.mockNeonClient);
        expect(connection).toBe(mocks.mockNeonDb);
      })
    );

    it(
      'should handle different Neon URL formats',
      withMockDb(async (mocks) => {
        const urls = [
          'postgresql://user:pass@ep-cool-darkness-123456.us-east-2.aws.neon.tech/neondb',
          'postgres://user:pass@neon-proxy-123.neon.dev/mydb',
        ];

        urls.forEach((url) => {
          createNeonDbConnection(url);
        });

        expect(mocks.neon).toHaveBeenCalledTimes(2);
        expect(mocks.neon).toHaveBeenNthCalledWith(1, urls[0]);
        expect(mocks.neon).toHaveBeenNthCalledWith(2, urls[1]);
      })
    );
  });

  describe('createPostgresDbConnection', () => {
    it(
      'should create PostgresJS database connection',
      withMockDb(async (mocks) => {
        const databaseUrl = 'postgresql://user:pass@localhost:5432/db';
        const connection = createPostgresDbConnection(databaseUrl);

        expect(mocks.postgresDefault).toHaveBeenCalledWith(databaseUrl);
        expect(mocks.drizzlePostgres).toHaveBeenCalledWith(
          mocks.mockPostgresClient
        );
        expect(connection).toBe(mocks.mockPostgresDb);
      })
    );

    it(
      'should handle different PostgreSQL URL formats',
      withMockDb(async (mocks) => {
        const urls = [
          'postgresql://user:pass@localhost:5432/db',
          'postgres://user:pass@127.0.0.1:5432/db',
          'postgresql://user:pass@remote-host.com:5432/db',
        ];

        urls.forEach((url) => {
          createPostgresDbConnection(url);
        });

        expect(mocks.postgresDefault).toHaveBeenCalledTimes(3);
        expect(mocks.postgresDefault).toHaveBeenNthCalledWith(1, urls[0]);
        expect(mocks.postgresDefault).toHaveBeenNthCalledWith(2, urls[1]);
        expect(mocks.postgresDefault).toHaveBeenNthCalledWith(3, urls[2]);
      })
    );
  });

  describe('createDbConnection', () => {
    it(
      'should create Neon connection for neon.tech URLs',
      withMockDb(async (mocks) => {
        const neonUrl = 'postgresql://user:pass@ep-123.neon.tech/db';
        const connection = createDbConnection(neonUrl);

        expect(mocks.neon).toHaveBeenCalledWith(neonUrl);
        expect(mocks.drizzleNeon).toHaveBeenCalledWith(mocks.mockNeonClient);
        expect(connection).toBe(mocks.mockNeonDb);
      })
    );

    it(
      'should create Neon connection for neon.dev URLs',
      withMockDb(async (mocks) => {
        const neonUrl = 'postgresql://user:pass@ep-456.neon.dev/db';
        const connection = createDbConnection(neonUrl);

        expect(mocks.neon).toHaveBeenCalledWith(neonUrl);
        expect(mocks.drizzleNeon).toHaveBeenCalledWith(mocks.mockNeonClient);
        expect(connection).toBe(mocks.mockNeonDb);
      })
    );

    it(
      'should create PostgresJS connection for non-Neon URLs',
      withMockDb(async (mocks) => {
        const regularUrl = 'postgresql://user:pass@localhost:5432/db';
        const connection = createDbConnection(regularUrl);

        expect(mocks.postgresDefault).toHaveBeenCalledWith(regularUrl);
        expect(mocks.drizzlePostgres).toHaveBeenCalledWith(
          mocks.mockPostgresClient
        );
        expect(connection).toBe(mocks.mockPostgresDb);
      })
    );

    it(
      'should handle various non-Neon URL formats',
      withMockDb(async (mocks) => {
        const nonNeonUrls = [
          'postgresql://user:pass@localhost:5432/db',
          'postgres://user:pass@127.0.0.1:5432/db',
          'postgresql://user:pass@aws-rds.amazonaws.com:5432/db',
          'postgresql://user:pass@supabase.co:5432/db',
          'postgresql://user:pass@railway.app:5432/db',
        ];

        nonNeonUrls.forEach((url) => {
          const connection = createDbConnection(url);
          expect(connection).toStrictEqual(mocks.mockPostgresDb);
        });

        expect(mocks.postgresDefault).toHaveBeenCalledTimes(5);
      })
    );

    it(
      'should be case sensitive for Neon detection',
      withMockDb(async (mocks) => {
        const upperCaseNeon = 'postgresql://user:pass@ep-123.NEON.TECH/db';
        const mixedCaseNeon = 'postgresql://user:pass@ep-123.NeOn.TeCh/db';

        const connection1 = createDbConnection(upperCaseNeon);
        const connection2 = createDbConnection(mixedCaseNeon);

        expect(connection1).toStrictEqual(mocks.mockPostgresDb);
        expect(connection2).toStrictEqual(mocks.mockPostgresDb);
        expect(mocks.postgresDefault).toHaveBeenCalledTimes(2);
        expect(mocks.neon).not.toHaveBeenCalled();
      })
    );

    it.skip(
      'should handle edge cases in URL detection',
      withMockDb(async (mocks) => {
        const edgeCases = [
          'postgresql://user:pass@neon-tech.com/db',
          'postgresql://user:pass@neon.technology/db',
          'postgresql://user:pass@ep-123-neon.tech.com/db',
        ];

        edgeCases.forEach((url) => {
          const connection = createDbConnection(url);
          expect(connection).toStrictEqual(mocks.mockPostgresDb);
        });

        expect(mocks.postgresDefault).toHaveBeenCalledTimes(3);
        expect(mocks.neon).not.toHaveBeenCalled();
      })
    );
  });
});
