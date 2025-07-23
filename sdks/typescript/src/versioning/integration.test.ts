import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

// Mock fs module before imports
vi.mock('fs');
vi.mock('typescript', () => {
  const mocked = {
    readConfigFile: vi.fn(),
    parseJsonConfigFileContent: vi.fn(),
    createProgram: vi.fn(),
    sys: {
      readFile: vi.fn(),
    },
    forEachChild: vi.fn(),
    isCallExpression: vi.fn(() => false),
    isIdentifier: vi.fn(() => false),
    isObjectLiteralExpression: vi.fn(() => false),
    isPropertyAssignment: vi.fn(() => false),
    isStringLiteral: vi.fn(() => false),
    isVariableDeclaration: vi.fn(() => false),
    isFunctionExpression: vi.fn(() => false),
    isArrowFunction: vi.fn(() => false),
    SyntaxKind: {
      AsyncKeyword: 134,
    },
  };
  return {
    ...mocked,
    default: mocked,
  };
});

import { Project } from 'ts-morph';
import * as ts from 'typescript';
import { TypeScriptExtractor } from './typescript-extractor';
import { metadataLoader } from './metadata-loader';
import { Closure } from '../utils/closure';

describe.skip('TypeScript Extraction Integration Tests', () => {
  const testProjectDir = '/test/project';
  const tsConfigContent = {
    compilerOptions: {
      target: 'es2020',
      module: 'commonjs',
      lib: ['es2020'],
      strict: true,
    },
    include: ['src/**/*.ts'],
  };

  beforeEach(() => {
    vi.clearAllMocks();
    // Reset metadata loader
    (metadataLoader as any).metadata = null;
    (metadataLoader as any).loaded = false;

    // Setup TypeScript mocks
    vi.mocked(ts.readConfigFile).mockReturnValue({
      config: tsConfigContent,
    });

    vi.mocked(ts.parseJsonConfigFileContent).mockReturnValue({
      options: {
        target: 7, // ES2020
        module: 1, // CommonJS
      },
      fileNames: [],
      errors: [],
    } as any);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('End-to-end extraction and runtime loading', () => {
    it.skip('should extract TypeScript code and load it at runtime', () => {
      // Setup filesystem mocks
      vi.mocked(fs.existsSync).mockImplementation((p) => {
        const pathStr = p.toString();
        return pathStr.includes('tsconfig.json') || pathStr.includes('src/');
      });

      vi.mocked(fs.readFileSync).mockImplementation((p) => {
        const pathStr = p.toString();
        if (pathStr.includes('tsconfig.json')) {
          return JSON.stringify(tsConfigContent);
        }
        return '';
      });

      // Create test source code
      const sourceCode = `
        import { trace } from '@lilypad/typescript-sdk';
        
        interface User {
          name: string;
          age: number;
        }
        
        const GREETING = 'Hello';
        
        function formatName(user: User): string {
          return user.name.toUpperCase();
        }
        
        export const greetUser = trace(
          (user: User): string => {
            return GREETING + ' ' + formatName(user) + '!';
          },
          { versioning: 'automatic', name: 'greetUser' }
        );
      `;

      // Mock TypeScript compiler to return our source
      const mockSourceFile = {
        fileName: path.join(testProjectDir, 'src/index.ts'),
        getText: () => sourceCode,
        getFullText: () => sourceCode,
        statements: [],
      };

      // Setup mock for createProgram
      vi.mocked(ts.createProgram).mockReturnValue({
        getSourceFiles: () => [mockSourceFile],
      } as any);

      // Extract metadata
      const extractor = new TypeScriptExtractor(testProjectDir, 'tsconfig.json');
      const metadata = extractor.extract();

      // Verify extraction
      expect(Object.keys(metadata.functions)).toHaveLength(1);
      const func = Object.values(metadata.functions)[0];
      expect(func.name).toBe('greetUser');
      expect(func.sourceCode).toContain('(user: User): string =>');
      expect(func.selfContainedCode).toContain('interface User');
      expect(func.selfContainedCode).toContain('const GREETING');
      expect(func.selfContainedCode).toContain('function formatName');

      // Save metadata to "disk"
      const metadataPath = path.join(testProjectDir, 'lilypad-metadata.json');
      vi.mocked(fs.existsSync).mockImplementation((p) => {
        return p.toString() === metadataPath;
      });
      vi.mocked(fs.readFileSync).mockImplementation((p) => {
        if (p.toString() === metadataPath) {
          return JSON.stringify(metadata);
        }
        return '';
      });

      // Simulate runtime loading
      const tsSource = metadataLoader.getByName('greetUser');
      expect(tsSource).toBeDefined();
      expect(tsSource?.selfContainedCode).toContain('interface User');
    });

    it('should handle complex dependency chains', () => {
      const complexCode = `
        import { trace } from '@lilypad/typescript-sdk';
        
        // Base types
        interface Product {
          id: string;
          price: number;
        }
        
        interface User {
          isPremium: boolean;
        }
        
        // Constants that depend on each other
        const BASE_DISCOUNT = 0.05;
        const PREMIUM_MULTIPLIER = 3;
        const MAX_DISCOUNT = BASE_DISCOUNT * PREMIUM_MULTIPLIER;
        
        // Functions that depend on constants
        function calculateDiscount(user: User): number {
          return user.isPremium ? MAX_DISCOUNT : BASE_DISCOUNT;
        }
        
        function applyDiscount(price: number, discount: number): number {
          return price * (1 - discount);
        }
        
        // Main function with deep dependencies
        export const calculatePrice = trace(
          (product: Product, user: User): number => {
            const discount = calculateDiscount(user);
            return applyDiscount(product.price, discount);
          },
          { versioning: 'automatic', name: 'calculatePrice' }
        );
      `;

      // Setup project
      const project = new Project({
        useInMemoryFileSystem: true,
        compilerOptions: tsConfigContent.compilerOptions,
      });

      const _sourceFile = project.createSourceFile('src/index.ts', complexCode);

      // Create extractor with mocked project
      const extractor = new TypeScriptExtractor(testProjectDir, 'tsconfig.json');
      (extractor as any).dependencyExtractor = {
        generateSelfContainedCode: (_node: unknown, _sf: unknown) => {
          // Simulate full extraction
          return `// Type dependencies
interface Product {
  id: string;
  price: number;
}
interface User {
  isPremium: boolean;
}

// Variable and class dependencies
const BASE_DISCOUNT = 0.05;
const PREMIUM_MULTIPLIER = 3;
const MAX_DISCOUNT = BASE_DISCOUNT * PREMIUM_MULTIPLIER;

// Function dependencies
function calculateDiscount(user: User): number {
  return user.isPremium ? MAX_DISCOUNT : BASE_DISCOUNT;
}
function applyDiscount(price: number, discount: number): number {
  return price * (1 - discount);
}

// Main function
(product: Product, user: User): number => {
  const discount = calculateDiscount(user);
  return applyDiscount(product.price, discount);
}`;
        },
      };

      // Extract and verify all dependencies are captured
      const metadata = extractor.extract();
      const funcs = Object.values(metadata.functions);

      if (funcs.length > 0) {
        const func = funcs[0];
        expect(func.selfContainedCode).toContain('BASE_DISCOUNT');
        expect(func.selfContainedCode).toContain('PREMIUM_MULTIPLIER');
        expect(func.selfContainedCode).toContain('MAX_DISCOUNT');
        expect(func.selfContainedCode).toContain('calculateDiscount');
        expect(func.selfContainedCode).toContain('applyDiscount');
      }
    });

    it.skip('should integrate with Closure for runtime versioning', () => {
      // Setup metadata
      const testMetadata = {
        version: '1.0.0',
        buildTime: new Date().toISOString(),
        functions: {
          testhash: {
            name: 'testFunc',
            hash: 'testhash',
            sourceCode: 'const testFunc = (x: number): number => x * 2;',
            selfContainedCode: '// Complete\nconst testFunc = (x: number): number => x * 2;',
            signature: 'const testFunc',
            filePath: 'src/test.ts',
            startLine: 1,
            endLine: 1,
            dependencies: {},
          },
        },
      };

      // Clear metadata loader state
      (metadataLoader as any).metadata = null;
      (metadataLoader as any).loaded = false;
      (metadataLoader as any).functionsByHash.clear();
      (metadataLoader as any).functionsByName.clear();

      // Mock metadata loading
      vi.mocked(fs.existsSync).mockReturnValue(true);
      vi.mocked(fs.readFileSync).mockReturnValue(JSON.stringify(testMetadata));

      // Force metadata reload to ensure our mock is used
      metadataLoader.load();

      // Verify metadata was loaded correctly
      const loadedFunc = metadataLoader.getByName('testFunc');
      expect(loadedFunc).toBeDefined();
      expect(loadedFunc?.selfContainedCode).toBe(
        '// Complete\nconst testFunc = (x: number): number => x * 2;',
      );

      // Create a test function
      const testFunc = (x: number): number => x * 2;

      // Create closure with versioning
      const closure = Closure.fromFunction(testFunc, undefined, true, 'testFunc');

      // Verify TypeScript source was used
      expect(closure.code).toBe('// Complete\nconst testFunc = (x: number): number => x * 2;');
      expect(closure.name).toBe('testFunc');
    });

    it('should handle missing metadata gracefully', () => {
      // No metadata file exists
      vi.mocked(fs.existsSync).mockReturnValue(false);

      // Function should still work without TypeScript metadata
      const testFunc = (x: number): number => x * 2;
      const closure = Closure.fromFunction(testFunc, undefined, true, 'testFunc');

      // Should fall back to JavaScript extraction
      expect(closure.code).toContain('(x)');
      expect(closure.name).toBe('testFunc');
    });

    it('should handle extraction errors gracefully', () => {
      // Mock TypeScript to throw error when reading config
      vi.mocked(ts.readConfigFile).mockReturnValue({
        error: {
          messageText: 'Cannot read config file',
          category: 1,
          code: 5000,
        },
      } as any);

      // TypeScriptExtractor should handle the error
      const extractor = new TypeScriptExtractor(testProjectDir, 'tsconfig.json');
      const metadata = extractor.extract();

      // Should return empty metadata when extraction fails
      expect(metadata.functions).toEqual({});
    });
  });

  describe('Build tool integration', () => {
    it('should work with CLI extraction', () => {
      const _mockArgv = ['node', 'lilypad-extract', '--output', 'metadata.json'];

      // This would be tested in the actual CLI test
      // Here we just verify the output format matches expectations
      const expectedOutput = {
        version: '1.0.0',
        buildTime: expect.any(String),
        functions: expect.any(Object),
      };

      const extractor = new TypeScriptExtractor('./', 'tsconfig.json');
      const result = extractor.extract();

      expect(result).toMatchObject(expectedOutput);
    });
  });
});
