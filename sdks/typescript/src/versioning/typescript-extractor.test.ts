import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import os from 'os';
import { TypeScriptExtractor } from './typescript-extractor';

describe('TypeScriptExtractor', () => {
  let extractor: TypeScriptExtractor;
  let tempDir: string;
  let tsConfigPath: string;

  beforeEach(() => {
    // Create a temporary directory for each test
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lilypad-extractor-test-'));
    tsConfigPath = path.join(tempDir, 'tsconfig.json');

    // Create a basic tsconfig.json
    const tsConfig = {
      compilerOptions: {
        target: 'es2020',
        module: 'commonjs',
        lib: ['es2020'],
        strict: true,
        rootDir: '.',
        outDir: './dist',
      },
      include: ['./**/*.ts'],
      exclude: ['node_modules', 'dist'],
    };
    fs.writeFileSync(tsConfigPath, JSON.stringify(tsConfig, null, 2));
  });

  afterEach(() => {
    // Clean up temp directory
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
  });

  describe('constructor', () => {
    it('should initialize with valid tsconfig', () => {
      expect(() => {
        extractor = new TypeScriptExtractor(tempDir, 'tsconfig.json', ['./**/*.ts']);
      }).not.toThrow();
    });

    it('should handle tsconfig read errors gracefully', () => {
      // Create an invalid tsconfig
      fs.writeFileSync(tsConfigPath, 'invalid json');

      // Should not throw, but handle the error
      expect(() => {
        extractor = new TypeScriptExtractor(tempDir, 'tsconfig.json', ['./**/*.ts']);
      }).not.toThrow();
    });
  });

  describe('extract', () => {
    it('should extract metadata from source files', () => {
      // Copy fixture file to temp dir
      const fixtureContent = fs.readFileSync(
        path.join(__dirname, '../../tests/fixtures/simple-function.ts'),
        'utf-8',
      );
      fs.writeFileSync(path.join(tempDir, 'simple-function.ts'), fixtureContent);

      extractor = new TypeScriptExtractor(tempDir, 'tsconfig.json', ['./**/*.ts']);
      const metadata = extractor.extract();

      expect(metadata).toMatchObject({
        version: '1.0.0',
        buildTime: expect.any(String),
        functions: expect.any(Object),
      });

      const functions = Object.values(metadata.functions);
      expect(functions).toHaveLength(1);
      expect(functions[0].name).toBe('greetUser');
    });

    it('should skip node_modules files', () => {
      // Create a node_modules directory
      const nodeModulesDir = path.join(tempDir, 'node_modules', 'some-lib');
      fs.mkdirSync(nodeModulesDir, { recursive: true });
      fs.writeFileSync(
        path.join(nodeModulesDir, 'index.ts'),
        `import { trace } from '@lilypad/typescript-sdk';
        export const libFunc = trace((x: number) => x * 2, { versioning: 'automatic' });`,
      );

      extractor = new TypeScriptExtractor(tempDir, 'tsconfig.json', ['./**/*.ts']);
      const metadata = extractor.extract();

      expect(metadata.functions).toEqual({});
    });
  });

  describe('extractFunction', () => {
    it('should extract function name from options', () => {
      const sourceCode = `
        import { trace } from '@lilypad/typescript-sdk';
        
        const myFunc = trace(
          async (x: number) => x * 2,
          { versioning: 'automatic', name: 'myFunc' }
        );
      `;
      fs.writeFileSync(path.join(tempDir, 'test.ts'), sourceCode);

      extractor = new TypeScriptExtractor(tempDir, 'tsconfig.json', ['./**/*.ts']);
      const metadata = extractor.extract();
      const functions = Object.values(metadata.functions);

      expect(functions).toHaveLength(1);
      expect(functions[0].name).toBe('myFunc');
    });

    it('should use "anonymous" if no name can be determined', () => {
      // Copy anonymous function fixture
      const fixtureContent = fs.readFileSync(
        path.join(__dirname, '../../tests/fixtures/anonymous-function.ts'),
        'utf-8',
      );
      fs.writeFileSync(path.join(tempDir, 'anonymous.ts'), fixtureContent);

      extractor = new TypeScriptExtractor(tempDir, 'tsconfig.json', ['./**/*.ts']);
      const metadata = extractor.extract();
      const functions = Object.values(metadata.functions);

      // Should only extract the one with automatic versioning
      expect(functions).toHaveLength(1);
      expect(functions[0].name).toBe('anonymous');
    });
  });

  describe('isVersionedFunction', () => {
    it('should detect versioned functions with automatic versioning', () => {
      const sourceCode = `
        import { trace } from '@lilypad/typescript-sdk';
        
        const fn = (x: number) => x;
        
        trace(fn, { versioning: 'automatic' });
        trace(fn, { versioning: null });
        trace(fn);
      `;
      fs.writeFileSync(path.join(tempDir, 'versioning-test.ts'), sourceCode);

      extractor = new TypeScriptExtractor(tempDir, 'tsconfig.json', ['./**/*.ts']);
      const metadata = extractor.extract();

      // Only the first one should be extracted
      expect(Object.keys(metadata.functions)).toHaveLength(1);
    });
  });

  describe('complex extraction scenarios', () => {
    it('should extract functions with dependencies', () => {
      // Copy complex function fixture
      const fixtureContent = fs.readFileSync(
        path.join(__dirname, '../../tests/fixtures/complex-function.ts'),
        'utf-8',
      );
      fs.writeFileSync(path.join(tempDir, 'complex.ts'), fixtureContent);

      extractor = new TypeScriptExtractor(tempDir, 'tsconfig.json', ['./**/*.ts']);
      const metadata = extractor.extract();
      const functions = Object.values(metadata.functions);

      expect(functions).toHaveLength(1);
      expect(functions[0].name).toBe('calculatePrice');
      expect(functions[0].sourceCode).toContain('calculateDiscount');
      expect(functions[0].sourceCode).toContain('applyDiscount');
    });

    it('should handle multiple files', () => {
      // Create multiple test files
      fs.writeFileSync(
        path.join(tempDir, 'file1.ts'),
        `import { trace } from '@lilypad/typescript-sdk';
         export const func1 = trace((x: number) => x + 1, { versioning: 'automatic', name: 'func1' });`,
      );

      fs.writeFileSync(
        path.join(tempDir, 'file2.ts'),
        `import { trace } from '@lilypad/typescript-sdk';
         export const func2 = trace((x: number) => x + 2, { versioning: 'automatic', name: 'func2' });`,
      );

      extractor = new TypeScriptExtractor(tempDir, 'tsconfig.json', ['./**/*.ts']);
      const metadata = extractor.extract();
      const functions = Object.values(metadata.functions);

      expect(functions).toHaveLength(2);
      const names = functions.map((f) => f.name).sort();
      expect(names).toEqual(['func1', 'func2']);
    });
  });

  describe('saveMetadata', () => {
    it('should save metadata to file', () => {
      const sourceCode = `
        import { trace } from '@lilypad/typescript-sdk';
        export const testFunc = trace((x: number) => x * 2, { versioning: 'automatic' });
      `;
      fs.writeFileSync(path.join(tempDir, 'test.ts'), sourceCode);

      extractor = new TypeScriptExtractor(tempDir, 'tsconfig.json', ['./**/*.ts']);
      const outputPath = path.join(tempDir, 'output', 'metadata.json');

      extractor.saveMetadata(outputPath);

      expect(fs.existsSync(outputPath)).toBe(true);
      const savedMetadata = JSON.parse(fs.readFileSync(outputPath, 'utf-8'));
      expect(savedMetadata.version).toBe('1.0.0');
      expect(savedMetadata.buildTime).toBeDefined();
      expect(Object.keys(savedMetadata.functions)).toHaveLength(1);
    });
  });
});
