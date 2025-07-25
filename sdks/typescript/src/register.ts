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
import type { LogLevel } from './types';
import { getOrCreateContextManager } from './utils/shared-context';
import { OpenAIInstrumentation } from './instrumentors/openai-otel-instrumentation';
import { AnthropicInstrumentation } from './instrumentors/anthropic-otel-instrumentation';
import { GoogleInstrumentation } from './instrumentors/google-otel-instrumentation';
import { JSONSpanExporter } from './exporters/json-exporter';
import { BASE_URL, REMOTE_CLIENT_URL } from './constants';

// Enable debug logging based on environment variable
const logLevel = process.env.LILYPAD_LOG_LEVEL || 'info';
const validLogLevels: LogLevel[] = ['debug', 'info', 'warn', 'error'];
if (validLogLevels.includes(logLevel as LogLevel)) {
  logger.setLevel(logLevel as LogLevel);
}

// Check environment variables
const apiKey = process.env.LILYPAD_API_KEY;
const projectId = process.env.LILYPAD_PROJECT_ID || 'default';
const baseUrl = process.env.LILYPAD_BASE_URL || BASE_URL;
const serviceName = process.env.LILYPAD_SERVICE_NAME || 'lilypad-node-app';
const remoteClientUrl = process.env.LILYPAD_REMOTE_CLIENT_URL || REMOTE_CLIENT_URL;

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
    baseUrl: baseUrl || BASE_URL,
    serviceName: serviceName || 'lilypad-node-app',
  });

  // Create resource
  const resource = Resource.default().merge(
    new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: serviceName,
      [SemanticResourceAttributes.SERVICE_VERSION]: '0.1.0',
    }),
  );

  // Initialize synchronously first
  try {
    // Create provider
    const provider = new NodeTracerProvider({
      resource,
    });

    // Import LilypadClient synchronously
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { LilypadClient } = require('../lilypad/generated');
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
        remoteClientUrl,
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

    logger.info('[Register] Tracer provider registered successfully');

    // Store the provider reference for shutdown
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { setProvider } = require('./configure');
    setProvider(provider);

    // Register instrumentations
    try {
      const openAIInstrumentation = new OpenAIInstrumentation({
        requestHook: (_span, params) => {
          logger.debug('[Register] OpenAI request hook called', { model: params.model });
        },
        responseHook: (_span, response) => {
          logger.debug('[Register] OpenAI response hook called', { id: response.id });
        },
        fallbackToProxy: true, // Enable Proxy fallback for lazy-loaded properties
        suppressInternalInstrumentation: false,
      });

      const anthropicInstrumentation = new AnthropicInstrumentation({
        requestHook: (_span, params) => {
          logger.debug('[Register] Anthropic request hook called', { model: params.model });
        },
        responseHook: (_span, response) => {
          logger.debug('[Register] Anthropic response hook called', { id: response.id });
        },
        fallbackToProxy: true, // Enable Proxy fallback for lazy-loaded properties
        suppressInternalInstrumentation: false,
      });

      const googleInstrumentation = new GoogleInstrumentation({
        requestHook: (_span, params) => {
          logger.debug('[Register] Google request hook called', { paramsType: typeof params });
        },
        responseHook: (_span, response) => {
          logger.debug('[Register] Google response hook called', {
            candidates: response.candidates?.length,
          });
        },
        fallbackToProxy: true, // Enable Proxy fallback for lazy-loaded properties
        suppressInternalInstrumentation: false,
      });

      registerInstrumentations({
        instrumentations: [openAIInstrumentation, anthropicInstrumentation, googleInstrumentation],
      });

      logger.info(
        '[Register] OpenAI, Anthropic, and Google auto-instrumentation loaded with InstrumentationBase',
      );
    } catch (instrumentationError) {
      logger.error('[Register] Failed to register instrumentations:', instrumentationError);
      // Continue even if instrumentation fails
    }

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
}
