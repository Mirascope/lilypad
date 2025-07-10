import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { wrapAsyncGenerator, isAsyncIterable, isAsyncIterator } from './wrap-async-generator';
import { SpanStatusCode } from '@opentelemetry/api';
import { logger } from './logger';

// Mock the logger
vi.mock('./logger', () => ({
  logger: {
    debug: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}));

describe('wrap-async-generator', () => {
  const mockSpan = {
    isRecording: vi.fn(() => true),
    addEvent: vi.fn(),
    setAttribute: vi.fn(),
    setStatus: vi.fn(),
    recordException: vi.fn(),
    end: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('wrapAsyncGenerator', () => {
    it('should wrap a simple async generator', async () => {
      // Create a simple async generator
      async function* simpleGenerator() {
        yield 1;
        yield 2;
        yield 3;
      }

      const wrapped = wrapAsyncGenerator(mockSpan, simpleGenerator());
      const results: number[] = [];

      for await (const value of wrapped) {
        results.push(value);
      }

      expect(results).toEqual([1, 2, 3]);
      expect(mockSpan.setStatus).toHaveBeenCalledWith({ code: SpanStatusCode.OK });
      expect(mockSpan.setAttribute).toHaveBeenCalledWith('stream.total_chunks', 3);
      expect(mockSpan.end).toHaveBeenCalledOnce();
    });

    it('should handle onChunk callback', async () => {
      async function* generator() {
        yield 'chunk1';
        yield 'chunk2';
      }

      const chunks: Array<{ value: string; index: number }> = [];
      const onChunk = vi.fn((chunk: string, index: number) => {
        chunks.push({ value: chunk, index });
      });

      const wrapped = wrapAsyncGenerator(mockSpan, generator(), { onChunk });

      for await (const _ of wrapped) {
        // Just consume the generator
      }

      expect(onChunk).toHaveBeenCalledTimes(2);
      expect(chunks).toEqual([
        { value: 'chunk1', index: 0 },
        { value: 'chunk2', index: 1 },
      ]);
    });

    it('should handle onComplete callback', async () => {
      async function* generator() {
        yield 1;
        yield 2;
      }

      const onComplete = vi.fn();
      const wrapped = wrapAsyncGenerator(mockSpan, generator(), { onComplete });

      for await (const _ of wrapped) {
        // Just consume the generator
      }

      expect(onComplete).toHaveBeenCalledWith(2);
      expect(onComplete).toHaveBeenCalledOnce();
    });

    it('should record chunk events when enabled', async () => {
      async function* generator() {
        yield { data: 'test' };
        yield { data: 'test2' };
      }

      const wrapped = wrapAsyncGenerator(mockSpan, generator(), {
        recordChunkEvents: true,
      });

      for await (const _ of wrapped) {
        // Just consume the generator
      }

      expect(mockSpan.addEvent).toHaveBeenCalledTimes(2);
      expect(mockSpan.addEvent).toHaveBeenCalledWith('stream.chunk', {
        'chunk.index': 0,
        'chunk.size': expect.any(Number),
      });
      expect(mockSpan.addEvent).toHaveBeenCalledWith('stream.chunk', {
        'chunk.index': 1,
        'chunk.size': expect.any(Number),
      });
    });

    it('should handle errors in the generator', async () => {
      async function* errorGenerator() {
        yield 1;
        throw new Error('Generator error');
      }

      const onError = vi.fn();
      const wrapped = wrapAsyncGenerator(mockSpan, errorGenerator(), { onError });

      const results: number[] = [];
      await expect(async () => {
        for await (const value of wrapped) {
          results.push(value);
        }
      }).rejects.toThrow('Generator error');

      expect(results).toEqual([1]); // Should have yielded 1 before error
      expect(onError).toHaveBeenCalledWith(expect.objectContaining({ message: 'Generator error' }));
      expect(mockSpan.recordException).toHaveBeenCalled();
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'Generator error',
      });
      expect(mockSpan.end).toHaveBeenCalledOnce();
    });

    it('should handle errors in onChunk callback', async () => {
      async function* generator() {
        yield 1;
        yield 2;
      }

      const onChunk = vi.fn(() => {
        throw new Error('Callback error');
      });

      const wrapped = wrapAsyncGenerator(mockSpan, generator(), { onChunk });

      // Should not throw, just log warning
      const results: number[] = [];
      for await (const value of wrapped) {
        results.push(value);
      }

      expect(results).toEqual([1, 2]);
      expect(logger.warn).toHaveBeenCalledWith('Error in onChunk callback:', expect.any(Error));
      expect(mockSpan.setStatus).toHaveBeenCalledWith({ code: SpanStatusCode.OK });
      expect(mockSpan.end).toHaveBeenCalledOnce();
    });

    it('should handle errors in onComplete callback', async () => {
      async function* generator() {
        yield 1;
      }

      const onComplete = vi.fn(() => {
        throw new Error('Complete callback error');
      });

      const wrapped = wrapAsyncGenerator(mockSpan, generator(), { onComplete });

      for await (const _ of wrapped) {
        // Just consume
      }

      expect(logger.warn).toHaveBeenCalledWith('Error in onComplete callback:', expect.any(Error));
      expect(mockSpan.setStatus).toHaveBeenCalledWith({ code: SpanStatusCode.OK });
      expect(mockSpan.end).toHaveBeenCalledOnce();
    });

    it('should handle errors in onError callback', async () => {
      async function* generator() {
        yield 1; // Add a yield before throwing
        throw new Error('Generator error');
      }

      const onError = vi.fn(() => {
        throw new Error('Error callback error');
      });

      const wrapped = wrapAsyncGenerator(mockSpan, generator(), { onError });

      await expect(async () => {
        for await (const _ of wrapped) {
          // Try to consume
        }
      }).rejects.toThrow('Generator error');

      expect(logger.warn).toHaveBeenCalledWith('Error in onError callback:', expect.any(Error));
      expect(mockSpan.end).toHaveBeenCalledOnce();
    });

    it('should handle AsyncIterable input', async () => {
      const asyncIterable: AsyncIterable<string> = {
        async *[Symbol.asyncIterator]() {
          yield 'a';
          yield 'b';
        },
      };

      const wrapped = wrapAsyncGenerator(mockSpan, asyncIterable);
      const results: string[] = [];

      for await (const value of wrapped) {
        results.push(value);
      }

      expect(results).toEqual(['a', 'b']);
      expect(mockSpan.setStatus).toHaveBeenCalledWith({ code: SpanStatusCode.OK });
      expect(mockSpan.end).toHaveBeenCalledOnce();
    });

    it('should handle AsyncIterator input', async () => {
      let index = 0;
      const values = ['x', 'y', 'z'];
      const asyncIterator: AsyncIterator<string> = {
        async next() {
          if (index < values.length) {
            return { done: false, value: values[index++] };
          }
          return { done: true, value: undefined };
        },
      };

      const wrapped = wrapAsyncGenerator(mockSpan, asyncIterator);
      const results: string[] = [];

      for await (const value of wrapped) {
        results.push(value);
      }

      expect(results).toEqual(['x', 'y', 'z']);
      expect(mockSpan.setAttribute).toHaveBeenCalledWith('stream.total_chunks', 3);
      expect(mockSpan.end).toHaveBeenCalledOnce();
    });

    it('should not end span if already ended', async () => {
      mockSpan.isRecording.mockReturnValue(false);

      async function* generator() {
        yield 1;
      }

      const wrapped = wrapAsyncGenerator(mockSpan, generator());

      for await (const _ of wrapped) {
        // Just consume
      }

      expect(logger.debug).toHaveBeenCalledWith('Span already ended, skipping end() call');
      expect(mockSpan.end).not.toHaveBeenCalled();
    });

    it('should handle empty generator', async () => {
      async function* emptyGenerator() {
        // Yields nothing
      }

      const wrapped = wrapAsyncGenerator(mockSpan, emptyGenerator());
      const results: unknown[] = [];

      for await (const value of wrapped) {
        results.push(value);
      }

      expect(results).toEqual([]);
      expect(mockSpan.setAttribute).toHaveBeenCalledWith('stream.total_chunks', 0);
      expect(mockSpan.setStatus).toHaveBeenCalledWith({ code: SpanStatusCode.OK });
      expect(mockSpan.end).toHaveBeenCalledOnce();
    });

    it('should handle generator that yields undefined', async () => {
      async function* generator() {
        yield undefined;
        yield null;
        yield false;
        yield 0;
        yield '';
      }

      const wrapped = wrapAsyncGenerator(mockSpan, generator());
      const results: unknown[] = [];

      for await (const value of wrapped) {
        results.push(value);
      }

      expect(results).toEqual([undefined, null, false, 0, '']);
      expect(mockSpan.setAttribute).toHaveBeenCalledWith('stream.total_chunks', 5);
    });

    it('should handle multiple errors during iteration', async () => {
      let callCount = 0;
      const asyncIterator: AsyncIterator<number> = {
        async next() {
          callCount++;
          if (callCount === 1) {
            return { done: false, value: 1 };
          }
          throw new Error('Iterator error');
        },
      };

      const wrapped = wrapAsyncGenerator(mockSpan, asyncIterator);
      const results: number[] = [];

      await expect(async () => {
        for await (const value of wrapped) {
          results.push(value);
        }
      }).rejects.toThrow('Iterator error');

      expect(results).toEqual([1]);
      expect(mockSpan.recordException).toHaveBeenCalled();
      expect(mockSpan.end).toHaveBeenCalledOnce();
    });
  });

  describe('isAsyncIterable', () => {
    it('should return true for async iterables', () => {
      const asyncIterable = {
        async *[Symbol.asyncIterator]() {
          yield 1;
        },
      };

      expect(isAsyncIterable(asyncIterable)).toBe(true);
    });

    it('should return false for non-async iterables', () => {
      expect(isAsyncIterable(null)).toBe(false);
      expect(isAsyncIterable(undefined)).toBe(false);
      expect(isAsyncIterable({})).toBe(false);
      expect(isAsyncIterable([])).toBe(false);
      expect(isAsyncIterable('string')).toBe(false);
      expect(isAsyncIterable(123)).toBe(false);
      expect(isAsyncIterable({ [Symbol.iterator]: () => {} })).toBe(false);
    });

    it('should return false for objects with non-function asyncIterator', () => {
      expect(isAsyncIterable({ [Symbol.asyncIterator]: 'not a function' })).toBe(false);
      expect(isAsyncIterable({ [Symbol.asyncIterator]: null })).toBe(false);
    });
  });

  describe('isAsyncIterator', () => {
    it('should return true for async iterators', () => {
      const asyncIterator = {
        async next() {
          return { done: true, value: undefined };
        },
      };

      expect(isAsyncIterator(asyncIterator)).toBe(true);
    });

    it('should return false for non-async iterators', () => {
      expect(isAsyncIterator(null)).toBe(false);
      expect(isAsyncIterator(undefined)).toBe(false);
      expect(isAsyncIterator({})).toBe(false);
      expect(isAsyncIterator([])).toBe(false);
      expect(isAsyncIterator('string')).toBe(false);
      expect(isAsyncIterator(123)).toBe(false);
    });

    it('should return false for objects with non-function next', () => {
      expect(isAsyncIterator({ next: 'not a function' })).toBe(false);
      expect(isAsyncIterator({ next: null })).toBe(false);
    });

    it('should return true for objects with next function even if not truly async', () => {
      // This is a limitation of the type guard - it only checks for the presence of next()
      const syncIterator = {
        next() {
          return { done: true, value: undefined };
        },
      };

      expect(isAsyncIterator(syncIterator)).toBe(true);
    });
  });

  describe('integration scenarios', () => {
    it('should handle real-world streaming scenario', async () => {
      // Simulate a streaming response like from OpenAI
      async function* streamingResponse() {
        const chunks = [
          { choices: [{ delta: { content: 'Hello' } }] },
          { choices: [{ delta: { content: ' ' } }] },
          { choices: [{ delta: { content: 'world' } }] },
          { choices: [{ delta: { content: '!' } }] },
        ];

        for (const chunk of chunks) {
          await new Promise((resolve) => setTimeout(resolve, 10));
          yield chunk;
        }
      }

      const collectedContent: string[] = [];
      const wrapped = wrapAsyncGenerator(mockSpan, streamingResponse(), {
        onChunk: (chunk: any) => {
          const content = chunk.choices?.[0]?.delta?.content;
          if (content) {
            collectedContent.push(content);
          }
        },
        recordChunkEvents: true,
      });

      for await (const _ of wrapped) {
        // Just consume
      }

      expect(collectedContent.join('')).toBe('Hello world!');
      expect(mockSpan.addEvent).toHaveBeenCalledTimes(4);
      expect(mockSpan.setAttribute).toHaveBeenCalledWith('stream.total_chunks', 4);
    });

    it('should handle early termination with break', async () => {
      async function* generator() {
        yield 1;
        yield 2;
        yield 3;
        yield 4;
        yield 5;
      }

      const wrapped = wrapAsyncGenerator(mockSpan, generator());
      const results: number[] = [];

      for await (const value of wrapped) {
        results.push(value);
        if (value === 3) {
          break;
        }
      }

      expect(results).toEqual([1, 2, 3]);
      // Span should still be ended properly
      expect(mockSpan.end).toHaveBeenCalledOnce();
      // When breaking early, the generator doesn't complete normally
      // so setStatus is not called with OK
      expect(mockSpan.setStatus).not.toHaveBeenCalled();
    });

    it('should handle early termination with return', async () => {
      async function* generator() {
        yield 'a';
        yield 'b';
        yield 'c';
      }

      const wrapped = wrapAsyncGenerator(mockSpan, generator());

      const processStream = async () => {
        for await (const value of wrapped) {
          if (value === 'b') {
            return 'early-exit';
          }
        }
        return 'completed';
      };

      const result = await processStream();
      expect(result).toBe('early-exit');
      expect(mockSpan.end).toHaveBeenCalledOnce();
      // Early return also means the generator doesn't complete normally
      expect(mockSpan.setStatus).not.toHaveBeenCalled();
    });
  });
});
