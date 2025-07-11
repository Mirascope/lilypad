/**
 * Generic wrapper for AsyncGenerator/AsyncIterable streams with OpenTelemetry tracing
 *
 * This utility ensures proper span lifecycle management for streaming responses,
 * ending the span only when the stream is fully consumed or errors.
 */

import { Span as OTelSpan, SpanStatusCode } from '@opentelemetry/api';
import { logger } from './logger';

/**
 * Options for wrapping async generators
 */
export interface WrapAsyncGeneratorOptions<T> {
  /**
   * Called for each chunk yielded by the generator
   */
  onChunk?: (chunk: T, index: number) => void;

  /**
   * Called when the generator completes successfully
   */
  onComplete?: (totalChunks: number) => void;

  /**
   * Called if the generator throws an error
   */
  onError?: (error: Error) => void;

  /**
   * Whether to record chunk details as span events
   * @default false
   */
  recordChunkEvents?: boolean;
}

/**
 * Wraps an AsyncGenerator/AsyncIterable to properly manage OpenTelemetry span lifecycle
 *
 * @param span - The OpenTelemetry span to manage
 * @param generator - The async generator to wrap
 * @param options - Optional callbacks and configuration
 * @returns Wrapped async generator that manages span lifecycle
 *
 * @example
 * ```typescript
 * const stream = await openai.chat.completions.create({ stream: true });
 * const wrappedStream = wrapAsyncGenerator(span, stream, {
 *   onChunk: (chunk) => console.log('Chunk:', chunk),
 *   onComplete: (total) => span.setAttribute('stream.chunks', total),
 *   recordChunkEvents: true
 * });
 *
 * for await (const chunk of wrappedStream) {
 *   // Process chunk - span will end automatically when done
 * }
 * ```
 */
export async function* wrapAsyncGenerator<T>(
  span: OTelSpan,
  generator: AsyncIterable<T> | AsyncIterator<T>,
  options: WrapAsyncGeneratorOptions<T> = {},
): AsyncGenerator<T> {
  const { onChunk, onComplete, onError, recordChunkEvents = false } = options;

  let chunkIndex = 0;
  let errorOccurred = false;

  try {
    // Ensure we have an async iterator
    const iterator =
      Symbol.asyncIterator in generator
        ? (generator as AsyncIterable<T>)[Symbol.asyncIterator]()
        : (generator as AsyncIterator<T>);

    // Process chunks
    while (true) {
      try {
        const { done, value } = await iterator.next();

        if (done) {
          logger.debug(`Stream completed after ${chunkIndex} chunks`);
          break;
        }

        // Record chunk event if enabled
        if (recordChunkEvents) {
          span.addEvent('stream.chunk', {
            'chunk.index': chunkIndex,
            'chunk.size': JSON.stringify(value).length,
          });
        }

        // Call chunk callback if provided
        if (onChunk) {
          try {
            onChunk(value, chunkIndex);
          } catch (callbackError) {
            logger.warn('Error in onChunk callback:', callbackError);
          }
        }

        chunkIndex++;
        yield value;
      } catch (iteratorError) {
        // Error during iteration
        errorOccurred = true;
        const error = iteratorError as Error;

        logger.error('Error during stream iteration:', error);
        span.recordException(error);
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: error.message,
        });

        if (onError) {
          try {
            onError(error);
          } catch (callbackError) {
            logger.warn('Error in onError callback:', callbackError);
          }
        }

        throw error;
      }
    }

    // Stream completed successfully
    if (!errorOccurred) {
      span.setStatus({ code: SpanStatusCode.OK });
      span.setAttribute('stream.total_chunks', chunkIndex);

      if (onComplete) {
        try {
          onComplete(chunkIndex);
        } catch (callbackError) {
          logger.warn('Error in onComplete callback:', callbackError);
        }
      }
    }
  } finally {
    // Always end the span when iteration completes or errors
    if (!span.isRecording()) {
      logger.debug('Span already ended, skipping end() call');
    } else {
      logger.debug(`Ending span after processing ${chunkIndex} chunks`);
      span.end();
    }
  }
}

/**
 * Type guard to check if a value is an AsyncIterable
 */
export function isAsyncIterable<T>(value: unknown): value is AsyncIterable<T> {
  return value != null && typeof value[Symbol.asyncIterator] === 'function';
}

/**
 * Type guard to check if a value is an AsyncIterator
 */
export function isAsyncIterator<T>(value: unknown): value is AsyncIterator<T> {
  return value != null && typeof value.next === 'function';
}
