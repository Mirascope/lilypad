import { Resource } from '@opentelemetry/resources';
import { SEMRESATTRS_SERVICE_NAME } from '@opentelemetry/semantic-conventions';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { trace } from '@opentelemetry/api';

import type { LilypadConfig } from './types';
import { setSettings, isConfigured, getSettings } from './utils/settings';
import { logger } from './utils/logger';
import { getOrCreateContextManager } from './utils/shared-context';
import { CryptoIdGenerator } from './utils/id-generator';
import { JSONSpanExporter } from './exporters/json-exporter';
import { LilypadClient } from '../lilypad/generated';
import { BASE_URL, REMOTE_CLIENT_URL } from './constants';

// Tracer provider instance for proper shutdown
let _provider: NodeTracerProvider | null = null;

export async function configure(config: LilypadConfig): Promise<void> {
  // Check if already configured via register.js
  const existingProvider = trace.getTracerProvider();
  const existingSettings = getSettings();

  if (existingSettings && existingProvider) {
    logger.info('Lilypad SDK already configured via register.js, updating settings only');

    // Merge new config with existing settings
    const mergedConfig = {
      ...existingSettings,
      ...config,
    };

    setSettings(mergedConfig);
    logger.debug('Settings updated with merged configuration');

    // If user provides additional exporter config, we could add it to existing provider
    // For now, we just return since the provider is already set up
    return;
  }

  if (isConfigured()) {
    logger.warn('Lilypad SDK already configured. Skipping reconfiguration.');
    return;
  }

  // Set up auto instrumentation early if enabled
  logger.debug(`autoLlm config value: ${config.autoLlm}`);
  if (config.autoLlm) {
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
    logger.debug('autoLlm is disabled, skipping OpenAI instrumentation');
  }

  // Validate required config
  if (!config.apiKey || !config.projectId) {
    throw new Error('Lilypad SDK configuration requires apiKey and projectId.');
  }

  // Validate project ID format (UUIDs)
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (!config.projectId.match(uuidRegex)) {
    throw new Error('Invalid project ID format. Project ID should be a valid UUID.');
  }

  // Set default values with environment variable overrides
  const finalConfig: LilypadConfig = {
    baseUrl:
      process.env.LILYPAD_BASE_URL ||
      (process.env.LILYPAD_REMOTE_API_URL
        ? `${process.env.LILYPAD_REMOTE_API_URL}/v0`
        : config.baseUrl || BASE_URL),
    remoteClientUrl:
      process.env.LILYPAD_REMOTE_CLIENT_URL || config.remoteClientUrl || REMOTE_CLIENT_URL,
    logLevel: 'info',
    serviceName: 'lilypad-node-app',
    autoLlm: false,
    autoHttp: false,
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

  // Use shared context manager singleton
  getOrCreateContextManager();
  logger.debug('Using shared context manager');

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

export function setProvider(provider: NodeTracerProvider): void {
  _provider = provider;
}
