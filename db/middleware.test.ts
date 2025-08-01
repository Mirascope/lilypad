import type { NeonHttpDatabase } from 'drizzle-orm/neon-http';
import type { PostgresJsDatabase } from 'drizzle-orm/postgres-js';
import type { Context } from 'hono';
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest';
import { dbMiddleware } from './middleware';

// Mock the utils module before any imports
vi.mock('./utils', async () => {
  const actual = await vi.importActual('./utils');
  return {
    ...actual,
    createDbConnection: vi.fn(
      () => ({}) as NeonHttpDatabase | PostgresJsDatabase
    ),
  };
});

describe('dbMiddleware', () => {
  let createDbConnectionMock: any;
  const mockDb = {} as NeonHttpDatabase | PostgresJsDatabase;

  beforeAll(async () => {
    const utils = await import('./utils');
    createDbConnectionMock = utils.createDbConnection as any;
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should set database connection when DATABASE_URL is provided', async () => {
    const mockSet = vi.fn();
    const mockNext = vi.fn();

    const mockContext = {
      env: { DATABASE_URL: 'postgresql://test:test@localhost:5432/testdb' },
      set: mockSet,
    } as unknown as Context;

    await dbMiddleware(mockContext, mockNext);

    expect(createDbConnectionMock).toHaveBeenCalledWith(
      'postgresql://test:test@localhost:5432/testdb'
    );
    expect(mockSet).toHaveBeenCalledWith('db', mockDb);
    expect(mockNext).toHaveBeenCalled();
  });

  it('should throw error when DATABASE_URL is not provided', async () => {
    const mockNext = vi.fn();

    const mockContext = {
      env: {},
      set: vi.fn(),
    } as unknown as Context;

    await expect(dbMiddleware(mockContext, mockNext)).rejects.toThrow(
      'DATABASE_URL is required'
    );

    expect(mockNext).not.toHaveBeenCalled();
  });

  it('should throw error when env is undefined', async () => {
    const mockNext = vi.fn();

    const mockContext = {
      env: undefined,
      set: vi.fn(),
    } as unknown as Context;

    await expect(dbMiddleware(mockContext, mockNext)).rejects.toThrow(
      'DATABASE_URL is required'
    );

    expect(mockNext).not.toHaveBeenCalled();
  });

  it('should throw error when DATABASE_URL is empty string', async () => {
    const mockNext = vi.fn();

    const mockContext = {
      env: { DATABASE_URL: '' },
      set: vi.fn(),
    } as unknown as Context;

    await expect(dbMiddleware(mockContext, mockNext)).rejects.toThrow(
      'DATABASE_URL is required'
    );

    expect(mockNext).not.toHaveBeenCalled();
  });

  it('should handle different DATABASE_URL formats', async () => {
    const mockSet = vi.fn();
    const mockNext = vi.fn();

    const testUrls = [
      'postgresql://user:pass@neon.tech/db',
      'postgres://user:pass@localhost:5432/mydb',
      'postgresql://user:pass@aws-rds.amazonaws.com:5432/prod',
    ];

    for (const url of testUrls) {
      createDbConnectionMock.mockClear();
      mockSet.mockClear();
      mockNext.mockClear();

      const mockContext = {
        env: { DATABASE_URL: url },
        set: mockSet,
      } as unknown as Context;

      await dbMiddleware(mockContext, mockNext);

      expect(createDbConnectionMock).toHaveBeenCalledWith(url);
      expect(mockSet).toHaveBeenCalledWith('db', {});
      expect(mockNext).toHaveBeenCalled();
    }
  });
});
