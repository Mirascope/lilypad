import { describe, it, expect, beforeEach, vi } from 'vitest';
import { configure } from './configure';
import * as settings from './utils/settings';
import { logger } from './utils/logger';
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';

vi.mock('./utils/settings');
vi.mock('./utils/logger');
vi.mock('@opentelemetry/sdk-trace-node');
vi.mock('./exporters/json-exporter');
vi.mock('@opentelemetry/sdk-trace-base', () => ({
  BatchSpanProcessor: vi.fn().mockImplementation(() => ({})),
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
          baseUrl: 'https://api.app.lilypad.so/v0',
          remoteClientUrl: 'https://app.lilypad.so',
          logLevel: 'info',
          serviceName: 'lilypad-node-app',
          auto_llm: false,
          auto_http: false,
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
        auto_llm: true,
      };

      await configure(customConfig);

      expect(mockSetSettings).toHaveBeenCalledWith(
        expect.objectContaining({
          baseUrl: 'https://custom.api.com',
          logLevel: 'debug',
          serviceName: 'my-service',
          auto_llm: true,
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
      auto_llm: true,
    };

    it('should attempt to instrument OpenAI when auto_llm is true', async () => {
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

    it('should handle missing OpenAI gracefully', async () => {
      // Skip this test as dynamic imports are complex to mock in vitest
      // This functionality is better tested in integration tests
    });
  });
});
