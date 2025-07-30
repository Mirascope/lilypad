import type { NeonQueryFunction } from '@neondatabase/serverless';
import {
  afterAll,
  beforeAll,
  beforeEach,
  describe,
  expect,
  it,
  spyOn,
  type Mock,
} from 'bun:test';
import type {
  NeonHttpDatabase,
  NeonHttpQueryResult,
} from 'drizzle-orm/neon-http';
import type { PostgresJsDatabase } from 'drizzle-orm/postgres-js';
import type postgres from 'postgres';
import {
  createDbConnection,
  createNeonDbConnection,
  createPostgresDbConnection,
  getDeletedRowCount,
  type Database,
} from './utils';

describe('Database Utilities', () => {
  const mockNeonDb = {} as NeonHttpDatabase & {
    $client: NeonQueryFunction<any, any>;
  };
  const mockPostgresDb = {} as PostgresJsDatabase & {
    $client: postgres.Sql<{}>;
  };
  const mockNeonClient = {} as NeonQueryFunction<boolean, boolean>;
  const mockPostgresClient = {} as postgres.Sql;

  let neonSpy: Mock<typeof import('@neondatabase/serverless').neon>;
  let neonDrizzleSpy: Mock<typeof import('drizzle-orm/neon-http').drizzle>;
  let postgresDrizzleSpy: Mock<
    typeof import('drizzle-orm/postgres-js').drizzle
  >;
  let postgresClientSpy: Mock<typeof import('postgres')>;

  beforeAll(async () => {
    const neonModule = await import('@neondatabase/serverless');
    const neonDrizzle = await import('drizzle-orm/neon-http');
    const postgresDrizzle = await import('drizzle-orm/postgres-js');
    const postgresModule = await import('postgres');

    neonSpy = spyOn(neonModule, 'neon').mockReturnValue(mockNeonClient);
    neonDrizzleSpy = spyOn(neonDrizzle, 'drizzle').mockReturnValue(mockNeonDb);
    postgresDrizzleSpy = spyOn(postgresDrizzle, 'drizzle').mockReturnValue(
      mockPostgresDb
    );
    postgresClientSpy = spyOn(postgresModule, 'default').mockReturnValue(
      mockPostgresClient
    );
  });

  afterAll(() => {
    neonSpy?.mockRestore();
    neonDrizzleSpy?.mockRestore();
    postgresDrizzleSpy?.mockRestore();
    postgresClientSpy?.mockRestore();
  });

  beforeEach(() => {
    neonSpy?.mockClear();
    neonDrizzleSpy?.mockClear();
    postgresDrizzleSpy?.mockClear();
    postgresClientSpy?.mockClear();
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
      const result = getDeletedRowCount({ count: 0 } as postgres.RowList<
        never[]
      >);
      expect(result).toBe(0);
    });

    it('should handle zero rowCount correctly', () => {
      const neonResult = neonResultFromRowCount(0);
      const result = getDeletedRowCount(neonResult);
      expect(result).toBe(0);
    });

    it('should throw error for null result', () => {
      expect(() => getDeletedRowCount(null as any)).toThrow(
        'Unknown result type: object'
      );
    });

    it('should throw error for undefined result', () => {
      expect(() => getDeletedRowCount(undefined as any)).toThrow(
        'Unknown result type: undefined'
      );
    });

    it('should throw error for result without count or rowCount', () => {
      expect(() =>
        getDeletedRowCount({ otherProperty: 'value' } as any)
      ).toThrow('Unknown result type: object');
    });

    it('should throw error for primitive values', () => {
      expect(() => getDeletedRowCount('string' as any)).toThrow(
        'Unknown result type: string'
      );
      expect(() => getDeletedRowCount(123 as any)).toThrow(
        'Unknown result type: number'
      );
      expect(() => getDeletedRowCount(true as any)).toThrow(
        'Unknown result type: boolean'
      );
    });

    it('should throw error when count is not a number', () => {
      expect(() =>
        getDeletedRowCount({ count: 'not-a-number' } as any)
      ).toThrow('Unknown result type: object');
    });

    it('should throw error when rowCount is not a number', () => {
      expect(() =>
        getDeletedRowCount({ rowCount: 'not-a-number' } as any)
      ).toThrow('Unknown result type: object');
    });
  });

  describe('createNeonDbConnection', () => {
    it('should create Neon database connection', () => {
      const databaseUrl = 'postgresql://user:pass@neon.tech/db';
      const connection = createNeonDbConnection(databaseUrl);

      expect(neonSpy).toHaveBeenCalledWith(databaseUrl);
      expect(neonDrizzleSpy).toHaveBeenCalledWith({});
      expect(connection).toBe(mockNeonDb);
    });

    it('should handle different Neon URL formats', () => {
      const urls = [
        'postgresql://user:pass@ep-123.neon.tech/db',
        'postgres://user:pass@ep-456.neon.dev/db',
      ];

      urls.forEach((url) => {
        createNeonDbConnection(url);
      });

      expect(neonSpy).toHaveBeenCalledTimes(2);
      expect(neonSpy).toHaveBeenNthCalledWith(1, urls[0]);
      expect(neonSpy).toHaveBeenNthCalledWith(2, urls[1]);
    });
  });

  describe('createPostgresDbConnection', () => {
    it('should create PostgresJS database connection', () => {
      const databaseUrl = 'postgresql://user:pass@localhost:5432/db';
      const connection = createPostgresDbConnection(databaseUrl);

      expect(postgresClientSpy).toHaveBeenCalledWith(databaseUrl);
      expect(postgresDrizzleSpy).toHaveBeenCalledWith({});
      expect(connection).toBe(mockPostgresDb);
    });

    it('should handle different PostgreSQL URL formats', () => {
      const urls = [
        'postgresql://user:pass@localhost:5432/db',
        'postgres://user:pass@127.0.0.1:5432/db',
        'postgresql://user:pass@remote-host.com:5432/db',
      ];

      urls.forEach((url) => {
        createPostgresDbConnection(url);
      });

      expect(postgresClientSpy).toHaveBeenCalledTimes(3);
      expect(postgresClientSpy).toHaveBeenNthCalledWith(1, urls[0]);
      expect(postgresClientSpy).toHaveBeenNthCalledWith(2, urls[1]);
      expect(postgresClientSpy).toHaveBeenNthCalledWith(3, urls[2]);
    });
  });

  describe('createDbConnection', () => {
    it('should create Neon connection for neon.tech URLs', () => {
      const neonUrl = 'postgresql://user:pass@ep-123.neon.tech/db';
      const connection = createDbConnection(neonUrl);

      expect(neonSpy).toHaveBeenCalledWith(neonUrl);
      expect(neonDrizzleSpy).toHaveBeenCalledWith({});
      expect(connection).toBe(mockNeonDb);
    });

    it('should create Neon connection for neon.dev URLs', () => {
      const neonUrl = 'postgresql://user:pass@ep-456.neon.dev/db';
      const connection = createDbConnection(neonUrl);

      expect(neonSpy).toHaveBeenCalledWith(neonUrl);
      expect(neonDrizzleSpy).toHaveBeenCalledWith({});
      expect(connection).toBe(mockNeonDb);
    });

    it('should create PostgresJS connection for non-Neon URLs', () => {
      const regularUrl = 'postgresql://user:pass@localhost:5432/db';
      const connection = createDbConnection(regularUrl);

      expect(postgresClientSpy).toHaveBeenCalledWith(regularUrl);
      expect(postgresDrizzleSpy).toHaveBeenCalledWith({});
      expect(connection).toBe(mockPostgresDb);
    });

    it('should handle various non-Neon URL formats', () => {
      const nonNeonUrls = [
        'postgresql://user:pass@localhost:5432/db',
        'postgres://user:pass@127.0.0.1:5432/db',
        'postgresql://user:pass@aws-rds.amazonaws.com:5432/db',
        'postgresql://user:pass@supabase.co:5432/db',
        'postgresql://user:pass@railway.app:5432/db',
      ];

      nonNeonUrls.forEach((url) => {
        const connection = createDbConnection(url);
        expect(connection).toBe(mockPostgresDb);
      });

      expect(postgresClientSpy).toHaveBeenCalledTimes(5);
    });

    it('should be case sensitive for Neon detection', () => {
      // Should NOT match (case sensitive)
      const nonMatchingUrls = [
        'postgresql://user:pass@NEON.TECH:5432/db',
        'postgresql://user:pass@Neon.Dev:5432/db',
        'postgresql://user:pass@my-neon-tech.com:5432/db',
      ];

      nonMatchingUrls.forEach((url) => {
        const connection = createDbConnection(url);
        expect(connection).toBe(mockPostgresDb);
      });

      expect(postgresClientSpy).toHaveBeenCalledTimes(3);
    });

    it('should handle edge cases in URL detection', () => {
      // Test URLs that should go to Postgres (don't contain neon.tech or neon.dev)
      const postgresUrls = [
        'postgresql://user:pass@fake-neon-host.com:5432/db',
        'postgresql://user:pass@neon-technology.com:5432/db',
        '',
        'invalid-url',
      ];

      postgresUrls.forEach((url) => {
        const connection = createDbConnection(url);
        expect(connection).toBe(mockPostgresDb);
      });

      // Test URL that should go to Neon (contains neon.dev substring)
      const neonUrl = 'postgresql://user:pass@neon.development:5432/db';
      const neonConnection = createDbConnection(neonUrl);
      expect(neonConnection).toBe(mockNeonDb);

      expect(postgresClientSpy).toHaveBeenCalledTimes(4);
      expect(neonSpy).toHaveBeenCalledTimes(1);
    });
  });

  describe('Type exports', () => {
    it('should export Database type', () => {
      // This test ensures the type is exported and can be used
      const db1: Database = mockNeonDb;
      const db2: Database = mockPostgresDb;

      expect(db1).toBeDefined();
      expect(db2).toBeDefined();
    });
  });
});
