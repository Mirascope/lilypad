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

// Tracer provider instance for proper shutdown
let _provider: NodeTracerProvider | null = null;

export async function configure(config: LilypadConfig): Promise<void> {
  if (isConfigured()) {
    logger.warn('Lilypad SDK already configured. Skipping reconfiguration.');
    return;
  }

  // Validate required config
  if (!config.apiKey || !config.projectId) {
    throw new Error('Lilypad SDK configuration requires apiKey and projectId.');
  }

  // Validate API key format
  if (!config.apiKey.match(/^[a-zA-Z0-9-_]+$/)) {
    throw new Error(
      'Invalid API key format. API key should only contain alphanumeric characters, hyphens, and underscores.',
    );
  }

  // Validate project ID format (UUIDs)
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  if (!config.projectId.match(uuidRegex)) {
    throw new Error('Invalid project ID format. Project ID should be a valid UUID.');
  }

  // Set default values
  const finalConfig: LilypadConfig = {
    baseUrl: 'https://app.lilypad.so/api/v0',
    remoteClientUrl: 'https://app.lilypad.so',
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

  // Store settings
  setSettings(finalConfig);

  // Configure logger
  logger.setLevel(finalConfig.logLevel || 'info');

  // Create resource
  const resource = Resource.default().merge(
    new Resource({
      [SEMRESATTRS_SERVICE_NAME]: finalConfig.serviceName,
    }),
  );

  // Create and configure exporter
  const exporter = new JSONSpanExporter(finalConfig);
  const spanProcessor = new BatchSpanProcessor(exporter, finalConfig.batchProcessorOptions);

  // Create tracer provider with span processor
  const provider = new NodeTracerProvider({
    resource,
    idGenerator: new CryptoIdGenerator(),
    spanProcessors: [spanProcessor],
  });

  // Register as global tracer provider
  provider.register();

  // Store provider for shutdown
  _provider = provider;

  // Auto-instrument if configured
  if (finalConfig.auto_llm) {
    await instrumentLLMs();
  }

  logger.info(`Lilypad SDK configured successfully for project ${finalConfig.projectId}`);
}

async function instrumentLLMs(): Promise<void> {
  try {
    // Dynamically check for OpenAI and instrument if available
    const openai = await import('openai').catch(() => null);
    if (openai) {
      const { OpenAIInstrumentor } = await import('./instrumentors/openai');
      const instrumentor = new OpenAIInstrumentor();
      instrumentor.instrument();
      logger.debug('OpenAI instrumentation enabled');
    }
  } catch (error) {
    // Log warning but don't fail the entire configuration
    logger.warn(
      'OpenAI auto-instrumentation skipped:',
      error instanceof Error ? error.message : String(error),
    );
    logger.info('You can still use Lilypad without automatic OpenAI tracing.');
  }
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
