import { describe, it, expect, vi } from 'vitest';
import { StreamWrapper, isAsyncIterable } from './stream-wrapper';
import type { Span } from '@opentelemetry/api';

describe('StreamWrapper', () => {
  const mockSpan: Span = {
    recordException: vi.fn(),
    setAttributes: vi.fn(),
    end: vi.fn(),
  } as any;

  async function* createMockStream<T>(items: T[], shouldThrow = false): AsyncIterable<T> {
    for (let i = 0; i < items.length; i++) {
      if (shouldThrow && i === Math.floor(items.length / 2)) {
        throw new Error('Stream error');
      }
      yield items[i];
    }
  }

  describe('basic streaming', () => {
    it('should pass through stream items', async () => {
      const items = [1, 2, 3, 4, 5];
      const stream = createMockStream(items);
      const wrapper = new StreamWrapper(stream, mockSpan);

      const collected = [];
      for await (const item of wrapper) {
        collected.push(item);
      }

      expect(collected).toEqual(items);
    });

    it('should collect chunks', async () => {
      const items = ['a', 'b', 'c'];
      const stream = createMockStream(items);
      const wrapper = new StreamWrapper(stream, mockSpan);

      const collected = [];
      for await (const item of wrapper) {
        collected.push(item);
      }

      expect(wrapper.getChunks()).toEqual(items);
    });
  });

  describe('callbacks', () => {
    it('should call onChunk for each item', async () => {
      const items = [1, 2, 3];
      const stream = createMockStream(items);
      const onChunk = vi.fn();

      const wrapper = new StreamWrapper(stream, mockSpan, { onChunk });

      for await (const _ of wrapper) {
        // Consume stream
      }

      expect(onChunk).toHaveBeenCalledTimes(3);
      expect(onChunk).toHaveBeenCalledWith(1);
      expect(onChunk).toHaveBeenCalledWith(2);
      expect(onChunk).toHaveBeenCalledWith(3);
    });

    it('should call onFinalize with all chunks', async () => {
      const items = ['x', 'y', 'z'];
      const stream = createMockStream(items);
      const onFinalize = vi.fn();

      const wrapper = new StreamWrapper(stream, mockSpan, { onFinalize });

      for await (const _ of wrapper) {
        // Consume stream
      }

      expect(onFinalize).toHaveBeenCalledTimes(1);
      expect(onFinalize).toHaveBeenCalledWith(items);
    });
  });

  describe('error handling', () => {
    it('should handle stream errors', async () => {
      const items = [1, 2, 3, 4];
      const stream = createMockStream(items, true); // Will throw in the middle
      const wrapper = new StreamWrapper(stream, mockSpan);

      await expect(async () => {
        const collected = [];
        for await (const item of wrapper) {
          collected.push(item);
        }
      }).rejects.toThrow('Stream error');

      expect(mockSpan.recordException).toHaveBeenCalled();
      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'lilypad.trace.error': 'Stream error',
        error: true,
      });
    });

    it('should still call onFinalize after error', async () => {
      const items = [1, 2, 3];
      const stream = createMockStream(items, true);
      const onFinalize = vi.fn();
      const wrapper = new StreamWrapper(stream, mockSpan, { onFinalize });

      try {
        for await (const _ of wrapper) {
          // Will throw
        }
      } catch {
        // Expected
      }

      expect(onFinalize).toHaveBeenCalled();
      // Should have collected chunks before error
      expect(onFinalize.mock.calls[0][0].length).toBeGreaterThan(0);
    });
  });
});

describe('isAsyncIterable', () => {
  it('should return true for async iterables', () => {
    async function* generator() {
      yield 1;
    }

    expect(isAsyncIterable(generator())).toBe(true);
  });

  it('should return false for non-async iterables', () => {
    expect(isAsyncIterable(null)).toBe(false);
    expect(isAsyncIterable(undefined)).toBe(false);
    expect(isAsyncIterable(42)).toBe(false);
    expect(isAsyncIterable('string')).toBe(false);
    expect(isAsyncIterable([])).toBe(false);
    expect(isAsyncIterable({})).toBe(false);
  });

  it('should return false for sync iterables', () => {
    function* syncGenerator() {
      yield 1;
    }

    expect(isAsyncIterable(syncGenerator())).toBe(false);
  });

  it('should check for Symbol.asyncIterator', () => {
    const fakeAsyncIterable = {
      [Symbol.asyncIterator]: () => ({
        next: async () => ({ done: true, value: undefined }),
      }),
    };

    expect(isAsyncIterable(fakeAsyncIterable)).toBe(true);
  });
});
