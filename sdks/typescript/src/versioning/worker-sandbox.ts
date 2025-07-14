/**
 * Worker-based sandbox using Node.js child processes for true isolation
 */

import { fork } from 'child_process';
import { writeFile, unlink } from 'fs/promises';
import { tmpdir } from 'os';
import { join } from 'path';
import { logger } from '../utils/logger';
import type { Sandbox, SandboxOptions, SandboxResult } from './sandbox';

export class WorkerSandbox implements Sandbox {
  protected logs: string[] = [];

  async execute(
    code: string,
    args: any[],
    options: SandboxOptions = {}
  ): Promise<SandboxResult> {
    const startTime = Date.now();
    this.logs = [];
    
    // Create a temporary file for the worker code
    const tempFile = join(tmpdir(), `lilypad-worker-${Date.now()}.js`);
    
    try {
      logger.info('WorkerSandbox executing function');
      
      // Create worker code
      const workerCode = `
        const logs = [];
        const console = {
          log: (...args) => logs.push(['log', args.join(' ')]),
          info: (...args) => logs.push(['info', args.join(' ')]),
          warn: (...args) => logs.push(['warn', args.join(' ')]),
          error: (...args) => logs.push(['error', args.join(' ')]),
        };
        
        // Listen for messages from parent
        process.on('message', async (message) => {
          const { code, args, dependencies } = message;
          
          try {
            // Mock Lilypad functions
            const logToCurrentSpan = (...args) => {
              console.log('[logToCurrentSpan]', ...args);
            };
            
            const getCurrentSpan = () => {
              return {
                setAttribute: (key, value) => {
                  console.log('[getCurrentSpan.setAttribute]', key, value);
                }
              };
            };
            
            // Inject dependencies as variables for now
            // A full implementation would install packages in a temporary directory
            const deps = dependencies || {};
            
            
            // Execute the function
            let fn;
            try {
              // Try to evaluate the code
              fn = eval(code);
            } catch (evalError) {
              // If eval fails, try wrapping in parentheses (for function expressions)
              console.log('[Worker] Direct eval failed, trying wrapped:', evalError.message);
              fn = eval(\`(\${code})\`);
            }
            
            if (typeof fn !== 'function') {
              throw new Error(\`Evaluated code is not a function, got \${typeof fn}\`);
            }
            
            const result = await fn(...args);
            
            // Send result back
            process.send({
              success: true,
              result,
              logs,
            });
          } catch (error) {
            process.send({
              success: false,
              error: error.message || String(error),
              logs,
            });
          }
        });
        
        // Timeout handler
        setTimeout(() => {
          process.send({
            success: false,
            error: 'Execution timeout',
            logs,
          });
          process.exit(1);
        }, ${options.timeout || 30000});
      `;
      
      // Write worker code to temp file
      await writeFile(tempFile, workerCode, 'utf-8');
      
      // Fork the worker process
      const worker = fork(tempFile, [], {
        silent: true,
        execArgv: ['--no-warnings'],
      });
      
      // Handle worker output
      worker.stdout?.on('data', (data) => {
        const output = data.toString().trim();
        this.logs.push(`[stdout] ${output}`);
      });
      
      worker.stderr?.on('data', (data) => {
        const output = data.toString().trim();
        this.logs.push(`[stderr] ${output}`);
      });
      
      // Send execution message
      const executionPromise = new Promise<SandboxResult>((resolve, reject) => {
        worker.on('message', (message: any) => {
          worker.kill();
          
          // Process logs
          if (message.logs) {
            for (const [level, content] of message.logs) {
              this.logs.push(`[${level}] ${content}`);
            }
          }
          
          if (message.success) {
            resolve({
              result: message.result,
              logs: this.logs,
              executionTime: Date.now() - startTime,
            });
          } else {
            resolve({
              result: undefined,
              error: new Error(message.error),
              logs: this.logs,
              executionTime: Date.now() - startTime,
            });
          }
        });
        
        worker.on('error', (error) => {
          worker.kill();
          reject(error);
        });
        
        worker.on('exit', (code) => {
          if (code !== 0 && code !== null) {
            reject(new Error(`Worker exited with code ${code}`));
          }
        });
        
        // Send the code and arguments
        worker.send({
          code,
          args,
          dependencies: options.dependencies,
        });
      });
      
      // Execute with timeout
      const result = await executionPromise;
      
      // Clean up temp file
      await unlink(tempFile).catch(() => {});
      
      return result;
    } catch (error) {
      // Clean up temp file on error
      await unlink(tempFile).catch(() => {});
      
      return {
        result: undefined,
        error: error as Error,
        logs: this.logs,
        executionTime: Date.now() - startTime,
      };
    }
  }
}