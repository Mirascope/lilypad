/**
 * Sandbox execution for versioned functions
 * Provides isolated execution environments for both Node.js and browser
 */

import { logger } from '../utils/logger';

export interface SandboxOptions {
  timeout?: number;
  memoryLimit?: number;
  dependencies?: Record<string, string>;
}

export interface SandboxResult {
  result: any;
  error?: Error;
  logs: string[];
  executionTime: number;
}

/**
 * Abstract base class for sandbox implementations
 */
export abstract class Sandbox {
  protected logs: string[] = [];
  
  abstract execute(
    code: string,
    args: any[],
    options?: SandboxOptions
  ): Promise<SandboxResult>;
  
  protected createConsoleProxy(): Console {
    const self = this;
    return new Proxy(console, {
      get(target, prop) {
        if (prop === 'log' || prop === 'info' || prop === 'warn' || prop === 'error') {
          return (...args: any[]) => {
            const message = args.map(arg => 
              typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
            ).join(' ');
            self.logs.push(`[${prop}] ${message}`);
          };
        }
        return target[prop as keyof Console];
      }
    });
  }
}

/**
 * Node.js sandbox using isolated-vm
 */
export class NodeSandbox extends Sandbox {
  async execute(
    code: string,
    args: any[],
    options: SandboxOptions = {}
  ): Promise<SandboxResult> {
    const startTime = Date.now();
    this.logs = [];
    
    try {
      // Dynamic import to avoid bundling issues
      const ivm = await import('isolated-vm');
      
      // Create isolate with memory limit
      const isolate = new ivm.default.Isolate({
        memoryLimit: options.memoryLimit || 128,
      });
      
      // Create context
      const context = await isolate.createContext();
      
      // Set up console
      await context.global.set('__logs', new ivm.default.ExternalCopy(this.logs).copyInto());
      await context.eval(`
        const console = {
          log: (...args) => __logs.push('[log] ' + args.join(' ')),
          info: (...args) => __logs.push('[info] ' + args.join(' ')),
          warn: (...args) => __logs.push('[warn] ' + args.join(' ')),
          error: (...args) => __logs.push('[error] ' + args.join(' ')),
        };
      `);
      
      // Inject dependencies
      if (options.dependencies) {
        for (const [name, version] of Object.entries(options.dependencies)) {
          // In a real implementation, we would:
          // 1. Download the dependency from npm
          // 2. Bundle it
          // 3. Inject it into the context
          logger.warn(`Dependency injection not implemented: ${name}@${version}`);
        }
      }
      
      // Prepare the code for execution
      const wrappedCode = `
        ${code}
        
        // Execute the function
        (async function() {
          try {
            const result = await __lilypadExecute(...__args);
            return { success: true, result };
          } catch (error) {
            return { success: false, error: error.message || String(error) };
          }
        })();
      `;
      
      // Compile and run the script
      const script = await isolate.compileScript(wrappedCode);
      
      // Pass arguments
      await context.global.set('__args', new ivm.default.ExternalCopy(args).copyInto());
      
      // Run with timeout
      const resultHandle = await script.run(context, {
        timeout: options.timeout || 30000,
      });
      
      // Get the result
      const executionResult = await resultHandle;
      
      if (executionResult.success) {
        return {
          result: executionResult.result,
          logs: this.logs,
          executionTime: Date.now() - startTime,
        };
      } else {
        throw new Error(executionResult.error);
      }
    } catch (error) {
      return {
        result: undefined,
        error: error as Error,
        logs: this.logs,
        executionTime: Date.now() - startTime,
      };
    }
  }
}

/**
 * Browser sandbox using QuickJS WASM
 */
