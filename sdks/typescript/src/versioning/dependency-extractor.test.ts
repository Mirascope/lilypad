import { describe, it, expect, beforeEach } from 'vitest';
import { Project, ArrowFunction, FunctionExpression } from 'ts-morph';
import { DependencyExtractor } from './dependency-extractor';

describe('DependencyExtractor', () => {
  let project: Project;
  let extractor: DependencyExtractor;

  beforeEach(() => {
    project = new Project({
      useInMemoryFileSystem: true,
      compilerOptions: {
        target: 16, // ES2020
        module: 1, // CommonJS
      },
    });

    // Create a custom extractor that accepts the project directly
    class TestDependencyExtractor extends DependencyExtractor {
      constructor(testProject: Project) {
        // Call parent with dummy path
        super('./tsconfig.json');
        // Override the project
        this.project = testProject;
      }
    }

    extractor = new TestDependencyExtractor(project);
  });

  describe('extractFunctionWithDependencies', () => {
    it('should extract function with type dependencies', () => {
      const sourceFile = project.createSourceFile(
        'test.ts',
        `
        interface User {
          name: string;
          age: number;
        }
        
        function greet(user: User): string {
          return 'Hello ' + user.name;
        }
        `,
      );

      const greetFunc = sourceFile.getFunction('greet')!;
      const result = extractor.extractFunctionWithDependencies(sourceFile, greetFunc);

      expect(result.name).toBe('greet');
      expect(result.dependencies).toHaveLength(1);
      expect(result.dependencies[0]).toMatchObject({
        name: 'User',
        type: 'interface',
      });
      expect(result.selfContainedCode).toContain('interface User');
      expect(result.selfContainedCode).toContain('function greet');
    });

    it('should extract function with constant dependencies', () => {
      const sourceFile = project.createSourceFile(
        'test.ts',
        `
        const TAX_RATE = 0.08;
        const DISCOUNT = 0.15;
        
        function calculateTotal(price: number): number {
          return price * (1 + TAX_RATE) * (1 - DISCOUNT);
        }
        `,
      );

      const func = sourceFile.getFunction('calculateTotal')!;
      const result = extractor.extractFunctionWithDependencies(sourceFile, func);

      expect(result.dependencies.map((d) => d.name)).toContain('TAX_RATE');
      expect(result.dependencies.map((d) => d.name)).toContain('DISCOUNT');
      expect(result.selfContainedCode).toContain('const TAX_RATE = 0.08');
      expect(result.selfContainedCode).toContain('const DISCOUNT = 0.15');
    });

    it('should extract function with function dependencies', () => {
      const sourceFile = project.createSourceFile(
        'test.ts',
        `
        function formatCurrency(amount: number): string {
          return '$' + amount.toFixed(2);
        }
        
        function displayPrice(price: number): string {
          return 'Price: ' + formatCurrency(price);
        }
        `,
      );

      const func = sourceFile.getFunction('displayPrice')!;
      const result = extractor.extractFunctionWithDependencies(sourceFile, func);

      expect(result.dependencies).toHaveLength(1);
      expect(result.dependencies[0]).toMatchObject({
        name: 'formatCurrency',
        type: 'function',
      });
      expect(result.selfContainedCode).toContain('function formatCurrency');
    });

    it('should extract function with class dependencies', () => {
      const sourceFile = project.createSourceFile(
        'test.ts',
        `
        class Calculator {
          add(a: number, b: number): number {
            return a + b;
          }
        }
        
        function compute(): number {
          const calc = new Calculator();
          return calc.add(1, 2);
        }
        `,
      );

      const func = sourceFile.getFunction('compute')!;
      const result = extractor.extractFunctionWithDependencies(sourceFile, func);

      expect(result.dependencies).toHaveLength(1);
      expect(result.dependencies[0]).toMatchObject({
        name: 'Calculator',
        type: 'class',
      });
      expect(result.selfContainedCode).toContain('class Calculator');
    });

    it('should extract function with enum dependencies', () => {
      const sourceFile = project.createSourceFile(
        'test.ts',
        `
        enum Status {
          Active = 'ACTIVE',
          Inactive = 'INACTIVE',
        }
        
        function isActive(status: Status): boolean {
          return status === Status.Active;
        }
        `,
      );

      const func = sourceFile.getFunction('isActive')!;
      const result = extractor.extractFunctionWithDependencies(sourceFile, func);

      expect(result.dependencies).toHaveLength(1);
      expect(result.dependencies[0]).toMatchObject({
        name: 'Status',
        type: 'enum',
      });
      expect(result.selfContainedCode).toContain('enum Status');
    });

    it('should extract function with type alias dependencies', () => {
      const sourceFile = project.createSourceFile(
        'test.ts',
        `
        type UserId = string;
        type UserMap = Record<UserId, string>;
        
        function getUser(map: UserMap, id: UserId): string | undefined {
          return map[id];
        }
        `,
      );

      const func = sourceFile.getFunction('getUser')!;
      const result = extractor.extractFunctionWithDependencies(sourceFile, func);

      expect(result.dependencies.map((d) => d.name)).toContain('UserMap');
      expect(result.dependencies.map((d) => d.name)).toContain('UserId');
      expect(result.selfContainedCode).toContain('type UserId = string');
      expect(result.selfContainedCode).toContain('type UserMap = Record<UserId, string>');
    });

    it('should handle recursive dependencies', () => {
      const sourceFile = project.createSourceFile(
        'test.ts',
        `
        const BASE_RATE = 0.05;
        const PREMIUM_RATE = 0.15;
        
        function getRate(isPremium: boolean): number {
          return isPremium ? PREMIUM_RATE : BASE_RATE;
        }
        
        function calculateInterest(amount: number, isPremium: boolean): number {
          const rate = getRate(isPremium);
          return amount * rate;
        }
        `,
      );

      const func = sourceFile.getFunction('calculateInterest')!;
      const result = extractor.extractFunctionWithDependencies(sourceFile, func);

      // Should extract getRate, BASE_RATE, and PREMIUM_RATE
      const depNames = result.dependencies.map((d) => d.name);
      expect(depNames).toContain('getRate');
      expect(depNames).toContain('BASE_RATE');
      expect(depNames).toContain('PREMIUM_RATE');
    });

    it('should handle imported dependencies', () => {
      // Create a module file
      project.createSourceFile(
        'utils.ts',
        `
        export function helper(x: number): number {
          return x * 2;
        }
        
        export const CONSTANT = 42;
        `,
      );

      const sourceFile = project.createSourceFile(
        'test.ts',
        `
        import { helper, CONSTANT } from './utils';
        
        function useImported(x: number): number {
          return helper(x) + CONSTANT;
        }
        `,
      );

      const func = sourceFile.getFunction('useImported')!;
      const result = extractor.extractFunctionWithDependencies(sourceFile, func);

      expect(result.dependencies.map((d) => d.name)).toContain('helper');
      expect(result.dependencies.map((d) => d.name)).toContain('CONSTANT');
    });

    it('should handle external module imports', () => {
      const sourceFile = project.createSourceFile(
        'test.ts',
        `
        import { readFile } from 'fs';
        
        async function loadData(path: string): Promise<string> {
          return readFile(path, 'utf-8');
        }
        `,
      );

      const func = sourceFile.getFunction('loadData')!;
      const result = extractor.extractFunctionWithDependencies(sourceFile, func);

      expect(result.dependencies).toHaveLength(1);
      expect(result.dependencies[0]).toMatchObject({
        name: 'readFile',
        type: 'import',
        source: 'fs',
      });
      expect(result.imports).toContain("import { readFile } from 'fs';");
    });

    it('should ignore built-in types and globals', () => {
      const sourceFile = project.createSourceFile(
        'test.ts',
        `
        function processArray(arr: Array<string>): number {
          console.log('Processing...');
          return arr.length;
        }
        `,
      );

      const func = sourceFile.getFunction('processArray')!;
      const result = extractor.extractFunctionWithDependencies(sourceFile, func);

      // Should not include Array, console, etc.
      expect(result.dependencies).toHaveLength(0);
    });

    it('should handle generic types', () => {
      const sourceFile = project.createSourceFile(
        'test.ts',
        `
        interface Container<T> {
          value: T;
        }
        
        function getValue<T>(container: Container<T>): T {
          return container.value;
        }
        `,
      );

      const func = sourceFile.getFunction('getValue')!;
      const result = extractor.extractFunctionWithDependencies(sourceFile, func);

      expect(result.dependencies).toHaveLength(1);
      expect(result.dependencies[0]).toMatchObject({
        name: 'Container',
        type: 'interface',
      });
    });

    it('should not include parameter names as dependencies', () => {
      const sourceFile = project.createSourceFile(
        'test.ts',
        `
        function greet(name: string, age: number): string {
          return name + ' is ' + age + ' years old';
        }
        `,
      );

      const func = sourceFile.getFunction('greet')!;
      const result = extractor.extractFunctionWithDependencies(sourceFile, func);

      // Should not include 'name' or 'age' as dependencies
      expect(result.dependencies).toHaveLength(0);
    });

    it('should generate complete self-contained code', () => {
      const sourceFile = project.createSourceFile(
        'test.ts',
        `
        interface User {
          name: string;
          age: number;
        }
        
        const GREETING = 'Hello';
        
        function formatUser(user: User): string {
          return user.name + ' (' + user.age + ')';
        }
        
        function greet(user: User): string {
          return GREETING + ' ' + formatUser(user);
        }
        `,
      );

      const func = sourceFile.getFunction('greet')!;
      const result = extractor.extractFunctionWithDependencies(sourceFile, func);

      expect(result.selfContainedCode).toContain('// Type dependencies');
      expect(result.selfContainedCode).toContain('interface User');
      expect(result.selfContainedCode).toContain('// Variable and class dependencies');
      expect(result.selfContainedCode).toContain('const GREETING');
      expect(result.selfContainedCode).toContain('// Function dependencies');
      expect(result.selfContainedCode).toContain('function formatUser');
      expect(result.selfContainedCode).toContain('// Main function');
      expect(result.selfContainedCode).toContain('function greet');
    });

    it('should handle arrow functions', () => {
      const sourceFile = project.createSourceFile(
        'test.ts',
        `
        const TAX_RATE = 0.08;
        
        const calculateTax = (amount: number): number => {
          return amount * TAX_RATE;
        };
        `,
      );

      const func = sourceFile
        .getVariableDeclaration('calculateTax')!
        .getInitializer()! as ArrowFunction;
      const result = extractor.extractFunctionWithDependencies(sourceFile, func);

      expect(result.name).toBe('calculateTax');
      expect(result.dependencies).toHaveLength(1);
      expect(result.dependencies[0].name).toBe('TAX_RATE');
    });

    it('should handle function expressions', () => {
      const sourceFile = project.createSourceFile(
        'test.ts',
        `
        const FACTOR = 2;
        
        const double = function(x: number): number {
          return x * FACTOR;
        };
        `,
      );

      const func = sourceFile
        .getVariableDeclaration('double')!
        .getInitializer()! as FunctionExpression;
      const result = extractor.extractFunctionWithDependencies(sourceFile, func);

      expect(result.name).toBe('double');
      expect(result.dependencies).toHaveLength(1);
      expect(result.dependencies[0].name).toBe('FACTOR');
    });
  });
});
