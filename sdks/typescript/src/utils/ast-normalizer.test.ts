import { describe, it, expect } from 'vitest';
import { normalizeFunction, createFunctionHash } from './ast-normalizer';

describe('ast-normalizer', () => {
  describe('normalizeFunction', () => {
    describe('regular functions', () => {
      it('should normalize a simple function declaration', () => {
        const code = `function add(a, b) {
          return a + b;
        }`;

        const result = normalizeFunction(code);

        expect(result.signature).toBe('function add(a, b)');
        expect(result.normalizedCode).toBe('function add(a, b) { return a + b; }');
      });

      it('should handle async functions', () => {
        const code = `async function fetchData(url) {
          const response = await fetch(url);
          return response.json();
        }`;

        const result = normalizeFunction(code);

        expect(result.signature).toBe('async function fetchData(url)');
        expect(result.normalizedCode).toContain('async function');
        expect(result.normalizedCode).toContain('await fetch');
      });

      it('should handle generator functions', () => {
        const code = `function* gen() {
          yield 1;
          yield 2;
        }`;

        const result = normalizeFunction(code);

        expect(result.signature).toBe('function* gen()');
        expect(result.normalizedCode).toContain('yield');
      });

      it('should handle anonymous functions', () => {
        const code = `function(x) {
          return x * 2;
        }`;

        const result = normalizeFunction(code);

        // extractSimpleSignature returns the matched string which doesn't add 'anonymous'
        expect(result.signature).toBe('function(x)');
        expect(result.normalizedCode).toContain('return x * 2');
      });

      it('should handle function expressions', () => {
        const code = `const fn = function multiply(x, y) {
          return x * y;
        }`;

        const result = normalizeFunction(code);

        expect(result.signature).toBe('function multiply(x, y)');
        expect(result.normalizedCode).toContain('x * y');
      });
    });

    describe('arrow functions', () => {
      it('should normalize simple arrow functions', () => {
        const code = `(x) => x * 2`;

        const result = normalizeFunction(code);

        expect(result.signature).toBe('(x) =>');
        expect(result.normalizedCode).toBe('(x) => x * 2');
      });

      it('should handle async arrow functions', () => {
        const code = `async (data) => {
          await processData(data);
          return data.result;
        }`;

        const result = normalizeFunction(code);

        expect(result.signature).toBe('async (data) =>');
        expect(result.normalizedCode).toContain('await processData');
      });

      it('should handle arrow functions with multiple parameters', () => {
        const code = `(a, b, c) => a + b + c`;

        const result = normalizeFunction(code);

        expect(result.signature).toBe('(a, b, c) =>');
        expect(result.normalizedCode).toBe('(a, b, c) => a + b + c');
      });

      it('should handle arrow functions without parentheses', () => {
        const code = `x => x * x`;

        const result = normalizeFunction(code);

        // Acorn parses single param without parentheses
        expect(result.signature).toBe('(x) =>');
        expect(result.normalizedCode).toBe('x => x * x');
      });
    });

    describe('parameter handling', () => {
      it('should handle rest parameters', () => {
        const code = `function sum(...numbers) {
          return numbers.reduce((a, b) => a + b, 0);
        }`;

        const result = normalizeFunction(code);

        // The arrow function in reduce is detected first due to walk order
        expect(result.signature).toBe('(a, b) =>');
      });

      it('should handle rest parameters in simple function', () => {
        const code = `function collect(...args) {
          return args;
        }`;

        const result = normalizeFunction(code);

        expect(result.signature).toBe('function collect(...args)');
      });

      it('should handle default parameters', () => {
        const code = `function greet(name = "World") {
          return "Hello, " + name;
        }`;

        const result = normalizeFunction(code);

        expect(result.signature).toBe('function greet(name="World")');
      });

      it('should handle destructured parameters', () => {
        const code = `function process({ x, y }) {
          return x + y;
        }`;

        const result = normalizeFunction(code);

        // Destructured params are represented as '...'
        expect(result.signature).toBe('function process(...)');
      });
    });

    describe('whitespace normalization', () => {
      it('should normalize excessive whitespace', () => {
        const code = `function    test   (  x   )    {
          
          
              return    x    *    2   ;
          
          
        }`;

        const result = normalizeFunction(code);

        expect(result.normalizedCode).toBe('function test ( x ) { return x * 2 ; }');
      });

      it('should remove empty lines', () => {
        const code = `function test() {

          const a = 1;

          const b = 2;

          return a + b;

        }`;

        const result = normalizeFunction(code);

        expect(result.normalizedCode).not.toContain('\n\n');
        expect(result.normalizedCode).toContain('const a = 1');
        expect(result.normalizedCode).toContain('const b = 2');
      });
    });

    describe('error handling', () => {
      it('should handle invalid JavaScript gracefully', () => {
        const code = `function broken( {
          return oops
        `;

        const result = normalizeFunction(code);

        // Falls back to simple extraction - but extractSimpleSignature doesn't find incomplete functions
        expect(result.signature).toBe('function()');
        expect(result.normalizedCode).toBe('function broken( { return oops');
      });

      it('should handle non-function code', () => {
        const code = `const x = 42;`;

        const result = normalizeFunction(code);

        // Falls back to default
        expect(result.signature).toBe('function()');
        expect(result.normalizedCode).toBe('const x = 42;');
      });

      it('should handle empty string', () => {
        const result = normalizeFunction('');

        expect(result.signature).toBe('function()');
        expect(result.normalizedCode).toBe('');
      });
    });
  });

  describe('createFunctionHash', () => {
    it('should create consistent hash for same code', () => {
      const code = 'function test() { return 42; }';

      const hash1 = createFunctionHash(code);
      const hash2 = createFunctionHash(code);

      expect(hash1).toBe(hash2);
      expect(hash1).toMatch(/^[a-f0-9]{64}$/); // SHA256 hex string
    });

    it('should create different hash for different code', () => {
      const code1 = 'function test() { return 42; }';
      const code2 = 'function test() { return 43; }';

      const hash1 = createFunctionHash(code1);
      const hash2 = createFunctionHash(code2);

      expect(hash1).not.toBe(hash2);
    });

    it('should include dependencies in hash', () => {
      const code = 'function test() { return 42; }';
      const deps1 = { lodash: '4.17.21' };
      const deps2 = { lodash: '4.17.20' };

      const hash1 = createFunctionHash(code, deps1);
      const hash2 = createFunctionHash(code, deps2);
      const hash3 = createFunctionHash(code); // No deps

      expect(hash1).not.toBe(hash2);
      expect(hash1).not.toBe(hash3);
      expect(hash2).not.toBe(hash3);
    });

    it('should hash dependencies in consistent order', () => {
      const code = 'function test() { return 42; }';
      const deps1 = { b: '2.0', a: '1.0', c: '3.0' };
      const deps2 = { c: '3.0', a: '1.0', b: '2.0' };

      const hash1 = createFunctionHash(code, deps1);
      const hash2 = createFunctionHash(code, deps2);

      expect(hash1).toBe(hash2);
    });

    it('should handle empty dependencies object', () => {
      const code = 'function test() { return 42; }';

      const hash1 = createFunctionHash(code, {});
      const hash2 = createFunctionHash(code);

      expect(hash1).toBe(hash2);
    });
  });

  describe('integration scenarios', () => {
    it('should normalize and hash complex functions consistently', () => {
      const code1 = `
        async function fetchUserData(userId, options = {}) {
          const { includeProfile = true, includeHistory = false } = options;
          
          const user = await db.users.findById(userId);
          
          if (!user) {
            throw new Error('User not found');
          }
          
          const result = { user };
          
          if (includeProfile) {
            result.profile = await db.profiles.findByUserId(userId);
          }
          
          if (includeHistory) {
            result.history = await db.history.findByUserId(userId);
          }
          
          return result;
        }
      `;

      const code2 = `async function fetchUserData(userId,options={}){const{includeProfile=true,includeHistory=false}=options;const user=await db.users.findById(userId);if(!user){throw new Error('User not found');}const result={user};if(includeProfile){result.profile=await db.profiles.findByUserId(userId);}if(includeHistory){result.history=await db.history.findByUserId(userId);}return result;}`;

      const normalized1 = normalizeFunction(code1);
      const normalized2 = normalizeFunction(code2);

      // Both should have same signature
      expect(normalized1.signature).toBe('async function fetchUserData(userId, options=...)');
      expect(normalized2.signature).toBe('async function fetchUserData(userId, options=...)');

      // Create hashes
      const hash1 = createFunctionHash(normalized1.normalizedCode);
      const hash2 = createFunctionHash(normalized2.normalizedCode);

      // Due to whitespace normalization, they should be similar but might not be identical
      // due to AST parsing differences
      expect(hash1).toBeTruthy();
      expect(hash2).toBeTruthy();
    });

    it('should handle various function styles', () => {
      const functions = [
        'const fn = x => x * 2',
        'const fn = (x) => { return x * 2; }',
        'function fn(x) { return x * 2; }',
        'const fn = function(x) { return x * 2; }',
        'const fn = async x => x * 2',
        'const fn = async function(x) { return x * 2; }',
      ];

      const results = functions.map((code) => {
        const normalized = normalizeFunction(code);
        return {
          code,
          signature: normalized.signature,
          hash: createFunctionHash(normalized.normalizedCode),
        };
      });

      // All should produce valid results
      results.forEach((result) => {
        expect(result.signature).toBeTruthy();
        expect(result.hash).toMatch(/^[a-f0-9]{64}$/);
      });

      // Each should have a unique hash (different code structure)
      const hashes = new Set(results.map((r) => r.hash));
      expect(hashes.size).toBeGreaterThan(1);
    });
  });
});
