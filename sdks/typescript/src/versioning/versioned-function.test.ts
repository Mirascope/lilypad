import { describe, it, expect, vi, beforeEach } from 'vitest';
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

describe('versioned-function', () => {
  beforeEach(() => {
    vi.clearAllMocks();
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
      it('should return a function that executes with version tracking', async () => {
        const mockClient = {
          projects: {
            functions: {
              getByVersion: vi.fn().mockResolvedValue({
                uuid: 'version-uuid',
                hash: 'version-hash',
                version_num: 1,
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

        const v1 = versionedFn.version(1);
        const result = v1(5);

        expect(result).toBe(10);
        expect(mockFn).toHaveBeenCalledWith(5);

        // The version method logs but doesn't make API calls yet (not implemented)
        // So we just verify the function was called correctly
      });
    });

    describe('remote method', () => {
      it('should execute the function (placeholder for remote execution)', async () => {
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
