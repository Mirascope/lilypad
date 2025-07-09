import { describe, it, expect, beforeEach, vi } from 'vitest';
import * as settings from './utils/settings';
import { getProvider } from './configure';

vi.mock('./utils/settings');
vi.mock('./utils/logger');
vi.mock('./configure', () => ({
  getProvider: vi.fn(),
}));

describe('shutdown', () => {
  const mockSetSettings = vi.mocked(settings.setSettings);
  const mockIsConfigured = vi.mocked(settings.isConfigured);
  const mockGetProvider = vi.mocked(getProvider);
  const mockTracerProvider = {
    shutdown: vi.fn(),
    forceFlush: vi.fn(),
  };

  beforeEach(async () => {
    vi.clearAllMocks();
    // Reset modules to clear module-level state
    vi.resetModules();

    // Re-mock after module reset
    vi.mock('./utils/settings');
    vi.mock('./configure', () => ({
      getProvider: vi.fn(),
    }));

    mockIsConfigured.mockReturnValue(false);
    mockTracerProvider.shutdown.mockResolvedValue(undefined);
    mockTracerProvider.forceFlush.mockResolvedValue(undefined);
    mockGetProvider.mockReturnValue(null);
  });

  describe('isSDKShuttingDown', () => {
    it('should return false initially', async () => {
      const { isSDKShuttingDown } = await import('./shutdown');
      expect(isSDKShuttingDown()).toBe(false);
    });
  });

  describe('shutdown function', () => {
    it('should do nothing if SDK is not configured', async () => {
      const { shutdown } = await import('./shutdown');

      mockIsConfigured.mockReturnValue(false);

      await shutdown();

      expect(mockTracerProvider.shutdown).not.toHaveBeenCalled();
      // setSettings(null) is always called in finally block
      expect(mockSetSettings).toHaveBeenCalledWith(null);
    });

    it('should shutdown tracer provider if configured', async () => {
      const { shutdown } = await import('./shutdown');

      mockIsConfigured.mockReturnValue(true);
      mockGetProvider.mockReturnValue(mockTracerProvider as any);

      await shutdown();

      expect(mockTracerProvider.forceFlush).toHaveBeenCalled();
      expect(mockTracerProvider.shutdown).toHaveBeenCalled();
      expect(mockSetSettings).toHaveBeenCalledWith(null);
    });

    it('should handle tracer provider without shutdown method', async () => {
      const { shutdown } = await import('./shutdown');

      mockIsConfigured.mockReturnValue(true);
      const providerWithoutShutdown = {};
      mockGetProvider.mockReturnValue(providerWithoutShutdown as any);

      await expect(shutdown()).resolves.toBeUndefined();
      expect(mockSetSettings).toHaveBeenCalledWith(null);
    });

    it('should handle errors during shutdown', async () => {
      const { shutdown } = await import('./shutdown');

      mockIsConfigured.mockReturnValue(true);
      const error = new Error('Shutdown failed');
      mockTracerProvider.shutdown.mockRejectedValueOnce(error);
      mockGetProvider.mockReturnValue(mockTracerProvider as any);

      // Should not throw
      await expect(shutdown()).resolves.toBeUndefined();
      expect(mockSetSettings).toHaveBeenCalledWith(null);
    });

    it('should log warning when no tracer provider found', async () => {
      const { shutdown } = await import('./shutdown');
      const { logger } = await import('./utils/logger');
      const mockLogger = vi.mocked(logger);

      mockIsConfigured.mockReturnValue(true);
      mockGetProvider.mockReturnValue(null);

      await shutdown();

      expect(mockLogger.warn).toHaveBeenCalledWith('No tracer provider found to shutdown.');
      expect(mockSetSettings).toHaveBeenCalledWith(null);
    });

    it('should prevent multiple simultaneous shutdowns', async () => {
      const { shutdown } = await import('./shutdown');

      mockIsConfigured.mockReturnValue(true);
      mockGetProvider.mockReturnValue(mockTracerProvider as any);

      // Track how many times forceFlush and shutdown are called
      let forceFlushCallCount = 0;
      let shutdownCallCount = 0;

      mockTracerProvider.forceFlush.mockImplementation(() => {
        forceFlushCallCount++;
        return new Promise((resolve) => setTimeout(resolve, 50));
      });

      mockTracerProvider.shutdown.mockImplementation(() => {
        shutdownCallCount++;
        return new Promise((resolve) => setTimeout(resolve, 50));
      });

      // Start two shutdowns simultaneously
      const shutdown1 = shutdown();
      const shutdown2 = shutdown();

      await Promise.all([shutdown1, shutdown2]);

      // Should only shutdown once
      expect(forceFlushCallCount).toBe(1);
      expect(shutdownCallCount).toBe(1);
    });

    it('should set isShuttingDown flag during shutdown', async () => {
      const { shutdown, isSDKShuttingDown } = await import('./shutdown');

      mockIsConfigured.mockReturnValue(true);
      mockGetProvider.mockReturnValue(mockTracerProvider as any);

      // Create a promise to check the flag during shutdown
      let flagDuringShutdown = false;
      mockTracerProvider.forceFlush.mockImplementation(async () => {
        flagDuringShutdown = isSDKShuttingDown();
      });

      await shutdown();

      expect(flagDuringShutdown).toBe(true);
      expect(isSDKShuttingDown()).toBe(false); // Should be reset after shutdown
    });
  });

  describe('process signal handlers', () => {
    it('should handle SIGTERM signal', async () => {
      // Mock process.exit to prevent actual exit
      const mockExit = vi.spyOn(process, 'exit').mockImplementation((() => {}) as any);

      // Clear any existing listeners
      process.removeAllListeners('SIGTERM');

      // Import shutdown to register handlers
      await import('./shutdown');
      const { logger } = await import('./utils/logger');
      const mockLogger = vi.mocked(logger);

      mockIsConfigured.mockReturnValue(true);
      mockGetProvider.mockReturnValue(mockTracerProvider as any);

      // Emit SIGTERM
      process.emit('SIGTERM');

      // Wait for async operations
      await new Promise((resolve) => setTimeout(resolve, 50));

      expect(mockLogger.info).toHaveBeenCalledWith(
        'Received SIGTERM, initiating graceful shutdown...',
      );
      expect(mockTracerProvider.shutdown).toHaveBeenCalled();
      expect(mockExit).toHaveBeenCalledWith(0);

      mockExit.mockRestore();
    });

    it('should handle beforeExit event', async () => {
      // Clear any existing listeners
      process.removeAllListeners('beforeExit');

      // Import shutdown to register handlers
      await import('./shutdown');
      const { logger } = await import('./utils/logger');
      const mockLogger = vi.mocked(logger);

      mockIsConfigured.mockReturnValue(true);
      mockGetProvider.mockReturnValue(mockTracerProvider as any);

      // Emit beforeExit with code 0
      process.emit('beforeExit', 0);

      // Wait for async operations
      await new Promise((resolve) => setTimeout(resolve, 10));

      expect(mockLogger.debug).toHaveBeenCalledWith('Process exiting normally, flushing spans...');
      expect(mockTracerProvider.shutdown).toHaveBeenCalled();
    });

    it('should handle SIGINT signal', async () => {
      // Mock process.exit to prevent actual exit
      const mockExit = vi.spyOn(process, 'exit').mockImplementation((() => {}) as any);

      // Clear any existing listeners
      process.removeAllListeners('SIGINT');

      // Import shutdown to register handlers
      await import('./shutdown');
      const { logger } = await import('./utils/logger');
      const mockLogger = vi.mocked(logger);

      mockIsConfigured.mockReturnValue(true);
      mockGetProvider.mockReturnValue(mockTracerProvider as any);

      // Emit SIGINT
      process.emit('SIGINT');

      // Wait for async operations
      await new Promise((resolve) => setTimeout(resolve, 50));

      expect(mockLogger.info).toHaveBeenCalledWith(
        'Received SIGINT, initiating graceful shutdown...',
      );
      expect(mockTracerProvider.shutdown).toHaveBeenCalled();
      expect(mockExit).toHaveBeenCalledWith(0);

      mockExit.mockRestore();
    });
  });
});
