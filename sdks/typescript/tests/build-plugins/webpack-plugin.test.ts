import { describe, it, expect, beforeEach, afterEach, vi, type MockedClass } from 'vitest';
import {
  LilypadWebpackPlugin,
  type LilypadWebpackPluginOptions,
} from '../../src/build-plugins/webpack-plugin';
import type { Compiler } from 'webpack';
import fs from 'fs';
import path from 'path';
import os from 'os';
import { TypeScriptExtractor } from '../../src/versioning/typescript-extractor';

// Mock the TypeScriptExtractor
vi.mock('../../src/versioning/typescript-extractor', () => {
  const mockExtract = vi.fn().mockReturnValue({
    version: '1.0.0',
    buildTime: '2024-01-01T00:00:00Z',
    functions: {
      processData: {
        name: 'processData',
        hash: 'mock-hash-123',
        sourceCode: 'const processData = (data) => { return data; }',
        signature: '(data: any) => any',
        filePath: '/mock/process.ts',
        startLine: 5,
        endLine: 7,
        dependencies: {
          lodash: '4.17.21',
        },
      },
      calculateSum: {
        name: 'calculateSum',
        hash: 'mock-hash-456',
        sourceCode: 'const calculateSum = (a, b) => a + b',
        signature: '(a: number, b: number) => number',
        filePath: '/mock/math.ts',
        startLine: 10,
        endLine: 10,
        dependencies: {},
      },
    },
  });

  return {
    TypeScriptExtractor: vi.fn().mockImplementation(() => ({
      extract: mockExtract,
    })),
  };
});

const mockedTypeScriptExtractor = TypeScriptExtractor as MockedClass<typeof TypeScriptExtractor>;

