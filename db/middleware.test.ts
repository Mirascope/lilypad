import {
  afterAll,
  beforeAll,
  describe,
  expect,
  it,
  mock,
  spyOn,
  type Mock,
} from 'bun:test';
import type { NeonHttpDatabase } from 'drizzle-orm/neon-http';
import type { PostgresJsDatabase } from 'drizzle-orm/postgres-js';
import type { Context } from 'hono';
import { dbMiddleware } from './middleware';

describe('dbMiddleware', () => {
  const mockDb = {} as NeonHttpDatabase | PostgresJsDatabase;
  let createDbConnectionSpy: Mock<typeof import('./utils').createDbConnection>;

  beforeAll(async () => {
    const utils = await import('./utils');

    createDbConnectionSpy = spyOn(utils, 'createDbConnection').mockReturnValue(
      mockDb
    );
  });

  afterAll(() => {
    createDbConnectionSpy.mockRestore();
  });

  it('should set database connection when DATABASE_URL is provided', async () => {
    const mockSet = mock();
    const mockNext = mock();

    const mockContext = {
      env: { DATABASE_URL: 'postgresql://test:test@localhost:5432/testdb' },
      set: mockSet,
    } as unknown as Context;

    await dbMiddleware(mockContext, mockNext);

    expect(createDbConnectionSpy).toHaveBeenCalledWith(
      'postgresql://test:test@localhost:5432/testdb'
    );
    expect(mockSet).toHaveBeenCalledWith('db', mockDb);
    expect(mockNext).toHaveBeenCalled();
  });

  it('should throw error when DATABASE_URL is not provided', async () => {
    const mockNext = mock();

    const mockContext = {
      env: {},
      set: mock(),
    } as unknown as Context;

    await expect(dbMiddleware(mockContext, mockNext)).rejects.toThrow(
      'DATABASE_URL is required'
    );

    expect(mockNext).not.toHaveBeenCalled();
  });

  it('should throw error when env is undefined', async () => {
    const mockNext = mock();

    const mockContext = {
      env: undefined,
      set: mock(),
    } as unknown as Context;

    await expect(dbMiddleware(mockContext, mockNext)).rejects.toThrow(
      'DATABASE_URL is required'
    );

    expect(mockNext).not.toHaveBeenCalled();
  });

  it('should throw error when DATABASE_URL is empty string', async () => {
    const mockNext = mock();

    const mockContext = {
      env: { DATABASE_URL: '' },
      set: mock(),
    } as unknown as Context;

    await expect(dbMiddleware(mockContext, mockNext)).rejects.toThrow(
      'DATABASE_URL is required'
    );

    expect(mockNext).not.toHaveBeenCalled();
  });

  it('should handle different DATABASE_URL formats', async () => {
    const mockSet = mock();
    const mockNext = mock();

    const testUrls = [
      'postgresql://user:pass@neon.tech/db',
      'postgres://user:pass@localhost:5432/mydb',
      'postgresql://user:pass@aws-rds.amazonaws.com:5432/prod',
    ];

    for (const url of testUrls) {
      createDbConnectionSpy.mockClear();
      mockSet.mockClear();
      mockNext.mockClear();

      const mockContext = {
        env: { DATABASE_URL: url },
        set: mockSet,
      } as unknown as Context;

      await dbMiddleware(mockContext, mockNext);

      expect(createDbConnectionSpy).toHaveBeenCalledWith(url);
      expect(mockSet).toHaveBeenCalledWith('db', mockDb);
      expect(mockNext).toHaveBeenCalled();
    }
  });
});
