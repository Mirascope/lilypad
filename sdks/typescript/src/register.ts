/**
 * Register module for auto-instrumentation
 * This file should be loaded with --require or --loader flag
 */

import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';

import { logger } from './utils/logger';
import { setSettings } from './utils/settings';
import { getOrCreateContextManager } from './utils/shared-context';
import { OpenAIInstrumentation } from './instrumentors/openai-otel-instrumentation';
import { JSONSpanExporter } from './exporters/json-exporter';

// Enable debug logging based on environment variable
const logLevel = process.env.LILYPAD_LOG_LEVEL || 'info';
if (logLevel && ['debug', 'info', 'warn', 'error'].includes(logLevel)) {
  logger.setLevel(logLevel as any);
}

// Check environment variables
const apiKey = process.env.LILYPAD_API_KEY;
const projectId = process.env.LILYPAD_PROJECT_ID || 'default';
const baseUrl = process.env.LILYPAD_BASE_URL || 'https://api.app.lilypad.so/v0';
const serviceName = process.env.LILYPAD_SERVICE_NAME || 'lilypad-node-app';

logger.info('[Register] Environment check:', {
  hasApiKey: !!apiKey,
  projectId,
  baseUrl,
  serviceName,
});

if (!apiKey) {
  logger.warn('[Register] No LILYPAD_API_KEY found, auto-instrumentation disabled');
} else {
  // Use shared context manager singleton
  getOrCreateContextManager();
  
  // Save settings for manual span() support
  setSettings({
    apiKey,
    projectId,
    baseUrl: baseUrl || 'https://api.app.lilypad.so/v0',
    serviceName: serviceName || 'lilypad-node-app',
  });

  // Create resource
  const resource = Resource.default().merge(
    new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: serviceName,
      [SemanticResourceAttributes.SERVICE_VERSION]: '0.1.0',
    }),
  );

  // Create provider
  const provider = new NodeTracerProvider({
    resource,
  });

  // Create exporter and processor
  (async () => {
    try {
      // Import LilypadClient dynamically to avoid circular dependencies
      const { LilypadClient } = await import('../lilypad/generated');
      const client = new LilypadClient({
        environment: baseUrl,
        baseUrl: baseUrl,
        apiKey: apiKey,
      });

      const exporter = new JSONSpanExporter(
        {
          apiKey,
          projectId,
          baseUrl,
          serviceName,
        },
        client,
      );

      const spanProcessor = new BatchSpanProcessor(exporter, {
        maxQueueSize: parseInt(process.env.LILYPAD_MAX_QUEUE_SIZE || '2048'),
        maxExportBatchSize: parseInt(process.env.LILYPAD_MAX_BATCH_SIZE || '512'),
        scheduledDelayMillis: parseInt(process.env.LILYPAD_EXPORT_DELAY || '5000'),
        exportTimeoutMillis: parseInt(process.env.LILYPAD_EXPORT_TIMEOUT || '30000'),
      });

      provider.addSpanProcessor(spanProcessor);
      provider.register();

      // Register OpenAI instrumentation
      const openAIInstrumentation = new OpenAIInstrumentation({
        requestHook: (_span, params) => {
          logger.debug('[Register] Request hook called', { model: params.model });
        },
        responseHook: (_span, response) => {
          logger.debug('[Register] Response hook called', { id: response.id });
        },
        fallbackToProxy: true, // Enable Proxy fallback for lazy-loaded properties
        suppressInternalInstrumentation: false,
      });

      registerInstrumentations({
        instrumentations: [openAIInstrumentation],
      });

      logger.info('[Register] OpenAI auto-instrumentation loaded with InstrumentationBase');

      // Graceful shutdown
      const shutdown = async () => {
        logger.debug('[Register] Shutting down');
        await provider.shutdown();
      };

      process.once('SIGINT', shutdown);
      process.once('SIGTERM', shutdown);
      process.once('beforeExit', shutdown);
    } catch (error) {
      logger.error('[Register] Failed to initialize:', error);
    }
  })();
}
