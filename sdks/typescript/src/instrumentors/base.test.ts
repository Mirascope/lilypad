import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BaseInstrumentor } from './base';

// Create a concrete implementation for testing
class TestInstrumentor extends BaseInstrumentor {
  instrumentCalled = false;
  uninstrumentCalled = false;

  getName(): string {
    return 'TestInstrumentor';
  }

  instrument(): void {
    this.instrumentCalled = true;
    this.isInstrumentedFlag = true;
  }

  uninstrument(): void {
    this.uninstrumentCalled = true;
    this.isInstrumentedFlag = false;
  }

  // Expose protected methods for testing
  testStoreOriginal(key: string, method: Function): void {
    this.storeOriginal(key, method);
  }

  testGetOriginal(key: string): Function | undefined {
    return this.getOriginal(key);
  }

  testClearOriginals(): void {
    this.clearOriginals();
  }

  testSafeWrap<T extends (...args: unknown[]) => unknown>(
    original: T,
    wrapper: (original: T, ...args: Parameters<T>) => ReturnType<T>,
  ): T {
    return this.safeWrap(original, wrapper);
  }
}

describe('BaseInstrumentor', () => {
  let instrumentor: TestInstrumentor;

  beforeEach(() => {
    instrumentor = new TestInstrumentor();
  });

  describe('isInstrumented', () => {
    it('should return false initially', () => {
      expect(instrumentor.isInstrumented()).toBe(false);
    });

    it('should return true after instrumentation', () => {
      instrumentor.instrument();
      expect(instrumentor.isInstrumented()).toBe(true);
    });

    it('should return false after uninstrumentation', () => {
      instrumentor.instrument();
      instrumentor.uninstrument();
      expect(instrumentor.isInstrumented()).toBe(false);
    });
  });

  describe('original method storage', () => {
    it('should store and retrieve original methods', () => {
      const method1 = () => 'method1';
      const method2 = () => 'method2';

      instrumentor.testStoreOriginal('method1', method1);
      instrumentor.testStoreOriginal('method2', method2);

      expect(instrumentor.testGetOriginal('method1')).toBe(method1);
      expect(instrumentor.testGetOriginal('method2')).toBe(method2);
    });

    it('should not overwrite existing stored methods', () => {
      const original = () => 'original';
      const replacement = () => 'replacement';

      instrumentor.testStoreOriginal('method', original);
      instrumentor.testStoreOriginal('method', replacement);

      expect(instrumentor.testGetOriginal('method')).toBe(original);
    });

    it('should return undefined for non-existent methods', () => {
      expect(instrumentor.testGetOriginal('nonexistent')).toBeUndefined();
    });

    it('should clear all stored methods', () => {
      const method1 = () => 'method1';
      const method2 = () => 'method2';

      instrumentor.testStoreOriginal('method1', method1);
      instrumentor.testStoreOriginal('method2', method2);

      instrumentor.testClearOriginals();

      expect(instrumentor.testGetOriginal('method1')).toBeUndefined();
      expect(instrumentor.testGetOriginal('method2')).toBeUndefined();
    });
  });

  describe('safeWrap', () => {
    it('should wrap function successfully', () => {
      const original = (x: number) => x * 2;
      const wrapper = (orig: typeof original, x: number) => orig(x) + 1;

      const wrapped = instrumentor.testSafeWrap(original, wrapper);

      expect(wrapped(5)).toBe(11); // (5 * 2) + 1
    });

    it('should handle wrapper errors gracefully', () => {
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
      const original = (x: number) => x * 2;
      const wrapper = () => {
        throw new Error('Wrapper error');
      };

      const wrapped = instrumentor.testSafeWrap(original, wrapper);

      expect(wrapped(5)).toBe(10); // Falls back to original
      expect(consoleError).toHaveBeenCalledWith(
        'Error in TestInstrumentor instrumentor:',
        expect.any(Error),
      );

      consoleError.mockRestore();
    });

    it('should preserve function parameters and return types', () => {
      const original = (a: string, b: number): string => `${a}-${b}`;
      const wrapper = (orig: typeof original, a: string, b: number) => {
        return orig(a.toUpperCase(), b * 2);
      };

      const wrapped = instrumentor.testSafeWrap(original, wrapper);

      expect(wrapped('hello', 5)).toBe('HELLO-10');
    });

    it('should handle async functions', async () => {
      const original = async (x: number) => x * 2;
      const wrapper = async (orig: typeof original, x: number) => {
        const result = await orig(x);
        return result + 1;
      };

      const wrapped = instrumentor.testSafeWrap(original, wrapper);

      expect(await wrapped(5)).toBe(11);
    });
  });

  describe('abstract methods', () => {
    it('should have getName method', () => {
      expect(instrumentor.getName()).toBe('TestInstrumentor');
    });

    it('should have instrument method', () => {
      expect(instrumentor.instrumentCalled).toBe(false);
      instrumentor.instrument();
      expect(instrumentor.instrumentCalled).toBe(true);
    });

    it('should have uninstrument method', () => {
      expect(instrumentor.uninstrumentCalled).toBe(false);
      instrumentor.uninstrument();
      expect(instrumentor.uninstrumentCalled).toBe(true);
    });
  });
});
