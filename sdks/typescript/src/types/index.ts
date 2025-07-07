export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export type Propagator = 'tracecontext' | 'b3' | 'b3multi' | 'jaeger' | 'composite';

export interface LilypadConfig {
  /**
   * Your Lilypad API key
   */
  apiKey: string;

  /**
   * Your Lilypad project ID
   */
  projectId: string;

  /**
   * Base URL for Lilypad API (defaults to hosted service)
   */
  baseUrl?: string;

  /**
   * Remote client URL for viewing traces
   */
  remoteClientUrl?: string;

  /**
   * Logging level
   * @default 'info'
   */
  logLevel?: LogLevel;

  /**
   * Service name for telemetry
   * @default 'lilypad-node-app'
   */
  serviceName?: string;

  /**
   * Automatically instrument LLM libraries (OpenAI, Anthropic, etc.)
   * @default false
   */
  auto_llm?: boolean;

  /**
   * Trace propagation format
   * - 'tracecontext': W3C Trace Context (default)
   * - 'b3': Zipkin B3 Single Format
   * - 'b3multi': Zipkin B3 Multi Format
   * - 'jaeger': Jaeger format
   * - 'composite': All formats for maximum compatibility
   */
  propagator?: Propagator;

  /**
   * Automatically instrument all HTTP clients
   * @default false
   */
  auto_http?: boolean;

  /**
   * If true, preserve existing OpenTelemetry propagator settings
   * @default false
   */
  preserveExistingPropagator?: boolean;

  /**
   * Batch processor options for span export
   */
  batchProcessorOptions?: {
    /**
     * The delay interval in milliseconds between two consecutive exports
     * @default 5000
     */
    scheduledDelayMillis?: number;

    /**
     * The maximum queue size
     * @default 2048
     */
    maxQueueSize?: number;

    /**
     * The maximum batch size
     * @default 512
     */
    maxExportBatchSize?: number;

    /**
     * How long the export can run before it is cancelled
     * @default 30000
     */
    exportTimeoutMillis?: number;
  };
}

export interface ExporterConfig {
  apiKey: string;
  projectId: string;
  baseUrl: string;
  remoteClientUrl?: string;
  maxRetries?: number;
  initialBackoffMs?: number;
  maxBackoffMs?: number;
  backoffMultiplier?: number;
  queueSize?: number;
  requestTimeoutMs?: number;
}

export interface InstrumentorBase {
  instrument(): void;
  uninstrument(): void;
  isInstrumented(): boolean;
}

// Re-export types from other files
export * from './openai';
export * from './span';
