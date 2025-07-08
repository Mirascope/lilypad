import { describe, it, expect, beforeEach, vi } from 'vitest';
import * as settings from './utils/settings';
import { getProvider } from './configure';

vi.mock('./utils/settings');
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
  });
});
