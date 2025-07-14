import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createVersionedFunction, isVersionedFunction } from './versioned-function';
import { getSettings } from '../utils/settings';
import { getPooledClient } from '../utils/client-pool';

vi.mock('../utils/settings');
vi.mock('../utils/client-pool');
vi.mock('../utils/logger', () => ({
  logger: {
    info: vi.fn(),
    debug: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}));

// Create a mock for the sandbox module
let mockExecuteFn = vi.fn();

vi.mock('./sandbox', () => ({
  createSandbox: () => ({
    execute: mockExecuteFn,
  }),
}));

describe('versioned-function', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset the mock function for each test
    mockExecuteFn = vi.fn().mockResolvedValue({
      result: 'default mock result',
      logs: [],
      executionTime: 100,
    });
  });

  describe('createVersionedFunction', () => {
    it('should create a versioned function with all methods', () => {
      const mockFn = vi.fn((x: number) => x * 2);
      const versionedFn = createVersionedFunction(
        mockFn,
        'testFunction',
        'test-project',
        'test-uuid',
      );

      expect(typeof versionedFn).toBe('function');
      expect(typeof versionedFn.version).toBe('function');
      expect(typeof versionedFn.remote).toBe('function');
      expect(typeof versionedFn.versions).toBe('function');
      expect(typeof versionedFn.deploy).toBe('function');
    });

    it('should preserve function properties', () => {
      const mockFn = vi.fn(function namedFunction(x: number, y: number) {
        return x + y;
      });
      const versionedFn = createVersionedFunction(
        mockFn,
        'testFunction',
        'test-project',
        'test-uuid',
      );

      expect(versionedFn.name).toBe('namedFunction');
      expect(versionedFn.length).toBe(2);
    });

    it('should execute the original function when called directly', () => {
      const mockFn = vi.fn((x: number) => x * 2);
      const versionedFn = createVersionedFunction(
        mockFn,
        'testFunction',
        'test-project',
        'test-uuid',
      );

      const result = versionedFn(5);
      expect(result).toBe(10);
      expect(mockFn).toHaveBeenCalledWith(5);
    });

    it('should create versioned function even when SDK not configured', () => {
      vi.mocked(getSettings).mockReturnValue(null);

      const mockFn = vi.fn((x: number) => x * 2);
      const versionedFn = createVersionedFunction(
        mockFn,
        'testFunction',
        'test-project',
        'test-uuid',
      );

      // Should still have versioning methods
      expect(typeof versionedFn).toBe('function');
      expect(typeof versionedFn.version).toBe('function');
      expect(typeof versionedFn.remote).toBe('function');
      expect(typeof versionedFn.versions).toBe('function');
      expect(typeof versionedFn.deploy).toBe('function');

      // Should execute the original function
      const result = versionedFn(5);
      expect(result).toBe(10);
      expect(mockFn).toHaveBeenCalledWith(5);
    });

    describe('version method', () => {
      it('should execute specific version in sandbox', async () => {
        const mockVersions = [
          { version: 1, uuid: 'v1-uuid', created_at: '2024-01-01', is_deployed: false },
          { version: 2, uuid: 'v2-uuid', created_at: '2024-01-02', is_deployed: false },
        ];
        
        const mockClient = {
          projects: {
            functions: {
              get: vi.fn()
                .mockResolvedValueOnce({ name: 'testFunction' })
                .mockResolvedValueOnce({ 
                  code: 'function testFunction(x) { return x * 3; }',
                  dependencies: { lodash: '4.17.21' }
                }),
              getByName: vi.fn().mockResolvedValue(mockVersions),
            },
          },
        };
        
        vi.mocked(getPooledClient).mockReturnValue(mockClient as any);
        vi.mocked(getSettings).mockReturnValue({
          apiKey: 'test-key',
          projectId: 'test-project',
          baseUrl: 'http://test.com',
        });

        // Create an async function properly
        const mockFn = vi.fn().mockImplementation(async (x: number) => x * 2);
        // Mark it as async for detection
        mockFn.toString = () => 'async (x) => x * 2';
        
        const versionedFn = createVersionedFunction(
          mockFn,
          'testFunction',
          'test-project',
          'test-uuid',
        );

        // Setup mock for this specific test
        mockExecuteFn.mockResolvedValueOnce({
          result: 15, // 5 * 3 from version 1
          logs: ['[log] Executing version 1'],
          executionTime: 50,
        });

        const v1 = versionedFn.version(1);
        const result = await v1(5);

        expect(result).toBe(15);
        expect(mockExecuteFn).toHaveBeenCalledWith(
          'function testFunction(x) { return x * 3; }',
          [5],
          {
            timeout: 30000,
            memoryLimit: 128,
            dependencies: { lodash: '4.17.21' },
          }
        );
      });

      it('should fall back to current version if version not found', async () => {
        vi.mocked(getPooledClient).mockReturnValue({
          projects: {
            functions: {
              get: vi.fn().mockResolvedValue({ name: 'testFunction' }),
              getByName: vi.fn().mockResolvedValue([]),
            },
          },
        } as any);
        
        vi.mocked(getSettings).mockReturnValue({
          apiKey: 'test-key',
          projectId: 'test-project',
          baseUrl: 'http://test.com',
        });

        const mockFn = vi.fn().mockImplementation(async (x: number) => x * 2);
        mockFn.toString = () => 'async (x) => x * 2';
        
        const versionedFn = createVersionedFunction(
          mockFn,
          'testFunction',
          'test-project',
          'test-uuid',
        );

        const v3 = versionedFn.version(3);
        const result = await v3(5);

        expect(result).toBe(10);
        expect(mockFn).toHaveBeenCalledWith(5);
      });

      it('should throw error for sync functions requesting version execution', () => {
        const mockFn = vi.fn((x: number) => x * 2); // Sync function
        const versionedFn = createVersionedFunction(
          mockFn,
          'testFunction',
          'test-project',
          'test-uuid',
        );

        const v1 = versionedFn.version(1);
        
        expect(() => v1(5)).toThrow(
          'Version execution requires async operation'
        );
      });
    });

    describe('remote method', () => {
      it('should execute deployed function in sandbox', async () => {
        const mockClient = {
          projects: {
            functions: {
              get: vi.fn().mockResolvedValue({
                code: 'function deployed(x) { return x * 4; }',
                dependencies: { axios: '1.0.0' },
              }),
            },
          },
        };
        
        vi.mocked(getPooledClient).mockReturnValue(mockClient as any);
        vi.mocked(getSettings).mockReturnValue({
          apiKey: 'test-key',
          projectId: 'test-project',
          baseUrl: 'http://test.com',
        });

        const mockFn = vi.fn((x: number) => x * 2);
        const versionedFn = createVersionedFunction(
          mockFn,
          'testFunction',
          'test-project',
          'test-uuid',
        );

        // Setup mock for this specific test
        mockExecuteFn.mockResolvedValueOnce({
          result: 20, // 5 * 4 from deployed version
          logs: ['[log] Remote execution'],
          executionTime: 75,
        });

        const result = await versionedFn.remote(5);

        expect(result).toBe(20);
        expect(mockExecuteFn).toHaveBeenCalledWith(
          'function deployed(x) { return x * 4; }',
          [5],
          {
            timeout: 30000,
            memoryLimit: 128,
            dependencies: { axios: '1.0.0' },
          }
        );
      });

      it('should use bundled code if available', async () => {
        // Mock file system to return bundle
        vi.doMock('node:fs/promises', () => ({
          default: {
            readFile: vi.fn().mockResolvedValue('// Bundled code\nfunction bundled(x) { return x * 5; }'),
          },
          readFile: vi.fn().mockResolvedValue('// Bundled code\nfunction bundled(x) { return x * 5; }'),
        }));

        const mockClient = {
          projects: {
            functions: {
              get: vi.fn().mockResolvedValue({
                code: 'function deployed(x) { return x * 4; }',
                dependencies: {},
              }),
            },
          },
        };
        
        vi.mocked(getPooledClient).mockReturnValue(mockClient as any);
        vi.mocked(getSettings).mockReturnValue({
          apiKey: 'test-key',
          projectId: 'test-project',
          baseUrl: 'http://test.com',
        });

        const mockFn = vi.fn((x: number) => x * 2);
        const versionedFn = createVersionedFunction(
          mockFn,
          'testFunction',
          'test-project',
          'test-uuid',
        );

        // Setup mock for this specific test
        mockExecuteFn.mockResolvedValueOnce({
          result: 25, // 5 * 5 from bundled version
          logs: [],
          executionTime: 50,
        });

        const result = await versionedFn.remote(5);

        expect(result).toBe(25);
        expect(mockExecuteFn).toHaveBeenCalledWith(
          '// Bundled code\nfunction bundled(x) { return x * 5; }',
          [5],
          expect.any(Object)
        );
      });

      it('should fall back to local execution on error', async () => {
        const mockClient = {
          projects: {
            functions: {
              get: vi.fn().mockRejectedValue(new Error('API Error')),
            },
          },
        };
        
        vi.mocked(getPooledClient).mockReturnValue(mockClient as any);
        vi.mocked(getSettings).mockReturnValue({
          apiKey: 'test-key',
          projectId: 'test-project',
          baseUrl: 'http://test.com',
        });

        const mockFn = vi.fn((x: number) => x * 2);
        const versionedFn = createVersionedFunction(
          mockFn,
          'testFunction',
          'test-project',
          'test-uuid',
        );

        const result = await versionedFn.remote(5);

        expect(result).toBe(10); // Local execution result
        expect(mockFn).toHaveBeenCalledWith(5);
      });

      it('should fall back to local when SDK not configured', async () => {
        vi.mocked(getSettings).mockReturnValue(null);

        const mockFn = vi.fn((x: number) => x * 2);
        const versionedFn = createVersionedFunction(
          mockFn,
          'testFunction',
          'test-project',
          'test-uuid',
        );

        const result = await versionedFn.remote(5);
        expect(result).toBe(10);
        expect(mockFn).toHaveBeenCalledWith(5);
      });
    });

    describe('versions method', () => {
      it('should fetch all versions of the function', async () => {
        const mockVersions = [
          { uuid: 'v1-uuid', version_num: 1, created_at: '2024-01-01' },
          { uuid: 'v2-uuid', version_num: 2, created_at: '2024-01-02' },
        ];
        const mockClient = {
          projects: {
            functions: {
              get: vi.fn().mockResolvedValue({ name: 'testFunction' }),
              getByName: vi.fn().mockResolvedValue(mockVersions),
            },
          },
        };
        vi.mocked(getPooledClient).mockReturnValue(mockClient as any);
        vi.mocked(getSettings).mockReturnValue({
          apiKey: 'test-key',
          projectId: 'test-project',
          baseUrl: 'http://test.com',
        });

        const mockFn = vi.fn();
        const versionedFn = createVersionedFunction(
          mockFn,
          'testFunction',
          'test-project',
          'test-uuid',
        );

        const versions = await versionedFn.versions();

        expect(versions).toHaveLength(2);
        expect(versions[0]).toEqual({
          version: 1,
          uuid: 'v1-uuid',
          created_at: '2024-01-01',
          is_deployed: false,
        });
        expect(mockClient.projects.functions.getByName).toHaveBeenCalledWith(
          'test-project',
          'testFunction',
        );
      });

      it('should return empty array when settings not available', async () => {
        vi.mocked(getSettings).mockReturnValue(null);

        const mockFn = vi.fn();
        const versionedFn = createVersionedFunction(
          mockFn,
          'testFunction',
          'test-project',
          'test-uuid',
        );

        const versions = await versionedFn.versions();
        expect(versions).toEqual([]);
      });

      it('should handle errors gracefully', async () => {
        const mockClient = {
          projects: {
            functions: {
              getByName: vi.fn().mockRejectedValue(new Error('API Error')),
            },
          },
        };
        vi.mocked(getPooledClient).mockReturnValue(mockClient as any);
        vi.mocked(getSettings).mockReturnValue({
          apiKey: 'test-key',
          projectId: 'test-project',
          baseUrl: 'http://test.com',
        });

        const mockFn = vi.fn();
        const versionedFn = createVersionedFunction(
          mockFn,
          'testFunction',
          'test-project',
          'test-uuid',
        );

        const versions = await versionedFn.versions();
        expect(versions).toEqual([]);
      });
    });

    describe('deploy method', () => {
      it('should log deployment message', async () => {
        vi.mocked(getSettings).mockReturnValue({
          apiKey: 'test-key',
          projectId: 'test-project',
          baseUrl: 'http://test.com',
        });

        const mockFn = vi.fn();
        const versionedFn = createVersionedFunction(
          mockFn,
          'testFunction',
          'test-project',
          'test-uuid',
        );

        await versionedFn.deploy(1);
        // Deployment is a placeholder for now
      });

      it('should throw error when SDK not configured', async () => {
        vi.mocked(getSettings).mockReturnValue(null);

        const mockFn = vi.fn();
        const versionedFn = createVersionedFunction(
          mockFn,
          'testFunction',
          'test-project',
          'test-uuid',
        );

        await expect(versionedFn.deploy(1)).rejects.toThrow('Lilypad SDK not configured');
      });
    });
  });

  describe('isVersionedFunction', () => {
    it('should return true for versioned functions', () => {
      vi.mocked(getSettings).mockReturnValue({
        apiKey: 'test-key',
        projectId: 'test-project',
        baseUrl: 'http://test.com',
      });

      const mockFn = vi.fn();
      const versionedFn = createVersionedFunction(
        mockFn,
        'testFunction',
        'test-project',
        'test-uuid',
      );

      expect(isVersionedFunction(versionedFn)).toBe(true);
    });

    it('should return false for regular functions', () => {
      const regularFn = () => {};
      expect(isVersionedFunction(regularFn)).toBe(false);
    });

    it('should return false for non-functions', () => {
      expect(isVersionedFunction({})).toBe(false);
      expect(isVersionedFunction(null)).toBe(false);
      expect(isVersionedFunction(undefined)).toBe(false);
      expect(isVersionedFunction('string')).toBe(false);
    });
  });
});