export class BrowserSandbox extends Sandbox {
  async execute(
    code: string,
    args: any[],
    options: SandboxOptions = {}
  ): Promise<SandboxResult> {
    const startTime = Date.now();
    this.logs = [];
    
    try {
      // Dynamic import QuickJS WASM
      const { getQuickJS } = await import('quickjs-emscripten');
      const QuickJS = await getQuickJS();
      
      // Create VM
      const vm = QuickJS.newContext();
      
      // Set up console
      const consoleHandle = vm.newObject();
      
      const logFn = vm.newFunction('log', (...args) => {
        const nativeArgs = args.map(arg => vm.dump(arg));
        this.logs.push('[log] ' + nativeArgs.join(' '));
      });
      
      vm.setProp(consoleHandle, 'log', logFn);
      vm.setProp(consoleHandle, 'info', logFn);
      vm.setProp(consoleHandle, 'warn', logFn);
      vm.setProp(consoleHandle, 'error', logFn);
      
      vm.setProp(vm.global, 'console', consoleHandle);
      
      // Inject arguments
      const argsHandle = vm.newArray();
      args.forEach((arg, index) => {
        const argHandle = vm.newString(JSON.stringify(arg));
        vm.setProp(argsHandle, index, argHandle);
      });
      vm.setProp(vm.global, '__args', argsHandle);
      
      // Prepare and execute code
      const wrappedCode = `
        ${code}
        
        // Parse arguments
        const parsedArgs = [];
        for (let i = 0; i < __args.length; i++) {
          parsedArgs.push(JSON.parse(__args[i]));
        }
        
        // Execute function
        try {
          const result = __lilypadExecute(...parsedArgs);
          JSON.stringify({ success: true, result });
        } catch (error) {
          JSON.stringify({ success: false, error: error.message || String(error) });
        }
      `;
      
      const result = vm.evalCode(wrappedCode, 'lilypad-function.js', {
        shouldInterrupt: () => {
          return Date.now() - startTime > (options.timeout || 30000);
        },
      });
      
      if (result.error) {
        throw new Error(vm.dump(result.error));
      }
      
      // Parse result
      const resultJson = vm.dump(result.value);
      const executionResult = JSON.parse(resultJson);
      
      // Clean up
      result.value.dispose();
      vm.dispose();
      
      if (executionResult.success) {
        return {
          result: executionResult.result,
          logs: this.logs,
          executionTime: Date.now() - startTime,
        };
      } else {
        throw new Error(executionResult.error);
      }
    } catch (error) {
      return {
        result: undefined,
        error: error as Error,
        logs: this.logs,
        executionTime: Date.now() - startTime,
      };
    }
  }
}

/**
 * Mock sandbox for testing
 */
export class MockSandbox extends Sandbox {
  async execute(
    code: string,
    args: any[],
    options: SandboxOptions = {}
  ): Promise<SandboxResult> {
    const startTime = Date.now();
    this.logs = [];
    
    try {
      // For mock execution, we'll just return a simple result
      logger.info('Mock sandbox executing function with args:', args);
      this.logs.push('[log] Mock execution started');
      
      // Simulate async execution
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Return mock result based on function name in code
      let result: any = 'mock result';
      
      if (code.includes('add')) {
        result = args.reduce((sum, val) => sum + val, 0);
      } else if (code.includes('multiply')) {
        result = args.reduce((product, val) => product * val, 1);
      } else if (code.includes('concat')) {
        result = args.join('');
      }
      
      this.logs.push(`[log] Mock execution completed with result: ${result}`);
      
      return {
        result,
        logs: this.logs,
        executionTime: Date.now() - startTime,
      };
    } catch (error) {
      return {
        result: undefined,
        error: error as Error,
        logs: this.logs,
        executionTime: Date.now() - startTime,
      };
    }
  }
}

/**
 * Factory function to create appropriate sandbox
 */
export function createSandbox(options: { platform?: 'node' | 'browser' | 'mock' } = {}): Sandbox {
  const platform = options.platform || (typeof window !== 'undefined' ? 'browser' : 'node');
  
  // Check environment
  if (platform === 'browser') {
    // Browser environment
    return new BrowserSandbox();
  } else if (platform === 'mock' || process.env.NODE_ENV === 'test' || process.env.LILYPAD_MOCK_SANDBOX === 'true') {
    // Test environment or explicitly requested mock
    return new MockSandbox();
  } else {
    // Node.js environment - try NodeSandbox, fall back to WorkerSandbox
    try {
      // Test if isolated-vm can be loaded
      const ivm = require('isolated-vm');
      // Test if it actually works
      new ivm.Isolate({ memoryLimit: 8 });
      return new NodeSandbox();
    } catch (error) {
      logger.warn('isolated-vm not available, using WorkerSandbox for isolation');
      // Import WorkerSandbox dynamically to avoid circular dependencies
      const { WorkerSandbox } = require('./worker-sandbox');
      return new WorkerSandbox();
    }
  }
}