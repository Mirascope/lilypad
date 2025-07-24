import type { Span } from '@opentelemetry/api';

/**
 * Wrapper for streaming responses to collect chunks and finalize span
 */
export class StreamWrapper<T> {
  private chunks: T[] = [];
  private span: Span;
  private originalStream: AsyncIterable<T>;
  private onChunk?: (chunk: T) => void;
  private onFinalize?: (chunks: T[]) => void;

  constructor(
    originalStream: AsyncIterable<T>,
    span: Span,
    options?: {
      onChunk?: (chunk: T) => void;
      onFinalize?: (chunks: T[]) => void;
    },
  ) {
    this.originalStream = originalStream;
    this.span = span;
    this.onChunk = options?.onChunk;
    this.onFinalize = options?.onFinalize;
  }

  async *[Symbol.asyncIterator](): AsyncIterator<T> {
    try {
      for await (const chunk of this.originalStream) {
        this.chunks.push(chunk);
        if (this.onChunk) {
          this.onChunk(chunk);
        }
        yield chunk;
      }
    } catch (error) {
      // Record error in span
      const errorMessage = error instanceof Error ? error.message : String(error);
      this.span.recordException(error as Error);
      this.span.setAttributes({
        'lilypad.trace.error': errorMessage,
        error: true,
      });
      throw error;
    } finally {
      // Finalize the span with collected data
      if (this.onFinalize) {
        this.onFinalize(this.chunks);
      }
    }
  }

  /**
   * Get all collected chunks
   */
  getChunks(): T[] {
    return this.chunks;
  }
}

/**
 * Check if a value is an async iterable
 */
export function isAsyncIterable<T = unknown>(value: unknown): value is AsyncIterable<T> {
  return (
    value != null &&
    typeof value === 'object' &&
    Symbol.asyncIterator in value &&
    typeof (value as AsyncIterable<T>)[Symbol.asyncIterator] === 'function'
  );
}
