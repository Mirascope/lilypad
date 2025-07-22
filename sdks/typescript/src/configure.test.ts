import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { configure, getTracerProvider, getTracer, getProvider } from './configure';
import * as settings from './utils/settings';
import { logger } from './utils/logger';
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { trace } from '@opentelemetry/api';

vi.mock('./utils/settings');
vi.mock('./utils/logger');
vi.mock('@opentelemetry/sdk-trace-node');
vi.mock('./exporters/json-exporter');
vi.mock('@opentelemetry/sdk-trace-base', () => ({
  BatchSpanProcessor: vi.fn().mockImplementation(() => ({})),
}));
vi.mock('../lilypad/generated', () => ({
  LilypadClient: vi.fn().mockImplementation(() => ({})),
}));

describe('configure', () => {
  const mockSetSettings = vi.mocked(settings.setSettings);
  const mockIsConfigured = vi.mocked(settings.isConfigured);
  const mockLogger = vi.mocked(logger);

  beforeEach(() => {
    vi.clearAllMocks();
    mockIsConfigured.mockReturnValue(false);
    vi.mocked(NodeTracerProvider).mockImplementation(
      () =>
        ({
          register: vi.fn(),
        }) as any,
    );
    // Clear environment variables that might affect tests
    delete process.env.LILYPAD_BASE_URL;
    delete process.env.LILYPAD_REMOTE_API_URL;
    delete process.env.LILYPAD_REMOTE_CLIENT_URL;
  });

  afterEach(() => {
    // Clean up environment variables after each test
    delete process.env.LILYPAD_BASE_URL;
    delete process.env.LILYPAD_REMOTE_API_URL;
    delete process.env.LILYPAD_REMOTE_CLIENT_URL;
  });

  describe('configuration validation', () => {
    it('should throw error if apiKey is missing', async () => {
      await expect(configure({ projectId: 'test-project' } as any)).rejects.toThrow(
        'Lilypad SDK configuration requires apiKey and projectId',
      );
    });

    it('should throw error if projectId is missing', async () => {
      await expect(configure({ apiKey: 'test-key' } as any)).rejects.toThrow(
        'Lilypad SDK configuration requires apiKey and projectId',
      );
    });

    it('should accept API keys with any format', async () => {
      // The configure function doesn't validate API key format
      await expect(
        configure({
          apiKey: 'invalid key with spaces',
          projectId: '123e4567-e89b-12d3-a456-426614174000',
        }),
      ).resolves.toBeUndefined();
    });

    it('should throw error for invalid project ID format', async () => {
      await expect(
        configure({
          apiKey: 'valid-api-key',
          projectId: 'not-a-uuid',
        }),
      ).rejects.toThrow('Invalid project ID format');
    });

    it('should handle missing baseUrl after configuration', async () => {
      // Mock setSettings to remove baseUrl somehow
      const originalImpl = mockSetSettings.getMockImplementation();
      mockSetSettings.mockImplementation((config) => {
        // Simulate a scenario where baseUrl is undefined
        delete (config as any).baseUrl;
      });

      await expect(
        configure({
          apiKey: 'test-api-key',
          projectId: '123e4567-e89b-12d3-a456-426614174000',
        }),
      ).rejects.toThrow('Configuration error: missing required values');

      // Restore original implementation
      mockSetSettings.mockImplementation(originalImpl || vi.fn());
    });
  });

  describe('successful configuration', () => {
    const validConfig = {
      apiKey: 'test-api-key',
      projectId: '123e4567-e89b-12d3-a456-426614174000',
    };

    it('should configure SDK with minimal config', async () => {
      await configure(validConfig);

      expect(mockSetSettings).toHaveBeenCalledWith(
        expect.objectContaining({
          apiKey: 'test-api-key',
          projectId: '123e4567-e89b-12d3-a456-426614174000',
          baseUrl: 'https://lilypad-api.mirascope.com/v0',
          remoteClientUrl: 'https://lilypad.mirascope.com',
          logLevel: 'info',
          serviceName: 'lilypad-node-app',
          autoLlm: false,
          autoHttp: false,
          preserveExistingPropagator: false,
          batchProcessorOptions: {
            scheduledDelayMillis: 5000,
            maxQueueSize: 2048,
            maxExportBatchSize: 512,
            exportTimeoutMillis: 30000,
          },
        }),
      );
    });

    it('should use custom configuration values', async () => {
      const customConfig = {
        ...validConfig,
        baseUrl: 'https://custom.api.com',
        logLevel: 'debug' as const,
        serviceName: 'my-service',
        autoLlm: true,
      };

      await configure(customConfig);

      expect(mockSetSettings).toHaveBeenCalledWith(
        expect.objectContaining({
          baseUrl: 'https://custom.api.com',
          logLevel: 'debug',
          serviceName: 'my-service',
          autoLlm: true,
        }),
      );
    });

    it('should set logger level', async () => {
      await configure({
        ...validConfig,
        logLevel: 'warn',
      });

      expect(mockLogger.setLevel).toHaveBeenCalledWith('warn');
    });

    it('should skip reconfiguration if already configured', async () => {
      mockIsConfigured.mockReturnValue(true);

      await configure(validConfig);

      expect(mockLogger.warn).toHaveBeenCalledWith(
        'Lilypad SDK already configured. Skipping reconfiguration.',
      );
      expect(mockSetSettings).not.toHaveBeenCalled();
    });
  });

  describe('auto instrumentation', () => {
    const validConfig = {
      apiKey: 'test-api-key',
      projectId: '123e4567-e89b-12d3-a456-426614174000',
      autoLlm: true,
    };

    it('should attempt to instrument OpenAI when autoLlm is true', async () => {
      // Mock successful OpenAI import
      vi.doMock('openai', () => ({ default: {} }), { virtual: true });
      vi.doMock('./instrumentors/openai', () => ({
        OpenAIInstrumentor: vi.fn().mockImplementation(() => ({
          instrument: vi.fn(),
        })),
      }));

      await configure(validConfig);

      expect(mockLogger.debug).toHaveBeenCalledWith('OpenAI auto-instrumentation hooks installed');
    });

    it('should handle errors when loading OpenAI instrumentation', async () => {
      // This test is tricky because we need to test dynamic import failure
      // We'll test it by mocking the module to throw during import
      const mockError = new Error('Failed to load module');

      // First mock successful to avoid issues with module resolution
      vi.doMock('./instrumentors/openai-hook', () => ({
        setupOpenAIHooks: vi.fn(),
      }));

      // Then immediately mock it to throw
      vi.doMock('./instrumentors/openai-hook', () => {
        throw mockError;
      });

      await configure(validConfig);

      // The error might be wrapped or transformed, so let's check for the error messages
      expect(mockLogger.error).toHaveBeenCalledTimes(2);
      const errorCalls = mockLogger.error.mock.calls;
      expect(errorCalls[0][0]).toBe('Failed to enable OpenAI auto-instrumentation:');
      expect(errorCalls[1][0]).toBe('Error stack:');
    });
  });

  describe('environment variable handling', () => {
    const validConfig = {
      apiKey: 'test-api-key',
      projectId: '123e4567-e89b-12d3-a456-426614174000',
    };

    beforeEach(() => {
      delete process.env.LILYPAD_BASE_URL;
      delete process.env.LILYPAD_REMOTE_API_URL;
      delete process.env.LILYPAD_REMOTE_CLIENT_URL;
    });

    afterEach(() => {
      delete process.env.LILYPAD_BASE_URL;
      delete process.env.LILYPAD_REMOTE_API_URL;
      delete process.env.LILYPAD_REMOTE_CLIENT_URL;
    });

    it('should use LILYPAD_BASE_URL env var when set', async () => {
      process.env.LILYPAD_BASE_URL = 'https://env.api.com';

      await configure(validConfig);

      expect(mockSetSettings).toHaveBeenCalledWith(
        expect.objectContaining({
          baseUrl: 'https://env.api.com',
        }),
      );
    });

    it('should use LILYPAD_REMOTE_API_URL env var to construct baseUrl', async () => {
      process.env.LILYPAD_REMOTE_API_URL = 'https://remote.api.com';

      await configure(validConfig);

      expect(mockSetSettings).toHaveBeenCalledWith(
        expect.objectContaining({
          baseUrl: 'https://remote.api.com/v0',
        }),
      );
    });

    it('should use LILYPAD_REMOTE_CLIENT_URL env var when set', async () => {
      process.env.LILYPAD_REMOTE_CLIENT_URL = 'https://remote.client.com';

      await configure(validConfig);

      expect(mockSetSettings).toHaveBeenCalledWith(
        expect.objectContaining({
          remoteClientUrl: 'https://remote.client.com',
        }),
      );
    });

    it('should prioritize config values over env vars', async () => {
      process.env.LILYPAD_BASE_URL = 'https://env.api.com';
      process.env.LILYPAD_REMOTE_CLIENT_URL = 'https://env.client.com';

      await configure({
        ...validConfig,
        baseUrl: 'https://config.api.com',
        remoteClientUrl: 'https://config.client.com',
      });

      expect(mockSetSettings).toHaveBeenCalledWith(
        expect.objectContaining({
          baseUrl: 'https://config.api.com',
          remoteClientUrl: 'https://config.client.com',
        }),
      );
    });
  });

  describe('batchProcessorOptions', () => {
    const validConfig = {
      apiKey: 'test-api-key',
      projectId: '123e4567-e89b-12d3-a456-426614174000',
    };

    it('should merge custom batchProcessorOptions with defaults', async () => {
      await configure({
        ...validConfig,
        batchProcessorOptions: {
          maxQueueSize: 1024,
          scheduledDelayMillis: 10000,
        },
      });

      expect(mockSetSettings).toHaveBeenCalledWith(
        expect.objectContaining({
          batchProcessorOptions: {
            scheduledDelayMillis: 10000,
            maxQueueSize: 1024,
            maxExportBatchSize: 512,
            exportTimeoutMillis: 30000,
          },
        }),
      );
    });
  });

  describe('exported functions', () => {
    it('should call trace.getTracerProvider()', () => {
      const mockTracerProvider = { tracer: 'provider' };
      vi.spyOn(trace, 'getTracerProvider').mockReturnValue(mockTracerProvider as any);

      const result = getTracerProvider();

      expect(trace.getTracerProvider).toHaveBeenCalled();
      expect(result).toBe(mockTracerProvider);
    });

    it('should call trace.getTracer() with default name', () => {
      const mockTracer = { tracer: 'instance' };
      vi.spyOn(trace, 'getTracer').mockReturnValue(mockTracer as any);

      const result = getTracer();

      expect(trace.getTracer).toHaveBeenCalledWith('lilypad', undefined);
      expect(result).toBe(mockTracer);
    });

    it('should call trace.getTracer() with custom name and version', () => {
      const mockTracer = { tracer: 'instance' };
      vi.spyOn(trace, 'getTracer').mockReturnValue(mockTracer as any);

      const result = getTracer('custom-tracer', '1.0.0');

      expect(trace.getTracer).toHaveBeenCalledWith('custom-tracer', '1.0.0');
      expect(result).toBe(mockTracer);
    });

    it('should return provider state correctly', async () => {
      // Since we can't easily reset the module state, let's test that getProvider
      // returns something after configuration
      const validConfig = {
        apiKey: 'test-api-key',
        projectId: '123e4567-e89b-12d3-a456-426614174000',
      };

      await configure(validConfig);

      const result = getProvider();
      // The result will be a mocked instance since NodeTracerProvider is mocked
      expect(result).toBeDefined();
      expect(result).not.toBeNull();
    });
  });
});
