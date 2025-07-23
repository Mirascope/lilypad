import { describe, it, expect, beforeEach, vi } from 'vitest';
import * as ts from 'typescript';
import * as fs from 'fs';
import * as path from 'path';
import { TypeScriptExtractor } from './typescript-extractor';

// Move mocks before imports
vi.mock('fs');
vi.mock('typescript', () => {
  const mocked = {
    readConfigFile: vi.fn(),
    parseJsonConfigFileContent: vi.fn(),
    createProgram: vi.fn(),
    createSourceFile: vi.fn((fileName: string, content: string, _target: any) => {
      // Simple mock implementation
      const statements: any[] = [];
      return {
        fileName,
        statements,
        getText: () => content,
        getFullText: () => content,
      };
    }),
    ScriptTarget: {
      ES2020: 7,
    },
    ModuleKind: {
      CommonJS: 1,
    },
    sys: {
      readFile: vi.fn(),
    },
    isCallExpression: (node: any) => node.kind === 'CallExpression',
    isIdentifier: (node: any) => node.kind === 'Identifier',
    isPropertyAccessExpression: (node: any) => node.kind === 'PropertyAccess',
    isStringLiteral: (node: any) => node.kind === 'StringLiteral',
    isObjectLiteralExpression: (node: any) => node.kind === 'ObjectLiteral',
    isPropertyAssignment: (node: any) => node.kind === 'PropertyAssignment',
    isVariableDeclaration: (node: any) => node.kind === 'VariableDeclaration',
    isArrowFunction: (node: any) => node.kind === 'ArrowFunction',
    isFunctionExpression: (node: any) => node.kind === 'FunctionExpression',
    forEachChild: (node: any, cb: any) => {
      if (node.children) {
        node.children.forEach(cb);
      }
    },
  };
  return {
    ...mocked,
    default: mocked,
  };
});

