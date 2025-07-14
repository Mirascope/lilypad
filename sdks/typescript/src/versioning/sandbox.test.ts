import { describe, it, expect, vi, beforeEach } from 'vitest';
import { NodeSandbox, BrowserSandbox, MockSandbox, createSandbox } from './sandbox';

describe('sandbox', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.unstubAllEnvs();
  });

  describe('MockSandbox', () => {
    it('should execute and return mock result', async () => {
      const sandbox = new MockSandbox();
      const result = await sandbox.execute(
        'function add(a, b) { return a + b; }',
        [5, 3],
      );

      expect(result.result).toBe(8);
      expect(result.logs).toHaveLength(2);
      expect(result.logs[0]).toContain('Mock execution started');
      expect(result.logs[1]).toContain('Mock execution completed with result: 8');
      expect(result.executionTime).toBeGreaterThan(0);
    });

    it('should handle multiply function', async () => {
      const sandbox = new MockSandbox();
      const result = await sandbox.execute(
        'function multiply(a, b) { return a * b; }',
        [5, 3],
      );

      expect(result.result).toBe(15);
    });

    it('should handle concat function', async () => {
      const sandbox = new MockSandbox();
      const result = await sandbox.execute(
        'function concat(a, b) { return a + b; }',
        ['hello', 'world'],
      );

      expect(result.result).toBe('helloworld');
    });

    it('should return default mock result for unknown functions', async () => {
      const sandbox = new MockSandbox();
      const result = await sandbox.execute(
        'function unknown() { return "something"; }',
        [],
      );

      expect(result.result).toBe('mock result');
    });
  });

  describe('createSandbox', () => {
    it('should return MockSandbox in test environment', () => {
      vi.stubEnv('NODE_ENV', 'test');
      const sandbox = createSandbox();
      expect(sandbox).toBeInstanceOf(MockSandbox);
    });

    it('should return MockSandbox when LILYPAD_MOCK_SANDBOX is true', () => {
      vi.stubEnv('LILYPAD_MOCK_SANDBOX', 'true');
      const sandbox = createSandbox();
      expect(sandbox).toBeInstanceOf(MockSandbox);
    });

    it('should return BrowserSandbox in browser environment', () => {
      // Mock browser environment
      const originalWindow = global.window;
      global.window = {} as any;
      
      try {
        const sandbox = createSandbox();
        expect(sandbox).toBeInstanceOf(BrowserSandbox);
      } finally {
        // Clean up
        if (originalWindow === undefined) {
          delete (global as any).window;
        } else {
          global.window = originalWindow;
        }
      }
    });

    it('should return NodeSandbox in Node environment', () => {
      // Ensure we're not in test mode or browser
      vi.stubEnv('NODE_ENV', 'production');
      vi.stubEnv('LILYPAD_MOCK_SANDBOX', 'false');
      
      const sandbox = createSandbox();
      expect(sandbox).toBeInstanceOf(NodeSandbox);
    });
  });

  describe('NodeSandbox', () => {
    it('should be instantiable', () => {
      const sandbox = new NodeSandbox();
      expect(sandbox).toBeInstanceOf(NodeSandbox);
    });

    // Note: Full NodeSandbox tests would require mocking isolated-vm
    // which is complex due to its native bindings
  });

  describe('BrowserSandbox', () => {
    it('should be instantiable', () => {
      const sandbox = new BrowserSandbox();
      expect(sandbox).toBeInstanceOf(BrowserSandbox);
    });

    // Note: Full BrowserSandbox tests would require mocking quickjs-emscripten
    // which involves WASM modules
  });

  describe('Sandbox error handling', () => {
    it('should handle execution errors gracefully', async () => {
      const sandbox = new MockSandbox();
      
      // Test that the sandbox handles errors internally
      const result = await sandbox.execute(
        'function error() { throw new Error("Test error"); }',
        [],
      );
      
      // MockSandbox doesn't throw, it returns a result
      expect(result).toBeDefined();
      expect(result.result).toBeDefined();
      expect(result.executionTime).toBeGreaterThan(0);
    });
  });
});