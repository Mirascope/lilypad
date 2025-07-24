import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';
import { TypeScriptExtractor } from './typescript-extractor';
import { metadataLoader } from './metadata-loader';
import { Closure } from '../utils/closure';

describe('TypeScript Extraction Integration Tests', () => {
  let tempDir: string;
  let tsConfigPath: string;
  const tsConfigContent = {
    compilerOptions: {
      target: 'es2020',
      module: 'commonjs',
      lib: ['es2020'],
      strict: true,
      esModuleInterop: true,
      skipLibCheck: true,
      moduleResolution: 'node',
    },
    include: ['**/*.ts'],
    exclude: ['node_modules'],
  };

  beforeEach(() => {
    // Create a temporary directory for each test
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lilypad-integration-test-'));
    tsConfigPath = path.join(tempDir, 'tsconfig.json');

    // Write tsconfig
    fs.writeFileSync(tsConfigPath, JSON.stringify(tsConfigContent, null, 2));

    // Reset metadata loader
    (metadataLoader as any).metadata = null;
    (metadataLoader as any).loaded = false;
    (metadataLoader as any).functionsByHash.clear();
    (metadataLoader as any).functionsByName.clear();
  });

  afterEach(() => {
    // Clean up temp directory
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }

    // Clear metadata loader state
    (metadataLoader as any).metadata = null;
    (metadataLoader as any).loaded = false;
    (metadataLoader as any).functionsByHash.clear();
    (metadataLoader as any).functionsByName.clear();
  });

  describe('End-to-end extraction and runtime loading', () => {
    it('should handle missing metadata gracefully', () => {
      // Mock process.cwd to empty directory
      const emptyDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lilypad-empty-'));
      vi.spyOn(process, 'cwd').mockReturnValue(emptyDir);

      // Force metadata reload
      (metadataLoader as any).loaded = false;
      metadataLoader.load();

      // Function should still work without TypeScript metadata
      const testFunc = (x: number): number => x * 2;
      const closure = Closure.fromFunction(testFunc, undefined, true, 'testFunc');

      // Should fall back to JavaScript extraction
      expect(closure.code).toContain('x * 2');
      expect(closure.name).toBe('testFunc');

      fs.rmSync(emptyDir, { recursive: true, force: true });
      vi.restoreAllMocks();
    });

    it('should handle extraction errors gracefully', () => {
      // Create invalid tsconfig
      fs.writeFileSync(tsConfigPath, 'invalid json');

      // TypeScriptExtractor should handle the error
      const extractor = new TypeScriptExtractor(tempDir, 'tsconfig.json');
      const metadata = extractor.extract();

      // Should still return valid metadata structure
      expect(metadata.version).toBe('1.0.0');
      expect(metadata.buildTime).toBeDefined();
      expect(metadata.functions).toBeDefined();
    });
  });

  describe('Build tool integration', () => {
    it('should support custom include patterns', () => {
      // Create files in different directories
      const examplesDir = path.join(tempDir, 'examples');
      fs.mkdirSync(examplesDir, { recursive: true });

      fs.writeFileSync(
        path.join(examplesDir, 'example.ts'),
        `import { trace } from '@lilypad/typescript-sdk';
         export const exampleFunc = trace((x: number) => x + 10, { 
           versioning: 'automatic', 
           name: 'exampleFunc' 
         });`,
      );

      // Create extractor with custom include patterns
      const extractor = new TypeScriptExtractor(tempDir, 'tsconfig.json', ['examples/**/*.ts']);
      const result = extractor.extract();

      // Verify function from examples was extracted
      const funcs = Object.values(result.functions);
      expect(funcs.some((f) => f.name === 'exampleFunc')).toBe(true);
    });
  });
});
