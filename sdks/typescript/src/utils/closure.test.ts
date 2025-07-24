import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Closure, getCachedClosure, getQualifiedName } from './closure';
import { logger } from './logger';
import { formatCode } from './code-formatter';
import { getTypeScriptSource } from '../versioning/metadata-loader';

vi.mock('./logger', () => ({
  logger: {
    debug: vi.fn(),
  },
}));

vi.mock('./code-formatter', () => ({
  formatCode: vi.fn((code: string) => `formatted:${code}`),
}));

vi.mock('../versioning/metadata-loader', () => ({
  getTypeScriptSource: vi.fn(),
}));

describe('closure utilities', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getQualifiedName', () => {
    it('should return function name for named functions', () => {
      function namedFunction() {}
      expect(getQualifiedName(namedFunction)).toBe('namedFunction');
    });

    it('should return function name for arrow functions with names', () => {
      const namedArrow = () => {};
      Object.defineProperty(namedArrow, 'name', { value: 'namedArrow' });
      expect(getQualifiedName(namedArrow)).toBe('namedArrow');
    });

    it('should return "anonymous" for anonymous functions', () => {
      expect(getQualifiedName(() => {})).toBe('anonymous');
      expect(getQualifiedName(function () {})).toBe('anonymous');
    });
  });

  describe('Closure class', () => {
    describe('constructor', () => {
      it('should create closure with provided data', () => {
        const data = {
          name: 'testFunc',
          signature: 'function testFunc()',
          code: 'function testFunc() { return 42; }',
          hash: 'abc123',
          dependencies: { dep1: { version: '1.0.0' } },
        };

        const closure = new Closure(data);

        expect(closure.name).toBe(data.name);
        expect(closure.signature).toBe(data.signature);
        expect(closure.code).toBe(data.code);
        expect(closure.hash).toBe(data.hash);
        expect(closure.dependencies).toEqual(data.dependencies);
      });
    });

    describe('fromFunction', () => {
      it('should create closure from regular function', () => {
        function testFunc(x: number): number {
          return x * 2;
        }

        const closure = Closure.fromFunction(testFunc);

        expect(closure.name).toBe('testFunc');
        expect(closure.signature).toBe('function testFunc(x)');
        expect(closure.code).toContain('return x * 2');
        expect(closure.hash).toBeDefined();
        expect(closure.dependencies).toEqual({});
      });

      it('should create closure from arrow function', () => {
        const arrowFunc = (x: number) => x * 2;

        const closure = Closure.fromFunction(arrowFunc);

        expect(closure.name).toBe('arrowFunc');
        expect(closure.signature).toBe('(x)');
        expect(closure.code).toContain('x * 2');
      });

      it('should create closure from async function', () => {
        async function asyncFunc(): Promise<void> {
          await Promise.resolve();
        }

        const closure = Closure.fromFunction(asyncFunc);

        expect(closure.name).toBe('asyncFunc');
        expect(closure.signature).toBe('async function asyncFunc()');
        expect(closure.code).toContain('await');
      });

      it('should handle generator functions', () => {
        function* generatorFunc() {
          yield 1;
        }

        const closure = Closure.fromFunction(generatorFunc);

        expect(closure.name).toBe('generatorFunc');
        expect(closure.signature).toBe('function* generatorFunc()');
        expect(closure.code).toContain('yield');
      });

      it('should use custom function name when provided', () => {
        const fn = () => {};
        const closure = Closure.fromFunction(fn, undefined, false, 'customName');

        expect(closure.name).toBe('customName');
      });

      it('should include dependencies in hash calculation', () => {
        const fn = () => {};
        const deps1 = { dep1: { version: '1.0.0' } };
        const deps2 = { dep1: { version: '2.0.0' } };

        const closure1 = Closure.fromFunction(fn, deps1);
        const closure2 = Closure.fromFunction(fn, deps2);

        expect(closure1.hash).not.toBe(closure2.hash);
      });

      describe('versioned functions', () => {
        it('should use TypeScript source when available', () => {
          const tsSource = `function testFunc(x: number): number {
  return x * 2;
}`;
          vi.mocked(getTypeScriptSource).mockReturnValue(tsSource);

          const fn = function testFunc(x: number) {
            return x * 2;
          };
          const closure = Closure.fromFunction(fn, undefined, true);

          expect(getTypeScriptSource).toHaveBeenCalledWith('', 'testFunc');
          expect(closure.code).toBe(tsSource);
          expect(logger.debug).toHaveBeenCalledWith(
            expect.stringContaining('✅ Using TypeScript source'),
          );
        });

        it('should fall back to formatted JavaScript when TypeScript source not found', () => {
          vi.mocked(getTypeScriptSource).mockReturnValue(null);
          vi.mocked(formatCode).mockReturnValue('formatted code');

          const fn = function testFunc() {};
          const closure = Closure.fromFunction(fn, undefined, true);

          expect(closure.code).toBe('formatted code');
          expect(formatCode).toHaveBeenCalled();
          expect(logger.debug).toHaveBeenCalledWith(
            expect.stringContaining('⚠️ TypeScript source not found'),
          );
        });
      });

      describe('hash generation', () => {
        it('should generate consistent hash for same function', () => {
          const fn = () => 'test';
          const closure1 = Closure.fromFunction(fn);
          const closure2 = Closure.fromFunction(fn);

          expect(closure1.hash).toBe(closure2.hash);
        });

        it('should generate different hash for different functions', () => {
          const fn1 = () => 'test1';
          const fn2 = () => 'test2';

          const closure1 = Closure.fromFunction(fn1);
          const closure2 = Closure.fromFunction(fn2);

          expect(closure1.hash).not.toBe(closure2.hash);
        });
      });
    });
  });

  describe('getCachedClosure', () => {
    it('should cache closures for non-versioned functions', () => {
      const fn = () => {};

      const closure1 = getCachedClosure(fn);
      const closure2 = getCachedClosure(fn);

      expect(closure1).toBe(closure2); // Same instance
    });

    it('should not cache versioned functions', () => {
      const fn = () => {};
      vi.mocked(getTypeScriptSource).mockReturnValue(null);

      const closure1 = getCachedClosure(fn, undefined, true);
      const closure2 = getCachedClosure(fn, undefined, true);

      expect(closure1).not.toBe(closure2); // Different instances
      expect(logger.debug).toHaveBeenCalledWith(
        expect.stringContaining('Creating versioned closure'),
      );
    });

    it('should create new closure when dependencies are provided', () => {
      const fn = () => {};
      const deps = { dep1: { version: '1.0.0' } };

      const closure1 = getCachedClosure(fn);
      const closure2 = getCachedClosure(fn, deps);

      expect(closure1).not.toBe(closure2);
      expect(closure2.dependencies).toEqual(deps);
    });

    it('should detect TypeScript source usage', () => {
      const tsSource = `interface User {
  name: string;
}
function getUser(): Promise<User> {
  return Promise.resolve({ name: 'test' });
}`;
      vi.mocked(getTypeScriptSource).mockReturnValue(tsSource);

      const fn = () => {};
      getCachedClosure(fn, undefined, true, 'getUser');

      expect(logger.debug).toHaveBeenCalledWith(expect.stringContaining('TypeScript source USED'));
    });

    it('should detect when TypeScript source not used', () => {
      vi.mocked(getTypeScriptSource).mockReturnValue(null);
      vi.mocked(formatCode).mockReturnValue('function test() {}');

      const fn = () => {};
      getCachedClosure(fn, undefined, true, 'test');

      expect(logger.debug).toHaveBeenCalledWith(
        expect.stringContaining('TypeScript source NOT USED'),
      );
    });

    it('should pass function name to Closure.fromFunction', () => {
      const fn = () => {};
      const spy = vi.spyOn(Closure, 'fromFunction');

      getCachedClosure(fn, undefined, false, 'customFunc');

      expect(spy).toHaveBeenCalledWith(fn, undefined, false, 'customFunc');
      spy.mockRestore();
    });
  });

  describe('function signature extraction', () => {
    it('should extract signature from regular functions', () => {
      const tests = [
        { fn: function test() {}, expected: 'function test()' },
        { fn: function test(_a: number) {}, expected: 'function test(_a)' },
        { fn: function test(_a: number, _b: string) {}, expected: 'function test(_a, _b)' },
      ];

      tests.forEach(({ fn, expected }) => {
        const closure = Closure.fromFunction(fn);
        expect(closure.signature).toBe(expected);
      });
    });

    it('should extract signature from arrow functions', () => {
      const tests = [
        { fn: () => {}, expected: '()' },
        { fn: (_a: number) => _a, expected: '(_a)' },
        { fn: (_a: number, _b: string) => _a, expected: '(_a, _b)' },
      ];

      tests.forEach(({ fn, expected }) => {
        const closure = Closure.fromFunction(fn);
        expect(closure.signature).toBe(expected);
      });
    });

    it('should extract signature from async functions', () => {
      const tests = [
        { fn: async () => {}, expected: 'async ()' },
        { fn: async function test() {}, expected: 'async function test()' },
        { fn: async (a: number) => a, expected: 'async (a)' },
      ];

      tests.forEach(({ fn, expected }) => {
        const closure = Closure.fromFunction(fn);
        expect(closure.signature).toBe(expected);
      });
    });

    it('should handle functions without clear signature', () => {
      // Create a function with a non-standard toString
      const fn = () => {};
      Object.defineProperty(fn, 'toString', {
        value: () => 'weird function representation',
      });

      const closure = Closure.fromFunction(fn);
      expect(closure.signature).toBe('function()');
    });
  });
});
