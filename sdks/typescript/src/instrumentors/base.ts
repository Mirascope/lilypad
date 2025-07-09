import type { InstrumentorBase } from '../types';

/**
 * Base class for all instrumentors
 */
export abstract class BaseInstrumentor implements InstrumentorBase {
  protected isInstrumentedFlag = false;
  protected originalMethods = new Map<string, Function>();

  abstract getName(): string;
  abstract instrument(): void;
  abstract uninstrument(): void;

  isInstrumented(): boolean {
    return this.isInstrumentedFlag;
  }

  /**
   * Store original method for later restoration
   */
  protected storeOriginal(key: string, method: Function): void {
    if (!this.originalMethods.has(key)) {
      this.originalMethods.set(key, method);
    }
  }

  /**
   * Get stored original method
   */
  protected getOriginal(key: string): Function | undefined {
    return this.originalMethods.get(key);
  }

  /**
   * Clear all stored methods
   */
  protected clearOriginals(): void {
    this.originalMethods.clear();
  }

  /**
   * Safely wrap a method with error handling
   */
  protected safeWrap<T extends (...args: unknown[]) => unknown>(
    original: T,
    wrapper: (original: T, ...args: Parameters<T>) => ReturnType<T>,
  ): T {
    return ((...args: Parameters<T>) => {
      try {
        return wrapper(original, ...args);
      } catch (error) {
        console.error(`Error in ${this.getName()} instrumentor:`, error);
        // Fall back to original method
        return original(...args);
      }
    }) as T;
  }
}
