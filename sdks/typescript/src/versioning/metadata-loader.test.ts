import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import * as fs from 'fs';

vi.mock('fs');

import { MetadataLoader, getTypeScriptSource, metadataLoader } from './metadata-loader';

describe.skip('MetadataLoader', () => {
  let loader: MetadataLoader;
  const mockMetadata = {
    version: '1.0.0',
    buildTime: '2025-01-01T00:00:00Z',
    functions: {
      hash123: {
        name: 'testFunction',
        hash: 'hash123',
        sourceCode: 'function testFunction() { return 42; }',
        selfContainedCode: '// Complete\nfunction testFunction() { return 42; }',
        signature: 'function testFunction()',
        filePath: 'src/test.ts',
        startLine: 1,
        endLine: 3,
        dependencies: {},
      },
      hash456: {
        name: 'anotherFunction',
        hash: 'hash456',
        sourceCode: 'const anotherFunction = () => "hello";',
        signature: 'const anotherFunction',
        filePath: 'src/another.ts',
        startLine: 5,
        endLine: 5,
        dependencies: {},
      },
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();

    // Clear any existing metadata that might have been loaded by the singleton
    (metadataLoader as any).metadata = null;
    (metadataLoader as any).loaded = false;
    (metadataLoader as any).functionsByHash.clear();
    (metadataLoader as any).functionsByName.clear();

    loader = new MetadataLoader();
  });

  afterEach(() => {
    // Clear the singleton's cache
    (loader as any).metadata = null;
    (loader as any).loaded = false;

    // Also clear the global singleton
    (metadataLoader as any).metadata = null;
    (metadataLoader as any).loaded = false;
    (metadataLoader as any).functionsByHash.clear();
    (metadataLoader as any).functionsByName.clear();
  });

  describe('loadMetadata', () => {
    it('should load metadata from file system', () => {
      vi.mocked(fs.existsSync).mockReturnValue(true);
      vi.mocked(fs.readFileSync).mockReturnValue(JSON.stringify(mockMetadata));

      // Force reload
      (loader as any).loaded = false;
      (loader as any).metadata = null;

      // Call load() which internally calls loadMetadata
      loader.load();
      const result = loader.getAllFunctions();

      expect(result).toHaveLength(2);
      expect(fs.readFileSync).toHaveBeenCalled();
    });

    it('should try multiple paths to find metadata', () => {
      vi.mocked(fs.existsSync)
        .mockReturnValueOnce(false) // First path
        .mockReturnValueOnce(false) // Second path
        .mockReturnValueOnce(true); // Third path
      vi.mocked(fs.readFileSync).mockReturnValue(JSON.stringify(mockMetadata));

      loader.load();
      const result = loader.getAllFunctions();

      expect(result).toHaveLength(2);
      expect(fs.existsSync).toHaveBeenCalledTimes(3);
    });

    it('should return empty array if no metadata file found', () => {
      vi.mocked(fs.existsSync).mockReturnValue(false);

      loader.load();
      const result = loader.getAllFunctions();

      expect(result).toEqual([]);
    });

    it('should handle invalid JSON gracefully', () => {
      vi.mocked(fs.existsSync).mockReturnValue(true);
      vi.mocked(fs.readFileSync).mockReturnValue('invalid json');

      loader.load();
      const result = loader.getAllFunctions();

      expect(result).toEqual([]);
    });

    it('should cache loaded metadata', () => {
      vi.mocked(fs.existsSync).mockReturnValue(true);
      vi.mocked(fs.readFileSync).mockReturnValue(JSON.stringify(mockMetadata));

      // First load
      loader.load();
      // Second load (should use cache)
      loader.load();

      // Should only read file once
      expect(fs.readFileSync).toHaveBeenCalledTimes(1);
    });
  });

  describe('hasMetadata', () => {
    it('should return true when metadata is available', () => {
      vi.mocked(fs.existsSync).mockReturnValue(true);
      vi.mocked(fs.readFileSync).mockReturnValue(JSON.stringify(mockMetadata));

      expect(loader.hasMetadata()).toBe(true);
    });

    it('should return false when no metadata is available', () => {
      vi.mocked(fs.existsSync).mockReturnValue(false);

      expect(loader.hasMetadata()).toBe(false);
    });
  });

  describe('getByHash', () => {
    beforeEach(() => {
      vi.mocked(fs.existsSync).mockReturnValue(true);
      vi.mocked(fs.readFileSync).mockReturnValue(JSON.stringify(mockMetadata));
    });

    it('should return function by hash', () => {
      const result = loader.getByHash('hash123');

      expect(result).toEqual(mockMetadata.functions.hash123);
    });

    it('should return null for non-existent hash', () => {
      const result = loader.getByHash('nonexistent');

      expect(result).toBeNull();
    });

    it('should return null when no metadata available', () => {
      vi.mocked(fs.existsSync).mockReturnValue(false);
      loader = new MetadataLoader();

      const result = loader.getByHash('hash123');

      expect(result).toBeNull();
    });
  });

  describe('getByName', () => {
    beforeEach(() => {
      vi.mocked(fs.existsSync).mockReturnValue(true);
      vi.mocked(fs.readFileSync).mockReturnValue(JSON.stringify(mockMetadata));
    });

    it('should return function by name', () => {
      const result = loader.getByName('testFunction');

      expect(result).toEqual(mockMetadata.functions.hash123);
    });

    it('should return first match when multiple functions have same name', () => {
      const metadataWithDuplicates = {
        ...mockMetadata,
        functions: {
          hash1: { ...mockMetadata.functions.hash123, name: 'duplicate' },
          hash2: { ...mockMetadata.functions.hash456, name: 'duplicate' },
        },
      };
      vi.mocked(fs.readFileSync).mockReturnValue(JSON.stringify(metadataWithDuplicates));
      loader = new MetadataLoader();

      const result = loader.getByName('duplicate');

      expect(result?.hash).toBe('hash1');
    });

    it('should return null for non-existent name', () => {
      const result = loader.getByName('nonexistent');

      expect(result).toBeNull();
    });
  });

  describe('getAllFunctions', () => {
    it('should return all functions', () => {
      vi.mocked(fs.existsSync).mockReturnValue(true);
      vi.mocked(fs.readFileSync).mockReturnValue(JSON.stringify(mockMetadata));

      const result = loader.getAllFunctions();

      expect(result).toHaveLength(2);
      expect(result[0]).toEqual(mockMetadata.functions.hash123);
      expect(result[1]).toEqual(mockMetadata.functions.hash456);
    });

    it('should return empty array when no metadata', () => {
      vi.mocked(fs.existsSync).mockReturnValue(false);

      const result = loader.getAllFunctions();

      expect(result).toEqual([]);
    });
  });

  describe('getTypeScriptSource', () => {
    beforeEach(() => {
      vi.mocked(fs.existsSync).mockReturnValue(true);
      vi.mocked(fs.readFileSync).mockReturnValue(JSON.stringify(mockMetadata));
    });

    it('should return self-contained code when available', () => {
      const result = getTypeScriptSource('hash123');

      expect(result).toBe('// Complete\nfunction testFunction() { return 42; }');
    });

    it('should fall back to source code when self-contained not available', () => {
      const result = getTypeScriptSource('hash456');

      expect(result).toBe('const anotherFunction = () => "hello";');
    });

    it('should look up by name when hash not found', () => {
      const result = getTypeScriptSource('nonexistent', 'testFunction');

      expect(result).toBe('// Complete\nfunction testFunction() { return 42; }');
    });

    it('should return null when not found', () => {
      const result = getTypeScriptSource('nonexistent', 'alsoNonexistent');

      expect(result).toBeNull();
    });
  });

  describe('metadata file paths', () => {
    it('should check standard locations', () => {
      vi.mocked(fs.existsSync).mockReturnValue(false);

      loader.load();

      // Should check for both versioning-metadata.json and lilypad-metadata.json
      const calls = vi.mocked(fs.existsSync).mock.calls;
      const paths = calls.map((call) => call[0] as string);

      expect(paths.some((p) => p.includes('versioning-metadata.json'))).toBe(true);
      expect(paths.some((p) => p.includes('lilypad-metadata.json'))).toBe(true);
    });
  });
});