describe('Webpack Plugin', () => {
  let tempDir: string;
  let plugin: LilypadWebpackPlugin;
  let mockCompiler: Compiler;
  let mockCompilation: any;
  let hooks: Record<string, any>;

  beforeEach(() => {
    // Create temp directory
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'webpack-plugin-test-'));

    // Reset mocks
    vi.clearAllMocks();

    // Mock fs operations
    vi.spyOn(fs, 'existsSync').mockImplementation((filePath) => {
      const pathStr = filePath.toString();
      // Return true for tsconfig.json and metadata files by default
      return (
        pathStr.includes('tsconfig.json') ||
        pathStr.endsWith('tsconfig.json') ||
        pathStr.includes('lilypad-metadata.json') ||
        pathStr.includes('metadata.json')
      );
    });
    vi.spyOn(fs, 'readFileSync').mockImplementation((filePath) => {
      if (filePath.toString().includes('lilypad-metadata.json')) {
        return JSON.stringify({
          version: '1.0.0',
          buildTime: '2024-01-01T00:00:00Z',
          functions: {},
        });
      }
      return '';
    });
    vi.spyOn(fs, 'writeFileSync').mockImplementation(() => {});
    vi.spyOn(fs, 'mkdirSync').mockImplementation(() => tempDir);

    // Create mock hooks
    hooks = {
      beforeCompile: {
        tapAsync: vi.fn((name: string, callback: Function) => {
          hooks.beforeCompile._callback = callback;
        }),
      },
      emit: {
        tapAsync: vi.fn((name: string, callback: Function) => {
          hooks.emit._callback = callback;
        }),
      },
    };

    // Create mock compiler
    mockCompiler = {
      context: tempDir,
      hooks,
    } as any;

    // Create mock compilation
    mockCompilation = {
      assets: {},
    };
  });

  afterEach(() => {
    // Clean up temp directory
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
    vi.restoreAllMocks();
  });

  describe('constructor', () => {
    it('should initialize with default options', () => {
      plugin = new LilypadWebpackPlugin();
      expect(plugin).toBeInstanceOf(LilypadWebpackPlugin);

      // Test internal options through behavior
      plugin.apply(mockCompiler);
      expect(hooks.beforeCompile.tapAsync).toHaveBeenCalledWith(
        'LilypadWebpackPlugin',
        expect.any(Function),
      );
    });

    it('should initialize with custom options', () => {
      const options: LilypadWebpackPluginOptions = {
        tsConfig: './custom-tsconfig.json',
        output: 'custom-output.json',
        include: ['lib/**/*.ts', 'src/**/*.tsx'],
        verbose: true,
      };

      plugin = new LilypadWebpackPlugin(options);
      expect(plugin).toBeInstanceOf(LilypadWebpackPlugin);
    });
  });

  describe('apply method', () => {
    beforeEach(() => {
      plugin = new LilypadWebpackPlugin();
    });

    it('should register webpack hooks', () => {
      plugin.apply(mockCompiler);

      expect(hooks.beforeCompile.tapAsync).toHaveBeenCalledWith(
        'LilypadWebpackPlugin',
        expect.any(Function),
      );
      expect(hooks.emit.tapAsync).toHaveBeenCalledWith(
        'LilypadWebpackPlugin',
        expect.any(Function),
      );
    });

    it('should use the correct plugin name', () => {
      plugin.apply(mockCompiler);

      expect(hooks.beforeCompile.tapAsync).toHaveBeenCalledWith(
        'LilypadWebpackPlugin',
        expect.any(Function),
      );
      expect(hooks.emit.tapAsync).toHaveBeenCalledWith(
        'LilypadWebpackPlugin',
        expect.any(Function),
      );
    });
  });

  describe('beforeCompile hook', () => {
    beforeEach(() => {
      plugin = new LilypadWebpackPlugin({ verbose: true });
      plugin.apply(mockCompiler);
    });

    it('should extract metadata successfully', async () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      const callback = vi.fn();

      await hooks.beforeCompile._callback({}, callback);

      // The plugin logs when extraction starts
      expect(consoleSpy).toHaveBeenCalledWith('[Lilypad] Extracting TypeScript metadata...');

      // Check that the extractor was called
      expect(mockedTypeScriptExtractor).toHaveBeenCalled();

      // Callback should be called without error
      expect(callback).toHaveBeenCalledWith();
      expect(callback).not.toHaveBeenCalledWith(expect.any(Error));

      consoleSpy.mockRestore();
    });

    it('should handle missing tsconfig gracefully', async () => {
      vi.spyOn(fs, 'existsSync').mockReturnValue(false);

      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      const callback = vi.fn();

      await hooks.beforeCompile._callback({}, callback);

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        expect.stringContaining('[Lilypad] TypeScript config not found:'),
      );
      expect(callback).toHaveBeenCalledWith();
      expect(callback).not.toHaveBeenCalledWith(expect.any(Error));

      consoleWarnSpy.mockRestore();
    });

    it('should not warn when verbose is false and tsconfig is missing', async () => {
      plugin = new LilypadWebpackPlugin({ verbose: false });
      plugin.apply(mockCompiler);

      vi.spyOn(fs, 'existsSync').mockReturnValue(false);

      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      const callback = vi.fn();

      await hooks.beforeCompile._callback({}, callback);

      expect(consoleWarnSpy).not.toHaveBeenCalled();
      expect(callback).toHaveBeenCalledWith();

      consoleWarnSpy.mockRestore();
    });

    it('should handle extraction errors by logging and continuing', async () => {
      // Use the mocked TypeScriptExtractor
      mockedTypeScriptExtractor.mockImplementationOnce(() => ({
        extract: vi.fn().mockImplementation(() => {
          throw new Error('Extraction failed');
        }),
      }));

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const callback = vi.fn();

      await hooks.beforeCompile._callback({}, callback);

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[Lilypad] Error extracting metadata:',
        expect.any(Error),
      );
      expect(callback).toHaveBeenCalledWith();
      expect(callback).not.toHaveBeenCalledWith(expect.any(Error));

      consoleErrorSpy.mockRestore();
    });

    it('should not fail build on extraction error', async () => {
      // Use the mocked TypeScriptExtractor
      mockedTypeScriptExtractor.mockImplementationOnce(() => ({
        extract: vi.fn().mockImplementation(() => {
          throw new Error('Non-critical extraction error');
        }),
      }));

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const callback = vi.fn();

      await hooks.beforeCompile._callback({}, callback);

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[Lilypad] Error extracting metadata:',
        expect.any(Error),
      );
      expect(callback).toHaveBeenCalledWith();
      expect(callback).not.toHaveBeenCalledWith(expect.any(Error));

      consoleErrorSpy.mockRestore();
    });
  });

  describe('emit hook', () => {
    beforeEach(() => {
      plugin = new LilypadWebpackPlugin({ verbose: true, output: 'build-metadata.json' });
      plugin.apply(mockCompiler);
    });

    it('should add metadata to webpack assets when file exists', async () => {
      const mockMetadata = JSON.stringify({
        version: '1.0.0',
        buildTime: '2024-01-01T00:00:00Z',
        functions: { test: {} },
      });

      vi.spyOn(fs, 'existsSync').mockImplementation((_filePath) => {
        // Return true for the metadata file path
        return true;
      });
      vi.spyOn(fs, 'readFileSync').mockReturnValue(mockMetadata);

      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      const callback = vi.fn();

      await hooks.emit._callback(mockCompilation, callback);

      expect(mockCompilation.assets['build-metadata.json']).toBeDefined();
      expect(mockCompilation.assets['build-metadata.json'].source()).toBe(mockMetadata);
      expect(mockCompilation.assets['build-metadata.json'].size()).toBe(mockMetadata.length);
      expect(consoleSpy).toHaveBeenCalledWith(
        '[Lilypad] Added build-metadata.json to build output',
      );
      expect(callback).toHaveBeenCalledWith();

      consoleSpy.mockRestore();
    });

    it('should skip when metadata file does not exist', async () => {
      vi.spyOn(fs, 'existsSync').mockReturnValue(false);

      const callback = vi.fn();

      await hooks.emit._callback(mockCompilation, callback);

      expect(mockCompilation.assets['build-metadata.json']).toBeUndefined();
      expect(callback).toHaveBeenCalledWith();
    });
  });

  describe('integration scenarios', () => {
    it('should work with custom include patterns', async () => {
      plugin = new LilypadWebpackPlugin({
        include: ['components/**/*.tsx', 'utils/**/*.ts', 'lib/**/*.ts'],
      });

      plugin.apply(mockCompiler);

      const callback = vi.fn();
      await hooks.beforeCompile._callback({}, callback);

      // Use the mocked TypeScriptExtractor
      expect(mockedTypeScriptExtractor).toHaveBeenCalledWith(tempDir, 'tsconfig.json', [
        'components/**/*.tsx',
        'utils/**/*.ts',
        'lib/**/*.ts',
      ]);
    });

    it('should not interfere with webpack build on errors', async () => {
      // Simulate various error conditions
      // Use the mocked TypeScriptExtractor

      // Test 1: Extraction error
      mockedTypeScriptExtractor.mockImplementationOnce(() => ({
        extract: vi.fn().mockImplementation(() => {
          throw new Error('Critical extraction error');
        }),
      }));

      plugin = new LilypadWebpackPlugin();
      plugin.apply(mockCompiler);

      const callback1 = vi.fn();
      await hooks.beforeCompile._callback({}, callback1);
      expect(callback1).toHaveBeenCalledWith();

      // Test 2: File system error
      vi.spyOn(fs, 'writeFileSync').mockImplementationOnce(() => {
        throw new Error('Cannot write file');
      });

      const callback2 = vi.fn();
      await hooks.beforeCompile._callback({}, callback2);
      // Should still complete without error
      expect(callback2).toHaveBeenCalledWith();
    });
  });

  describe('edge cases', () => {
    it('should handle empty extraction results', async () => {
      // Use the mocked TypeScriptExtractor
      mockedTypeScriptExtractor.mockImplementationOnce(() => ({
        extract: vi.fn().mockReturnValue({
          version: '1.0.0',
          buildTime: '2024-01-01T00:00:00Z',
          functions: {},
        }),
      }));

      plugin = new LilypadWebpackPlugin({ verbose: true });
      plugin.apply(mockCompiler);

      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      const callback = vi.fn();

      await hooks.beforeCompile._callback({}, callback);

      expect(consoleSpy).toHaveBeenCalledWith('[Lilypad] Extracted 0 versioned functions');
      expect(callback).toHaveBeenCalledWith();

      consoleSpy.mockRestore();
    });

    it('should handle very large metadata gracefully', async () => {
      const largeFunctions: Record<string, any> = {};
      for (let i = 0; i < 1000; i++) {
        largeFunctions[`function${i}`] = {
          name: `function${i}`,
          hash: `hash-${i}`,
          sourceCode: 'x'.repeat(1000),
          signature: `() => void`,
          filePath: `/mock/file${i}.ts`,
          startLine: i,
          endLine: i + 10,
          dependencies: {},
        };
      }

      // Use the mocked TypeScriptExtractor
      mockedTypeScriptExtractor.mockImplementationOnce(() => ({
        extract: vi.fn().mockReturnValue({
          version: '1.0.0',
          buildTime: '2024-01-01T00:00:00Z',
          functions: largeFunctions,
        }),
      }));

      plugin = new LilypadWebpackPlugin();
      plugin.apply(mockCompiler);

      const callback = vi.fn();
      await hooks.beforeCompile._callback({}, callback);

      expect(fs.writeFileSync).toHaveBeenCalled();
      expect(callback).toHaveBeenCalledWith();
    });
  });
});
