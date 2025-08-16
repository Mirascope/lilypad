import { trace } from '@opentelemetry/api';
import {
  ConsoleSpanExporter,
  SimpleSpanProcessor,
} from '@opentelemetry/sdk-trace-base';
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { CryptoIdGenerator } from './utils/id-generator';

export interface LilypadConfig {
  mode?: 'debug';
}

let configured = false;
let tracerProvider: NodeTracerProvider | null = null;

export function configure(config: LilypadConfig = {}): void {
  if (configured) {
    console.error('TracerProvider already initialized.');
    return;
  }

  if (config.mode && config.mode !== 'debug') {
    throw new Error(
      `Invalid mode: ${config.mode}. Must be 'debug' or undefined.`
    );
  }

  if (config.mode === 'debug') {
    console.debug('Configuring lilypad SDK in debug mode.');

    try {
      const exporter = new ConsoleSpanExporter();
      const processor = new SimpleSpanProcessor(exporter);

      tracerProvider = new NodeTracerProvider({
        idGenerator: new CryptoIdGenerator(),
        spanProcessors: [processor],
      });

      tracerProvider.register();

      configured = true;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      throw new Error(`Failed to configure Lilypad SDK: ${errorMessage}`);
    }
  }
}

export function getTracer(name = 'lilypad') {
  return trace.getTracer(name);
}
