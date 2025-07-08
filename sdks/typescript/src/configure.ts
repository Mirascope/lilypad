import { Resource } from '@opentelemetry/resources';
import { SEMRESATTRS_SERVICE_NAME } from '@opentelemetry/semantic-conventions';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { trace } from '@opentelemetry/api';

import type { LilypadConfig } from './types';
import { setSettings, isConfigured } from './utils/settings';
import { logger } from './utils/logger';
import { CryptoIdGenerator } from './utils/id-generator';
import { JSONSpanExporter } from './exporters/json-exporter';
import { LilypadClient } from '../lilypad/generated';

// Tracer provider instance for proper shutdown
let _provider: NodeTracerProvider | null = null;

export async function configure(config: LilypadConfig): Promise<void> {
  if (isConfigured()) {
    logger.warn('Lilypad SDK already configured. Skipping reconfiguration.');
    return;
  }

  // Set up auto instrumentation early if enabled
  logger.debug(`auto_llm config value: ${config.auto_llm}`);
  if (config.auto_llm) {
    logger.debug('Attempting to load OpenAI instrumentation...');
    try {
      const { setupOpenAIHooks } = await import('./instrumentors/openai-hook');
      logger.debug('OpenAI instrumentation module loaded');
      setupOpenAIHooks();
      logger.debug('OpenAI auto-instrumentation hooks installed');
    } catch (error) {
      logger.error('Failed to enable OpenAI auto-instrumentation:', error);
      logger.error('Error stack:', error instanceof Error ? error.stack : 'No stack');
    }
  } else {
    logger.debug('auto_llm is disabled, skipping OpenAI instrumentation');
  }

  // Validate required config
  if (!config.apiKey || !config.projectId) {
    throw new Error('Lilypad SDK configuration requires apiKey and projectId.');
  }

  // Validate project ID format (UUIDs)
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  if (!config.projectId.match(uuidRegex)) {
    throw new Error('Invalid project ID format. Project ID should be a valid UUID.');
  }

  // Set default values with environment variable overrides
  const finalConfig: LilypadConfig = {
    baseUrl:
      process.env.LILYPAD_BASE_URL ||
      (process.env.LILYPAD_REMOTE_API_URL
        ? `${process.env.LILYPAD_REMOTE_API_URL}/v0`
        : config.baseUrl || 'https://api.app.lilypad.so/v0'),
    remoteClientUrl:
      process.env.LILYPAD_REMOTE_CLIENT_URL || config.remoteClientUrl || 'https://app.lilypad.so',
    logLevel: 'info',
    serviceName: 'lilypad-node-app',
    auto_llm: false,
    auto_http: false,
    preserveExistingPropagator: false,
    ...config,
    batchProcessorOptions: {
      scheduledDelayMillis: 5000,
      maxQueueSize: 2048,
      maxExportBatchSize: 512,
      exportTimeoutMillis: 30000,
      ...config.batchProcessorOptions,
    },
  };

  // Ensure config values override environment variables
  if (config.baseUrl) {
    finalConfig.baseUrl = config.baseUrl;
  }
  if (config.remoteClientUrl) {
    finalConfig.remoteClientUrl = config.remoteClientUrl;
  }

  setSettings(finalConfig);

  // Configure logger
  logger.setLevel(finalConfig.logLevel || 'info');

  // Log configuration for debugging
  logger.debug(`Using baseUrl: ${finalConfig.baseUrl}`);
  logger.debug(`Using remoteClientUrl: ${finalConfig.remoteClientUrl}`);

  const resource = Resource.default().merge(
    new Resource({
      [SEMRESATTRS_SERVICE_NAME]: finalConfig.serviceName,
    }),
  );

  // We've already validated these values exist
  const { baseUrl, apiKey } = finalConfig;
  if (!baseUrl || !apiKey) {
    throw new Error('Configuration error: missing required values');
  }

  const client = new LilypadClient({
    environment: baseUrl,
    baseUrl: baseUrl,
    apiKey: apiKey,
  });
  logger.debug(`Created LilypadClient with baseUrl: ${finalConfig.baseUrl}`);

  const exporter = new JSONSpanExporter(finalConfig, client);
  logger.debug('Created JSONSpanExporter');

  const spanProcessor = new BatchSpanProcessor(exporter, finalConfig.batchProcessorOptions);
  logger.debug(
    `Created BatchSpanProcessor with options: ${JSON.stringify(finalConfig.batchProcessorOptions)}`,
  );

  const provider = new NodeTracerProvider({
    resource,
    idGenerator: new CryptoIdGenerator(),
    spanProcessors: [spanProcessor],
  });
  logger.debug('Created NodeTracerProvider');

  provider.register();
  logger.debug('Registered tracer provider globally');

  _provider = provider;

  logger.info(`Lilypad SDK configured successfully for project ${finalConfig.projectId}`);
}

export function getTracerProvider() {
  return trace.getTracerProvider();
}

export function getTracer(name = 'lilypad', version?: string) {
  return trace.getTracer(name, version);
}

export function getProvider(): NodeTracerProvider | null {
  return _provider;
}
