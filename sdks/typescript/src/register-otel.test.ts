import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { logger } from './utils/logger';

// Mock all dependencies before importing the module
vi.mock('./utils/logger', () => ({
  logger: {
    debug: vi.fn(),
    info: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock('@opentelemetry/sdk-node', () => ({
  NodeSDK: vi.fn().mockImplementation(() => ({
    start: vi.fn(),
    shutdown: vi.fn().mockResolvedValue(undefined),
  })),
}));

vi.mock('@opentelemetry/resources', () => ({
  Resource: vi.fn().mockImplementation((attributes) => ({ attributes })),
}));

vi.mock('@opentelemetry/semantic-conventions', () => ({
  SemanticResourceAttributes: {
    SERVICE_NAME: 'service.name',
    SERVICE_VERSION: 'service.version',
  },
}));

vi.mock('@opentelemetry/context-async-hooks', () => ({
  AsyncLocalStorageContextManager: vi.fn(),
}));

vi.mock('./instrumentors/openai-otel-instrumentation', () => ({
  OpenAIInstrumentation: vi.fn(),
}));

vi.mock('./exporters/json-exporter', () => ({
  JSONSpanExporter: vi.fn(),
}));

vi.mock('@opentelemetry/sdk-trace-base', () => ({
  BatchSpanProcessor: vi.fn(),
  TraceIdRatioBasedSampler: vi.fn(),
}));

vi.mock('../lilypad/generated', () => ({
  LilypadClient: vi.fn().mockImplementation((config) => ({
    config,
  })),
}));

vi.mock('./constants', () => ({
  BASE_URL: 'https://lilypad-api.mirascope.com/v0',
}));

describe('register-otel', () => {
  const originalEnv = process.env;
  let NodeSDKSpy: any;
  let ResourceSpy: any;
  let OpenAIInstrumentationSpy: any;
  let JSONSpanExporterSpy: any;
  let BatchSpanProcessorSpy: any;
  let TraceIdRatioBasedSamplerSpy: any;
  let LilypadClientSpy: any;

  beforeEach(() => {
    vi.clearAllMocks();
    // Reset environment
    process.env = { ...originalEnv };
    // Clear any BASE_URL that might be set
    delete process.env.LILYPAD_BASE_URL;

    // Clear module cache to allow re-importing with different env vars
    vi.resetModules();
  });

  afterEach(() => {
    process.env = originalEnv;
    vi.clearAllTimers();
  });

  describe('without LILYPAD_API_KEY', () => {
    it('should skip initialization and log debug message', async () => {
      delete process.env.LILYPAD_API_KEY;

      await import('./register-otel');

      // Wait for any async operations
      await new Promise((resolve) => setTimeout(resolve, 10));

      expect(logger.debug).toHaveBeenCalledWith(
        '[Register-OTel] No LILYPAD_API_KEY found, skipping auto-instrumentation',
      );
      expect(logger.error).not.toHaveBeenCalled();
      expect(logger.info).not.toHaveBeenCalled();
    });
  });

  describe('with invalid LILYPAD_PROJECT_ID', () => {
    it('should log error for missing project ID', async () => {
      process.env.LILYPAD_API_KEY = 'test-key';
      delete process.env.LILYPAD_PROJECT_ID;

      await import('./register-otel');

      await new Promise((resolve) => setTimeout(resolve, 10));

      expect(logger.error).toHaveBeenCalledWith(
        '[Register-OTel] Invalid or missing LILYPAD_PROJECT_ID. Must be a valid UUID.',
      );
    });

    it('should log error for invalid UUID format', async () => {
      process.env.LILYPAD_API_KEY = 'test-key';
      process.env.LILYPAD_PROJECT_ID = 'not-a-uuid';

      await import('./register-otel');

      await new Promise((resolve) => setTimeout(resolve, 10));

      expect(logger.error).toHaveBeenCalledWith(
        '[Register-OTel] Invalid or missing LILYPAD_PROJECT_ID. Must be a valid UUID.',
      );
    });
  });

  describe('with LILYPAD_AUTO_LLM=false', () => {
    it('should skip initialization when auto LLM is disabled', async () => {
      process.env.LILYPAD_API_KEY = 'test-key';
      process.env.LILYPAD_PROJECT_ID = '123e4567-e89b-12d3-a456-426614174000';
      process.env.LILYPAD_AUTO_LLM = 'false';

      await import('./register-otel');

      await new Promise((resolve) => setTimeout(resolve, 10));

      expect(logger.debug).toHaveBeenCalledWith(
        '[Register-OTel] LILYPAD_AUTO_LLM is false, skipping auto-instrumentation',
      );
      expect(logger.info).not.toHaveBeenCalled();
    });
  });

  describe('with valid configuration', () => {
    beforeEach(async () => {
      process.env.LILYPAD_API_KEY = 'test-api-key';
      process.env.LILYPAD_PROJECT_ID = '123e4567-e89b-12d3-a456-426614174000';
      process.env.LILYPAD_SERVICE_NAME = 'test-service';
      process.env.npm_package_version = '1.0.0';

      // Import mocked modules to get spies
      const sdkNode = await import('@opentelemetry/sdk-node');
      const resources = await import('@opentelemetry/resources');
      const openaiInst = await import('./instrumentors/openai-otel-instrumentation');
      const jsonExporter = await import('./exporters/json-exporter');
      const traceBase = await import('@opentelemetry/sdk-trace-base');
      const lilypadClient = await import('../lilypad/generated');

      NodeSDKSpy = vi.mocked(sdkNode.NodeSDK);
      ResourceSpy = vi.mocked(resources.Resource);
      OpenAIInstrumentationSpy = vi.mocked(openaiInst.OpenAIInstrumentation);
      JSONSpanExporterSpy = vi.mocked(jsonExporter.JSONSpanExporter);
      BatchSpanProcessorSpy = vi.mocked(traceBase.BatchSpanProcessor);
      TraceIdRatioBasedSamplerSpy = vi.mocked(traceBase.TraceIdRatioBasedSampler);
      LilypadClientSpy = vi.mocked(lilypadClient.LilypadClient);
    });

    it('should initialize SDK with correct configuration', async () => {
      await import('./register-otel');

      // Wait for async initialization
      await new Promise((resolve) => setTimeout(resolve, 50));

      // Check Resource creation
      expect(ResourceSpy).toHaveBeenCalledWith({
        'service.name': 'test-service',
        'service.version': '1.0.0',
        'lilypad.project_id': '123e4567-e89b-12d3-a456-426614174000',
      });

      // Check LilypadClient creation
      expect(LilypadClientSpy).toHaveBeenCalledWith({
        environment: 'https://lilypad-api.mirascope.com/v0',
        baseUrl: 'https://lilypad-api.mirascope.com/v0',
        apiKey: 'test-api-key',
      });

      // Check exporter creation
      expect(JSONSpanExporterSpy).toHaveBeenCalledWith(
        {
          apiKey: 'test-api-key',
          projectId: '123e4567-e89b-12d3-a456-426614174000',
          baseUrl: 'https://lilypad-api.mirascope.com/v0',
          serviceName: 'test-service',
        },
        expect.any(Object), // The client instance
      );

      // Check SDK initialization
      expect(NodeSDKSpy).toHaveBeenCalled();
      const sdkInstance = NodeSDKSpy.mock.results[0].value;
      expect(sdkInstance.start).toHaveBeenCalled();

      expect(logger.info).toHaveBeenCalledWith(
        '[Register-OTel] Lilypad OpenTelemetry SDK initialized successfully',
      );
    });

    it('should use custom environment variables', async () => {
      process.env.LILYPAD_BASE_URL = 'https://custom.api.com';
      process.env.LILYPAD_MAX_QUEUE_SIZE = '4096';
      process.env.LILYPAD_MAX_BATCH_SIZE = '1024';
      process.env.LILYPAD_EXPORT_DELAY = '10000';
      process.env.LILYPAD_EXPORT_TIMEOUT = '60000';
      process.env.LILYPAD_SAMPLING_RATIO = '0.5';

      await import('./register-otel');

      await new Promise((resolve) => setTimeout(resolve, 50));

      // Check custom base URL
      expect(LilypadClientSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          baseUrl: 'https://custom.api.com',
        }),
      );

      // Check batch processor configuration
      expect(BatchSpanProcessorSpy).toHaveBeenCalledWith(expect.any(Object), {
        maxQueueSize: 4096,
        maxExportBatchSize: 1024,
        scheduledDelayMillis: 10000,
        exportTimeoutMillis: 60000,
      });

      // Check sampler configuration
      expect(TraceIdRatioBasedSamplerSpy).toHaveBeenCalledWith(0.5);
    });

    it('should configure OpenAI instrumentation with debug mode', async () => {
      process.env.LILYPAD_DEBUG = 'true';
      process.env.LILYPAD_SUPPRESS_LOGS = 'true';

      await import('./register-otel');

      await new Promise((resolve) => setTimeout(resolve, 50));

      expect(OpenAIInstrumentationSpy).toHaveBeenCalledWith({
        enabled: true,
        requestHook: expect.any(Function),
        responseHook: expect.any(Function),
        fallbackToProxy: true,
        suppressInternalInstrumentation: true,
      });

      // Test request hook
      const requestHook = OpenAIInstrumentationSpy.mock.calls[0][0].requestHook;
      const mockSpan = { setAttribute: vi.fn() };
      const mockParams = { model: 'gpt-4' };

      requestHook(mockSpan, mockParams);

      expect(mockSpan.setAttribute).toHaveBeenCalledWith(
        'lilypad.debug.params',
        JSON.stringify(mockParams),
      );

      // Test response hook
      const responseHook = OpenAIInstrumentationSpy.mock.calls[0][0].responseHook;
      const mockResponse = { id: 'response-123' };

      responseHook(mockSpan, mockResponse);

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.id', 'response-123');
    });

    it('should handle initialization errors gracefully', async () => {
      // Make LilypadClient throw an error
      LilypadClientSpy.mockImplementationOnce(() => {
        throw new Error('Connection failed');
      });

      await import('./register-otel');

      await new Promise((resolve) => setTimeout(resolve, 50));

      expect(logger.error).toHaveBeenCalledWith(
        '[Register-OTel] Failed to initialize Lilypad auto-instrumentation:',
        expect.any(Error),
      );

      // Should not throw - app continues running
      expect(logger.info).not.toHaveBeenCalled();
    });

    describe('shutdown handlers', () => {
      let sdkInstance: any;
      let shutdownResolve: any;
      let shutdownPromise: Promise<void>;

      beforeEach(async () => {
        // Create a promise that we can control
        shutdownPromise = new Promise((resolve) => {
          shutdownResolve = resolve;
        });

        // Mock SDK shutdown to use our controlled promise
        NodeSDKSpy.mockImplementation(() => {
          sdkInstance = {
            start: vi.fn(),
            shutdown: vi.fn().mockReturnValue(shutdownPromise),
          };
          return sdkInstance;
        });

        await import('./register-otel');
        await new Promise((resolve) => setTimeout(resolve, 50));
      });

      it('should register shutdown handlers for SIGINT', async () => {
        const sigintListeners = process.listeners('SIGINT');
        const shutdownHandler = sigintListeners[sigintListeners.length - 1];

        expect(shutdownHandler).toBeDefined();

        // Trigger shutdown - don't await yet
        const shutdownPromiseFromHandler = shutdownHandler();

        // Resolve shutdown promise
        shutdownResolve();

        // Now await both promises
        await Promise.all([shutdownPromise, shutdownPromiseFromHandler]);

        expect(sdkInstance.shutdown).toHaveBeenCalled();
        expect(logger.debug).toHaveBeenCalledWith(
          '[Register-OTel] Shutting down OpenTelemetry SDK',
        );
        expect(logger.debug).toHaveBeenCalledWith(
          '[Register-OTel] OpenTelemetry SDK shutdown complete',
        );
      }, 10000);

      it('should handle shutdown errors', async () => {
        // Make shutdown reject
        sdkInstance.shutdown.mockRejectedValueOnce(new Error('Shutdown failed'));

        const sigintListeners = process.listeners('SIGINT');
        const shutdownHandler = sigintListeners[sigintListeners.length - 1];

        await shutdownHandler();

        expect(logger.error).toHaveBeenCalledWith(
          '[Register-OTel] Error during shutdown:',
          expect.any(Error),
        );
      });
    });
  });

  describe('default values', () => {
    it('should use default service name when not provided', async () => {
      process.env.LILYPAD_API_KEY = 'test-key';
      process.env.LILYPAD_PROJECT_ID = '123e4567-e89b-12d3-a456-426614174000';
      delete process.env.LILYPAD_SERVICE_NAME;

      await import('./register-otel');

      await new Promise((resolve) => setTimeout(resolve, 50));

      const resources = await import('@opentelemetry/resources');
      const ResourceSpy = vi.mocked(resources.Resource);

      expect(ResourceSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          'service.name': 'lilypad-node-app',
        }),
      );
    });

    it('should use default values for batch processor config', async () => {
      process.env.LILYPAD_API_KEY = 'test-key';
      process.env.LILYPAD_PROJECT_ID = '123e4567-e89b-12d3-a456-426614174000';

      await import('./register-otel');

      await new Promise((resolve) => setTimeout(resolve, 50));

      const traceBase = await import('@opentelemetry/sdk-trace-base');
      const BatchSpanProcessorSpy = vi.mocked(traceBase.BatchSpanProcessor);

      expect(BatchSpanProcessorSpy).toHaveBeenCalledWith(expect.any(Object), {
        maxQueueSize: 2048,
        maxExportBatchSize: 512,
        scheduledDelayMillis: 5000,
        exportTimeoutMillis: 30000,
      });
    });
  });
});
