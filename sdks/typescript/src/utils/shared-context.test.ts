import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock modules
vi.mock('@opentelemetry/context-async-hooks', () => ({
  AsyncLocalStorageContextManager: vi.fn().mockImplementation(() => ({
    enable: vi.fn().mockReturnThis(),
  })),
}));

vi.mock('@opentelemetry/api', () => ({
  context: {
    setGlobalContextManager: vi.fn(),
  },
}));

vi.mock('./logger', () => ({
  logger: {
    debug: vi.fn(),
  },
}));

// Import mocked modules
import { AsyncLocalStorageContextManager } from '@opentelemetry/context-async-hooks';
import { context } from '@opentelemetry/api';
import { logger } from './logger';

describe('shared-context', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset the module to clear the singleton
    vi.resetModules();
  });

  describe('getOrCreateContextManager', () => {
    it('should create a new context manager on first call', async () => {
      // Re-import after module reset to get fresh singleton state
      const { getOrCreateContextManager } = await import('./shared-context');

      const contextManager = getOrCreateContextManager();

      expect(AsyncLocalStorageContextManager).toHaveBeenCalledTimes(1);
      expect(logger.debug).toHaveBeenCalledWith(
        'Creating new global AsyncLocalStorageContextManager',
      );
      expect(logger.debug).toHaveBeenCalledWith('Global context manager initialized and set');
      expect(context.setGlobalContextManager).toHaveBeenCalledTimes(1);
      expect(contextManager).toBeDefined();
    });

    it('should reuse existing context manager on subsequent calls', async () => {
      // Re-import after module reset
      const { getOrCreateContextManager } = await import('./shared-context');

      // First call creates the context manager
      const firstManager = getOrCreateContextManager();
      vi.clearAllMocks();

      // Second call should reuse
      const secondManager = getOrCreateContextManager();

      expect(AsyncLocalStorageContextManager).not.toHaveBeenCalled();
      expect(logger.debug).toHaveBeenCalledWith('Reusing existing global context manager');
      expect(context.setGlobalContextManager).not.toHaveBeenCalled();
      expect(secondManager).toBe(firstManager);
    });

    it('should enable the context manager', async () => {
      const { getOrCreateContextManager } = await import('./shared-context');

      const mockEnable = vi.fn().mockReturnThis();
      vi.mocked(AsyncLocalStorageContextManager).mockImplementation(
        () =>
          ({
            enable: mockEnable,
          }) as any,
      );

      getOrCreateContextManager();

      expect(mockEnable).toHaveBeenCalledTimes(1);
    });
  });

  describe('hasGlobalContextManager', () => {
    it('should return false when no context manager exists', async () => {
      const { hasGlobalContextManager } = await import('./shared-context');

      expect(hasGlobalContextManager()).toBe(false);
    });

    it('should return true after context manager is created', async () => {
      const { getOrCreateContextManager, hasGlobalContextManager } = await import(
        './shared-context'
      );

      getOrCreateContextManager();

      expect(hasGlobalContextManager()).toBe(true);
    });
  });

  describe('getGlobalContextManager', () => {
    it('should return null when no context manager exists', async () => {
      const { getGlobalContextManager } = await import('./shared-context');

      expect(getGlobalContextManager()).toBe(null);
    });

    it('should return the context manager after it is created', async () => {
      const { getOrCreateContextManager, getGlobalContextManager } = await import(
        './shared-context'
      );

      const createdManager = getOrCreateContextManager();
      const retrievedManager = getGlobalContextManager();

      expect(retrievedManager).toBe(createdManager);
      expect(retrievedManager).not.toBe(null);
    });
  });

  describe('singleton behavior', () => {
    it('should maintain singleton state across multiple imports', async () => {
      // First import and create context manager
      const module1 = await import('./shared-context');
      const manager1 = module1.getOrCreateContextManager();

      // Clear mocks but don't reset modules
      vi.clearAllMocks();

      // Second import should get the same instance
      const module2 = await import('./shared-context');
      const manager2 = module2.getOrCreateContextManager();

      expect(manager1).toBe(manager2);
      expect(AsyncLocalStorageContextManager).not.toHaveBeenCalled();
      expect(logger.debug).toHaveBeenCalledWith('Reusing existing global context manager');
    });
  });
});
