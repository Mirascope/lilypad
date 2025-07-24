/**
 * OpenTelemetry-compliant register module for auto-instrumentation
 *
 * Usage:
 *   CJS: node --require ./register-otel.js app.js
 *   ESM: node --import ./register-otel.mjs app.js
 */

import { NodeSDK } from '@opentelemetry/sdk-node';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import { AsyncLocalStorageContextManager } from '@opentelemetry/context-async-hooks';
// import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { logger } from './utils/logger';
import { OpenAIInstrumentation } from './instrumentors/openai-otel-instrumentation';
import { JSONSpanExporter } from './exporters/json-exporter';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { TraceIdRatioBasedSampler } from '@opentelemetry/sdk-trace-base';

// Check if we should auto-configure
const apiKey = process.env.LILYPAD_API_KEY;
const projectId = process.env.LILYPAD_PROJECT_ID;
const baseUrl = process.env.LILYPAD_BASE_URL || 'https://api.app.lilypad.so/v0';
const serviceName = process.env.LILYPAD_SERVICE_NAME || 'lilypad-node-app';
const autoLLM = process.env.LILYPAD_AUTO_LLM !== 'false'; // Default to true

if (!apiKey) {
  logger.debug('[Register-OTel] No LILYPAD_API_KEY found, skipping auto-instrumentation');
  // Don't throw - allow the app to run without tracing
} else if (
  !projectId ||
  !projectId.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
) {
  logger.error('[Register-OTel] Invalid or missing LILYPAD_PROJECT_ID. Must be a valid UUID.');
  // Don't throw - allow the app to run without tracing
} else if (autoLLM) {
  logger.debug('[Register-OTel] Configuring Lilypad auto-instrumentation with OTel SDK');

  // Initialize asynchronously
  (async () => {
    try {
      // Create resource
      const resource = new Resource({
        [SemanticResourceAttributes.SERVICE_NAME]: serviceName,
        [SemanticResourceAttributes.SERVICE_VERSION]: process.env.npm_package_version || 'unknown',
        'lilypad.project_id': projectId,
      });

      // Create Lilypad client directly
      const { LilypadClient } = await import('../lilypad/generated');
      const client = new LilypadClient({
        environment: baseUrl,
        baseUrl: baseUrl,
        apiKey: apiKey,
      });

      // Create exporter with the client
      const exporter = new JSONSpanExporter(
        {
          apiKey,
          projectId,
          baseUrl,
          serviceName,
        },
        client,
      );

      // Create span processor
      const spanProcessor = new BatchSpanProcessor(exporter, {
        maxQueueSize: parseInt(process.env.LILYPAD_MAX_QUEUE_SIZE || '2048'),
        maxExportBatchSize: parseInt(process.env.LILYPAD_MAX_BATCH_SIZE || '512'),
        scheduledDelayMillis: parseInt(process.env.LILYPAD_EXPORT_DELAY || '5000'),
        exportTimeoutMillis: parseInt(process.env.LILYPAD_EXPORT_TIMEOUT || '30000'),
      });

      // Create sampler
      const samplingRatio = parseFloat(process.env.LILYPAD_SAMPLING_RATIO || '1.0');
      const sampler = new TraceIdRatioBasedSampler(samplingRatio);

      // Create SDK with AsyncLocalStorage context manager
      const sdk = new NodeSDK({
        resource,
        spanProcessor: spanProcessor as any, // Type mismatch workaround
        sampler,
        contextManager: new AsyncLocalStorageContextManager(),
        instrumentations: [
          new OpenAIInstrumentation({
            enabled: true,
            requestHook: (span, params) => {
              // Add custom attributes if needed
              if (process.env.LILYPAD_DEBUG === 'true') {
                span.setAttribute('lilypad.debug.params', JSON.stringify(params));
              }
            },
            responseHook: (span, response) => {
              // Add custom response attributes if needed
              if (response.id) {
                span.setAttribute('gen_ai.response.id', response.id);
              }
            },
            fallbackToProxy: true,
            suppressInternalInstrumentation: process.env.LILYPAD_SUPPRESS_LOGS === 'true',
          }),
        ],
      });

      // Initialize the SDK
      sdk.start();
      logger.info('[Register-OTel] Lilypad OpenTelemetry SDK initialized successfully');

      // Graceful shutdown
      const shutdown = async () => {
        logger.debug('[Register-OTel] Shutting down OpenTelemetry SDK');
        try {
          await sdk.shutdown();
          logger.debug('[Register-OTel] OpenTelemetry SDK shutdown complete');
        } catch (error) {
          logger.error('[Register-OTel] Error during shutdown:', error);
        }
      };

      // Register shutdown handlers
      process.once('SIGINT', shutdown);
      process.once('SIGTERM', shutdown);
      process.once('beforeExit', shutdown);
    } catch (error) {
      logger.error('[Register-OTel] Failed to initialize Lilypad auto-instrumentation:', error);
      // Don't throw - allow the app to run without tracing
    }
  })();
} else {
  logger.debug('[Register-OTel] LILYPAD_AUTO_LLM is false, skipping auto-instrumentation');
}

// Export for testing
export { OpenAIInstrumentation };