describe.skip('TypeScriptExtractor', () => {
  let extractor: TypeScriptExtractor;
  const mockRootDir = '/test/project';
  const mockTsConfigPath = 'tsconfig.json';

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock fs.existsSync
    vi.mocked(fs.existsSync).mockReturnValue(true);

    // Mock ts.readConfigFile
    vi.mocked(ts.readConfigFile).mockReturnValue({
      config: {
        compilerOptions: {
          target: 'es2020',
          module: 'commonjs',
        },
        include: ['src/**/*.ts'],
      },
    });

    // Mock ts.parseJsonConfigFileContent
    vi.mocked(ts.parseJsonConfigFileContent).mockReturnValue({
      options: {
        target: ts.ScriptTarget.ES2020,
        module: ts.ModuleKind.CommonJS,
      },
      fileNames: ['/test/project/src/index.ts'],
      errors: [],
    } as unknown as ts.ParsedCommandLine);
  });

  describe('constructor', () => {
    it('should initialize with valid tsconfig', () => {
      expect(() => {
        extractor = new TypeScriptExtractor(mockRootDir, mockTsConfigPath);
      }).not.toThrow();
    });

    it('should throw error if tsconfig does not exist', () => {
      vi.mocked(fs.existsSync).mockReturnValue(false);

      expect(() => {
        extractor = new TypeScriptExtractor(mockRootDir, mockTsConfigPath);
      }).toThrow(`tsconfig.json not found at ${path.join(mockRootDir, mockTsConfigPath)}`);
    });
  });

  describe('extract', () => {
    beforeEach(() => {
      // Create a mock source file
      const mockSourceFile = {
        fileName: '/test/project/src/index.ts',
        statements: [],
      } as unknown as ts.SourceFile;

      // Mock ts.createProgram
      const mockProgram = {
        getSourceFiles: vi.fn().mockReturnValue([mockSourceFile]),
      };
      vi.mocked(ts.createProgram).mockReturnValue(mockProgram as unknown as ts.Program);

      extractor = new TypeScriptExtractor(mockRootDir, mockTsConfigPath);
    });

    it('should extract metadata from source files', () => {
      const metadata = extractor.extract();

      expect(metadata).toEqual({
        version: '1.0.0',
        buildTime: expect.any(String),
        functions: {},
      });
    });

    it('should skip node_modules files', () => {
      const mockSourceFile = {
        fileName: '/test/project/node_modules/some-lib/index.ts',
        statements: [],
      } as unknown as ts.SourceFile;

      const mockProgram = {
        getSourceFiles: vi.fn().mockReturnValue([mockSourceFile]),
      };
      vi.mocked(ts.createProgram).mockReturnValue(mockProgram as unknown as ts.Program);

      extractor = new TypeScriptExtractor(mockRootDir, mockTsConfigPath);
      const metadata = extractor.extract();

      expect(metadata.functions).toEqual({});
    });
  });

  describe('extractFunction', () => {
    let mockSourceFile: ts.SourceFile;

    beforeEach(() => {
      mockSourceFile = ts.createSourceFile(
        'test.ts',
        `
        import { trace } from '@lilypad/typescript-sdk';
        
        const myFunc = trace(
          async (x: number) => x * 2,
          { versioning: 'automatic', name: 'myFunc' }
        );
        `,
        ts.ScriptTarget.ES2020,
        true,
      );

      const mockProgram = {
        getSourceFiles: vi.fn().mockReturnValue([mockSourceFile]),
      };
      vi.mocked(ts.createProgram).mockReturnValue(mockProgram as unknown as ts.Program);

      extractor = new TypeScriptExtractor(mockRootDir, mockTsConfigPath);
    });

    it('should extract function name from options', () => {
      const metadata = extractor.extract();
      const functions = Object.values(metadata.functions);

      expect(functions).toHaveLength(1);
      expect(functions[0].name).toBe('myFunc');
    });

    it('should extract function name from variable declaration if not in options', () => {
      mockSourceFile = ts.createSourceFile(
        'test.ts',
        `
        import { trace } from '@lilypad/typescript-sdk';
        
        const myFunc = trace(
          async (x: number) => x * 2,
          { versioning: 'automatic' }
        );
        `,
        ts.ScriptTarget.ES2020,
        true,
      );

      const mockProgram = {
        getSourceFiles: vi.fn().mockReturnValue([mockSourceFile]),
      };
      vi.mocked(ts.createProgram).mockReturnValue(mockProgram as unknown as ts.Program);

      extractor = new TypeScriptExtractor(mockRootDir, mockTsConfigPath);
      const metadata = extractor.extract();
      const functions = Object.values(metadata.functions);

      expect(functions).toHaveLength(1);
      expect(functions[0].name).toBe('myFunc');
    });

    it('should use "anonymous" if no name can be determined', () => {
      mockSourceFile = ts.createSourceFile(
        'test.ts',
        `
        import { trace } from '@lilypad/typescript-sdk';
        
        trace(
          async (x: number) => x * 2,
          { versioning: 'automatic' }
        );
        `,
        ts.ScriptTarget.ES2020,
        true,
      );

      const mockProgram = {
        getSourceFiles: vi.fn().mockReturnValue([mockSourceFile]),
      };
      vi.mocked(ts.createProgram).mockReturnValue(mockProgram as unknown as ts.Program);

      extractor = new TypeScriptExtractor(mockRootDir, mockTsConfigPath);
      const metadata = extractor.extract();
      const functions = Object.values(metadata.functions);

      expect(functions).toHaveLength(1);
      expect(functions[0].name).toBe('anonymous');
    });
  });

  describe('isVersionedFunction', () => {
    it('should detect versioned functions with automatic versioning', () => {
      const mockSourceFile = ts.createSourceFile(
        'test.ts',
        `
        trace(fn, { versioning: 'automatic' });
        trace(fn, { versioning: null });
        trace(fn);
        `,
        ts.ScriptTarget.ES2020,
        true,
      );

      const mockProgram = {
        getSourceFiles: vi.fn().mockReturnValue([mockSourceFile]),
      };
      vi.mocked(ts.createProgram).mockReturnValue(mockProgram as unknown as ts.Program);

      extractor = new TypeScriptExtractor(mockRootDir, mockTsConfigPath);
      const metadata = extractor.extract();

      // Only the first one should be extracted
      expect(Object.keys(metadata.functions)).toHaveLength(1);
    });
  });

  describe('findCorrespondingFunction', () => {
    it('should find function by content matching', () => {
      const sourceCode = `
      const fn1 = (x: number) => x * 2;
      const fn2 = (x: number) => x * 3;
      `;

      const mockSourceFile = ts.createSourceFile(
        'test.ts',
        sourceCode,
        ts.ScriptTarget.ES2020,
        true,
      );

      const mockProgram = {
        getSourceFiles: vi.fn().mockReturnValue([mockSourceFile]),
      };
      vi.mocked(ts.createProgram).mockReturnValue(mockProgram as unknown as ts.Program);

      extractor = new TypeScriptExtractor(mockRootDir, mockTsConfigPath);

      // Access private method through any
      const findFunc = (extractor as any).findCorrespondingFunction.bind(extractor);

      const targetCode = '(x: number) => x * 3';
      const result = findFunc(mockSourceFile, targetCode, 0, 100);

      expect(result).toBeDefined();
      expect(result?.getText()).toContain('x * 3');
    });

    it('should use similarity scoring for fuzzy matching', () => {
      const sourceCode = `
      const fn = (x: number) => {
        return x * 2;
      };
      `;

      const mockSourceFile = ts.createSourceFile(
        'test.ts',
        sourceCode,
        ts.ScriptTarget.ES2020,
        true,
      );

      const mockProgram = {
        getSourceFiles: vi.fn().mockReturnValue([mockSourceFile]),
      };
      vi.mocked(ts.createProgram).mockReturnValue(mockProgram as unknown as ts.Program);

      extractor = new TypeScriptExtractor(mockRootDir, mockTsConfigPath);

      const findFunc = (extractor as any).findCorrespondingFunction.bind(extractor);

      // Slightly different formatting
      const targetCode = '(x:number)=>{return x*2;}';
      const result = findFunc(mockSourceFile, targetCode, 0, 100);

      expect(result).toBeDefined();
    });
  });
});
