import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';
import { MetadataLoader } from './metadata-loader';
import { createTempDir, cleanupTempDir, createTestMetadata } from '../../tests/utils/test-helpers';

// Mock console.log to avoid noise in tests
vi.spyOn(console, 'log').mockImplementation(() => {});
vi.spyOn(console, 'info').mockImplementation(() => {});
vi.spyOn(console, 'debug').mockImplementation(() => {});

describe('MetadataLoader', () => {
  let tempDir: string;
  let loader: MetadataLoader;
  let originalExistsSync: typeof fs.existsSync;
  let originalReadFileSync: typeof fs.readFileSync;

  beforeEach(() => {
    tempDir = createTempDir();

    // Create a loader with mocked paths
    loader = new MetadataLoader();

    // Clear loader state
    (loader as any).metadata = null;
    (loader as any).loaded = false;
    (loader as any).functionsByHash.clear();
    (loader as any).functionsByName.clear();

    // Store original fs methods
    originalExistsSync = fs.existsSync;
    originalReadFileSync = fs.readFileSync;
  });

  afterEach(() => {
    cleanupTempDir(tempDir);
    vi.clearAllMocks();
    // Restore original fs methods
    fs.existsSync = originalExistsSync;
    fs.readFileSync = originalReadFileSync;
  });

  describe('loadMetadata', () => {
    it('should load metadata from file system', () => {
      createTestMetadata(tempDir);

      // Mock process.cwd to return our temp dir
      vi.spyOn(process, 'cwd').mockReturnValue(tempDir);

      // Mock fs.existsSync to only find our test file
      vi.spyOn(fs, 'existsSync').mockImplementation((p: string) => {
        const pathStr = p.toString();
        // Only return true for our test metadata file
        if (pathStr.includes(tempDir) && pathStr.endsWith('lilypad-metadata.json')) {
          return originalExistsSync(p);
        }
        return false;
      });

      loader.load();
      const result = loader.getAllFunctions();

      expect(result).toHaveLength(2);
      expect(result[0].name).toBe('testFunction');
      expect(result[1].name).toBe('anotherFunction');
    });

    it('should return empty array if no metadata file found', () => {
      // Mock process.cwd to return empty temp dir
      vi.spyOn(process, 'cwd').mockReturnValue(tempDir);

      // Mock fs.existsSync to return false for all paths
      vi.spyOn(fs, 'existsSync').mockReturnValue(false);

      loader.load();
      const result = loader.getAllFunctions();

      expect(result).toEqual([]);
    });

    it('should handle invalid JSON gracefully', () => {
      fs.writeFileSync(path.join(tempDir, 'lilypad-metadata.json'), 'invalid json');
      vi.spyOn(process, 'cwd').mockReturnValue(tempDir);

      // Mock fs.existsSync to only find our test file
      vi.spyOn(fs, 'existsSync').mockImplementation((p: string) => {
        const pathStr = p.toString();
        if (pathStr.includes(tempDir) && pathStr.endsWith('lilypad-metadata.json')) {
          return originalExistsSync(p);
        }
        return false;
      });

      loader.load();
      const result = loader.getAllFunctions();

      expect(result).toEqual([]);
    });

    it('should cache loaded metadata', () => {
      createTestMetadata(tempDir);
      vi.spyOn(process, 'cwd').mockReturnValue(tempDir);

      // Mock fs.existsSync to only find our test file
      vi.spyOn(fs, 'existsSync').mockImplementation((p: string) => {
        const pathStr = p.toString();
        if (pathStr.includes(tempDir) && pathStr.endsWith('lilypad-metadata.json')) {
          return originalExistsSync(p);
        }
        return false;
      });

      const readFileSpy = vi.spyOn(fs, 'readFileSync');

      // First load
      loader.load();
      const firstResult = loader.getAllFunctions();

      // Second load (should use cache)
      loader.load();
      const secondResult = loader.getAllFunctions();

      expect(firstResult).toEqual(secondResult);
      expect(firstResult).toHaveLength(2);

      // Count actual metadata file reads (not counting other file reads)
      const metadataReads = readFileSpy.mock.calls.filter((call) =>
        call[0].toString().includes('metadata.json'),
      ).length;
      expect(metadataReads).toBe(1);
    });
  });

  describe('hasMetadata', () => {
    it('should return true when metadata is available', () => {
      createTestMetadata(tempDir);
      vi.spyOn(process, 'cwd').mockReturnValue(tempDir);

      // Mock fs.existsSync to only find our test file
      vi.spyOn(fs, 'existsSync').mockImplementation((p: string) => {
        const pathStr = p.toString();
        if (pathStr.includes(tempDir) && pathStr.endsWith('lilypad-metadata.json')) {
          return originalExistsSync(p);
        }
        return false;
      });

      expect(loader.hasMetadata()).toBe(true);
    });

    it('should return false when no metadata is available', () => {
      vi.spyOn(process, 'cwd').mockReturnValue(tempDir);

      // Mock fs.existsSync to return false for all paths
      vi.spyOn(fs, 'existsSync').mockReturnValue(false);

      expect(loader.hasMetadata()).toBe(false);
    });
  });

  describe('getByHash', () => {
    beforeEach(() => {
      createTestMetadata(tempDir);
      vi.spyOn(process, 'cwd').mockReturnValue(tempDir);

      // Mock fs.existsSync to only find our test file
      vi.spyOn(fs, 'existsSync').mockImplementation((p: string) => {
        const pathStr = p.toString();
        if (pathStr.includes(tempDir) && pathStr.endsWith('lilypad-metadata.json')) {
          return originalExistsSync(p);
        }
        return false;
      });
    });

    it('should return function by hash', () => {
      const result = loader.getByHash('hash123');

      expect(result).toBeDefined();
      expect(result?.name).toBe('testFunction');
      expect(result?.hash).toBe('hash123');
    });

    it('should return null for non-existent hash', () => {
      const result = loader.getByHash('nonexistent');

      expect(result).toBeNull();
    });
  });

  describe('getByName', () => {
    beforeEach(() => {
      createTestMetadata(tempDir);
      vi.spyOn(process, 'cwd').mockReturnValue(tempDir);

      // Mock fs.existsSync to only find our test file
      vi.spyOn(fs, 'existsSync').mockImplementation((p: string) => {
        const pathStr = p.toString();
        if (pathStr.includes(tempDir) && pathStr.endsWith('lilypad-metadata.json')) {
          return originalExistsSync(p);
        }
        return false;
      });
    });

    it('should return function by name', () => {
      const result = loader.getByName('testFunction');

      expect(result).toBeDefined();
      expect(result?.name).toBe('testFunction');
      expect(result?.hash).toBe('hash123');
    });

    it('should return null for non-existent name', () => {
      const result = loader.getByName('nonexistent');

      expect(result).toBeNull();
    });
  });

  describe('getAllFunctions', () => {
    it('should return all functions', () => {
      createTestMetadata(tempDir);
      vi.spyOn(process, 'cwd').mockReturnValue(tempDir);

      // Mock fs.existsSync to only find our test file
      vi.spyOn(fs, 'existsSync').mockImplementation((p: string) => {
        const pathStr = p.toString();
        if (pathStr.includes(tempDir) && pathStr.endsWith('lilypad-metadata.json')) {
          return originalExistsSync(p);
        }
        return false;
      });

      const result = loader.getAllFunctions();

      expect(result).toHaveLength(2);
      expect(result[0].name).toBe('testFunction');
      expect(result[1].name).toBe('anotherFunction');
    });

    it('should return empty array when no metadata', () => {
      vi.spyOn(process, 'cwd').mockReturnValue(tempDir);

      // Mock fs.existsSync to return false for all paths
      vi.spyOn(fs, 'existsSync').mockReturnValue(false);

      const result = loader.getAllFunctions();

      expect(result).toEqual([]);
    });
  });

  describe('metadata file paths', () => {
    it('should check standard locations', () => {
      // Mock fs.existsSync to return false for all paths
      const existsSpy = vi.spyOn(fs, 'existsSync').mockReturnValue(false);

      loader.load();

      // Should check for both versioning-metadata.json and lilypad-metadata.json
      const paths = existsSpy.mock.calls.map((call) => call[0] as string);

      expect(paths.some((p) => p.includes('versioning-metadata.json'))).toBe(true);
      expect(paths.some((p) => p.includes('lilypad-metadata.json'))).toBe(true);
    });
  });
});
