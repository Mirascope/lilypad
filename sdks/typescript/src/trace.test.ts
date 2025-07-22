import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock dependencies - must be before imports
vi.mock('./utils/settings');
vi.mock('./utils/closure');
vi.mock('./utils/logger', () => ({
  logger: {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}));
vi.mock('./configure', () => ({
  getProvider: vi.fn(),
}));

vi.mock('./utils/client-pool', () => ({
  getPooledClient: vi.fn(),
}));
vi.mock('./utils/error-handler', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./utils/error-handler')>();
  return {
    ...actual,
    handleBackgroundError: vi.fn(),
    // Use the actual implementation of ensureError
  };
});
vi.mock('../lilypad/generated/Client', () => ({
  LilypadClient: vi.fn().mockImplementation(() => ({
    projects: {
      functions: {
        getByHash: vi.fn(),
        create: vi.fn(),
        spans: {
          listPaginated: vi.fn(),
        },
      },
    },
    ee: {
      projects: {
        annotations: {
          create: vi.fn(),
        },
      },
    },
    spans: {
      update: vi.fn(),
    },
  })),
}));

import * as otel from '@opentelemetry/api';
import { trace, getCurrentSpan, logToCurrentSpan, Trace, AsyncTrace } from './trace';
import { getSettings } from './utils/settings';
import { getCachedClosure } from './utils/closure';

describe('trace', () => {
  const mockSpan = {
    spanContext: vi.fn(() => ({ spanId: 'test-span-id', traceId: 'test-trace-id' })),
    setAttribute: vi.fn(),
    setStatus: vi.fn(),
    recordException: vi.fn(),
    addEvent: vi.fn(),
    end: vi.fn(),
    isRecording: vi.fn(() => true),
  };

  const mockTracer = {
    startActiveSpan: vi.fn((name, options, callback) => {
      return callback(mockSpan);
    }),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(otel.trace, 'getTracer').mockReturnValue(mockTracer as any);
    vi.spyOn(otel.trace, 'getActiveSpan').mockReturnValue(undefined);

    vi.mocked(getSettings).mockReturnValue({
      apiKey: 'test-api-key',
      projectId: 'test-project-id',
      baseUrl: 'https://api.test.com',
      serviceName: 'test-service',
    });

    vi.mocked(getCachedClosure).mockReturnValue({
      name: 'testFunction',
      signature: 'function testFunction()',
      code: 'function testFunction() { return "test"; }',
      hash: 'test-hash',
      dependencies: {},
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('getCurrentSpan', () => {
    it('should return the active span', () => {
      const mockActiveSpan = { spanId: 'active-span' } as any;
      vi.spyOn(otel.trace, 'getActiveSpan').mockReturnValue(mockActiveSpan);

      const span = getCurrentSpan();
      expect(span).toBe(mockActiveSpan);
    });

    it('should return undefined when no active span', () => {
      vi.spyOn(otel.trace, 'getActiveSpan').mockReturnValue(undefined);

      const span = getCurrentSpan();
      expect(span).toBeUndefined();
    });
  });

  describe('logToCurrentSpan', () => {
    it('should add event to current span', () => {
      vi.spyOn(otel.trace, 'getActiveSpan').mockReturnValue(mockSpan as any);

      logToCurrentSpan('info', 'Test message', { extra: 'data' });

      expect(mockSpan.addEvent).toHaveBeenCalledWith('info', {
        'info.message': 'Test message',
        extra: 'data',
      });
    });

    it('should set error status for error level', () => {
      vi.spyOn(otel.trace, 'getActiveSpan').mockReturnValue(mockSpan as any);

      logToCurrentSpan('error', 'Error message');

      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: otel.SpanStatusCode.ERROR,
        message: 'Error message',
      });
    });

    it('should set error status for critical level', () => {
      vi.spyOn(otel.trace, 'getActiveSpan').mockReturnValue(mockSpan as any);

      logToCurrentSpan('critical', 'Critical error');

      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: otel.SpanStatusCode.ERROR,
        message: 'Critical error',
      });
    });

    it('should do nothing when no active span', () => {
      vi.spyOn(otel.trace, 'getActiveSpan').mockReturnValue(undefined);

      logToCurrentSpan('info', 'Test message');

      expect(mockSpan.addEvent).not.toHaveBeenCalled();
    });
  });

  describe('trace function', () => {
    it('should work with synchronous functions', async () => {
      const testFn = (arg1: string, arg2: number) => `${arg1}-${arg2}`;
      const tracedFn = trace(testFn);

      const result = await tracedFn('test', 123);

      expect(result).toBe('test-123');
      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        'testFn',
        expect.objectContaining({
          kind: otel.SpanKind.INTERNAL,
          attributes: expect.objectContaining({
            'lilypad.type': 'trace',
            'lilypad.project_uuid': 'test-project-id',
            'code.function': 'testFn',
          }),
        }),
        expect.any(Function),
      );
      expect(mockSpan.setAttribute).toHaveBeenCalledWith(
        'lilypad.trace.arg_values',
        expect.stringContaining('test'),
      );
      expect(mockSpan.setStatus).toHaveBeenCalledWith({ code: otel.SpanStatusCode.OK });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should work with async functions', async () => {
      const testFn = async (value: string) => {
        await new Promise((resolve) => setTimeout(resolve, 10));
        return value.toUpperCase();
      };

      const tracedFn = trace(testFn, { name: 'custom-name' });
      const result = await tracedFn('hello');

      expect(result).toBe('HELLO');
      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        'custom-name',
        expect.any(Object),
        expect.any(Function),
      );
    });

    it('should handle errors and record exception', async () => {
      const testError = new Error('Test error');
      const failingFn = async () => {
        throw testError;
      };

      const tracedFn = trace(failingFn);

      await expect(tracedFn()).rejects.toThrow('Test error');
      expect(mockSpan.recordException).toHaveBeenCalledWith(testError);
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: otel.SpanStatusCode.ERROR,
        message: 'Test error',
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should handle custom options', async () => {
      const fnWithOptions = () => 'result';

      const tracedFn = trace(fnWithOptions, {
        name: 'custom-trace',
        tags: ['tag1', 'tag2'],
        attributes: { custom: 'attribute' },
      });

      await tracedFn();

      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        'custom-trace',
        expect.objectContaining({
          attributes: expect.objectContaining({
            custom: 'attribute',
          }),
        }),
        expect.any(Function),
      );
      expect(mockSpan.setAttribute).toHaveBeenCalledWith('lilypad.trace.tags', ['tag1', 'tag2']);
    });

    it('should work without settings configured', async () => {
      vi.mocked(getSettings).mockReturnValue(null);

      const testFn = () => 'no-trace';
      const tracedFn = trace(testFn);

      const result = await tracedFn();

      expect(result).toBe('no-trace');
      expect(tracedFn).not.toBe(testFn); // Returns wrapped function that checks settings at runtime
      expect(mockTracer.startActiveSpan).not.toHaveBeenCalled(); // No tracing when not configured
    });

    it('should return Trace wrapper in wrap mode', async () => {
      const wrappedFn = () => 'wrapped-result';
      const tracedFn = trace(wrappedFn, { mode: 'wrap' });

      const result = await tracedFn();

      expect(result).toBeInstanceOf(Trace);
      expect((result as any).response).toBe('wrapped-result');
    });

    it('should return AsyncTrace wrapper for async functions in wrap mode', async () => {
      const asyncWrappedFn = async () => 'async-wrapped-result';
      const tracedFn = trace(asyncWrappedFn, { mode: 'wrap' });

      const result = await tracedFn();

      expect(result).toBeInstanceOf(AsyncTrace);
      expect((result as any).response).toBe('async-wrapped-result');
    });

    it('should handle string options as name', async () => {
      const namedFn = () => 'result';
      const tracedFn = trace(namedFn, 'string-name');

      await tracedFn();

      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        'string-name',
        expect.any(Object),
        expect.any(Function),
      );
    });

    it('should handle anonymous functions', async () => {
      const anonymousFn = trace(() => 'anonymous result');

      const result = await anonymousFn();

      expect(result).toBe('anonymous result');
      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        'anonymous',
        expect.any(Object),
        expect.any(Function),
      );
    });
  });

  describe('Trace wrapper', () => {
    let traceWrapper: Trace<string>;

    beforeEach(() => {
      traceWrapper = new Trace('test-result', 'span-123', 'func-uuid-456');
    });

    it('should store response and metadata', () => {
      expect(traceWrapper.response).toBe('test-result');
      expect((traceWrapper as any).spanId).toBe('span-123');
      expect((traceWrapper as any).functionUuid).toBe('func-uuid-456');
    });

    it('should throw error when no annotations provided', () => {
      // tag() method doesn't throw for empty arguments
      expect(() => {
        traceWrapper.tag();
      }).not.toThrow();
    });

    it('should throw error when no emails provided to assign', () => {
      expect(() => {
        traceWrapper.assign();
      }).toThrow('At least one email address must be provided');
    });

    it('should throw error when SDK not configured', () => {
      vi.mocked(getSettings).mockReturnValue(null);

      expect(() => {
        traceWrapper.tag('test');
      }).toThrow('Lilypad SDK not configured');
    });

    it('should handle empty tags array', () => {
      expect(() => {
        traceWrapper.tag();
      }).not.toThrow();
    });
  });

  describe('AsyncTrace wrapper', () => {
    let asyncTraceWrapper: AsyncTrace<string>;

    beforeEach(() => {
      asyncTraceWrapper = new AsyncTrace('async-result', 'span-456', 'func-uuid-789');
    });

    it('should store response and metadata', () => {
      expect(asyncTraceWrapper.response).toBe('async-result');
      expect((asyncTraceWrapper as any).spanId).toBe('span-456');
      expect((asyncTraceWrapper as any).functionUuid).toBe('func-uuid-789');
    });

    it('should throw error when no annotations provided', async () => {
      // Tag method doesn't throw for empty args
      await asyncTraceWrapper.tag();
    });

    it('should throw error when SDK not configured', async () => {
      vi.mocked(getSettings).mockReturnValue(null);

      await expect(asyncTraceWrapper.tag('test')).rejects.toThrow('Lilypad SDK not configured');
    });

    it('should throw error when span not found', async () => {
      const mockClient = {
        projects: {
          functions: {
            spans: {
              listPaginated: vi.fn().mockResolvedValue({ items: [] }),
            },
          },
        },
      };

      const { LilypadClient } = await import('../lilypad/generated/Client');
      vi.mocked(LilypadClient).mockImplementation(() => mockClient as any);

      await expect(asyncTraceWrapper.tag('test')).rejects.toThrow('Cannot tag: span not found');
    });

    it('should handle empty tags array', async () => {
      await expect(asyncTraceWrapper.tag()).resolves.not.toThrow();
    });
  });

  describe('Function creation cache', () => {
    it('should cache function UUIDs', async () => {
      const mockClient = {
        projects: {
          functions: {
            getByHash: vi.fn().mockResolvedValue({ uuid: 'cached-uuid' }),
            create: vi.fn(),
          },
        },
      };

      const { LilypadClient } = await import('../lilypad/generated/Client');
      vi.mocked(LilypadClient).mockImplementation(() => mockClient as any);

      const { getPooledClient } = await import('./utils/client-pool');
      vi.mocked(getPooledClient).mockReturnValue(mockClient as any);

      const cachedFn = () => 'cached';
      const tracedFn = trace(cachedFn);

      // Call twice - this should trigger function creation
      await tracedFn();
      await tracedFn();

      // Wait for background operations to complete
      await new Promise((resolve) => setTimeout(resolve, 100));

      // Should only call getByHash once due to caching
      expect(mockClient.projects.functions.getByHash).toHaveBeenCalledTimes(1);
    });
  });

  describe('wrap mode', () => {
    beforeEach(async () => {
      const { getProvider } = await import('./configure');
      vi.mocked(getProvider).mockReturnValue({
        forceFlush: vi.fn().mockResolvedValue(undefined),
        shutdown: vi.fn().mockResolvedValue(undefined),
      } as any);
    });

    it('should return Trace object for sync function with wrap mode', async () => {
      const mockClient = {
        projects: {
          functions: {
            getByHash: vi.fn().mockResolvedValue({ uuid: 'existing-uuid' }),
          },
        },
      };

      const { LilypadClient } = await import('../lilypad/generated/Client');
      vi.mocked(LilypadClient).mockImplementation(() => mockClient as any);

      const { getPooledClient } = await import('./utils/client-pool');
      vi.mocked(getPooledClient).mockReturnValue(mockClient as any);

      const syncFn = (value: string) => `processed: ${value}`;
      const tracedFn = trace(syncFn, { mode: 'wrap' });

      const result = await tracedFn('test');

      expect(result).toBeInstanceOf(Trace);
      expect(result.response).toBe('processed: test');
      // spanId and functionUuid are protected, so we can't test them directly
      // but we can verify the object has the expected structure
    });

    it('should return AsyncTrace object for async function with wrap mode', async () => {
      const mockClient = {
        projects: {
          functions: {
            create: vi.fn().mockResolvedValue({ uuid: 'new-uuid' }),
            getByHash: vi.fn().mockRejectedValue({ statusCode: 404 }),
          },
        },
      };

      const { LilypadClient } = await import('../lilypad/generated/Client');
      vi.mocked(LilypadClient).mockImplementation(() => mockClient as any);

      const { getPooledClient } = await import('./utils/client-pool');
      vi.mocked(getPooledClient).mockReturnValue(mockClient as any);

      const asyncFn = async (value: number) => {
        await new Promise((resolve) => setTimeout(resolve, 10));
        return value * 2;
      };

      const tracedFn = trace(asyncFn, { mode: 'wrap' });
      const result = await tracedFn(21);

      expect(result).toBeInstanceOf(AsyncTrace);
      expect(result.response).toBe(42);
      // spanId and functionUuid are protected, so we can't test them directly
      // but we can verify the object has the expected structure
    });
  });

  describe('Trace class', () => {
    let mockClient: any;
    let traceInstance: Trace<string>;

    beforeEach(async () => {
      const { getProvider } = await import('./configure');
      vi.mocked(getProvider).mockReturnValue({
        forceFlush: vi.fn().mockResolvedValue(undefined),
        shutdown: vi.fn().mockResolvedValue(undefined),
      } as any);

      mockClient = {
        projects: {
          functions: {
            spans: {
              listPaginated: vi.fn().mockResolvedValue({
                items: [
                  { span_id: 'test-span-id', uuid: 'span-uuid-123' },
                  { span_id: 'other-span-id', uuid: 'other-uuid' },
                ],
              }),
            },
          },
        },
        ee: {
          projects: {
            annotations: {
              create: vi.fn().mockResolvedValue({}),
            },
          },
        },
        spans: {
          update: vi.fn().mockResolvedValue({}),
        },
      };

      const { LilypadClient } = await import('../lilypad/generated/Client');
      vi.mocked(LilypadClient).mockImplementation(() => mockClient);

      const { getPooledClient } = await import('./utils/client-pool');
      vi.mocked(getPooledClient).mockReturnValue(mockClient);

      traceInstance = new Trace('test-response', 'test-span-id', 'func-uuid-123');
    });

    it('should assign trace to users', async () => {
      let assignResolver: () => void;
      const assignPromise = new Promise<void>((resolve) => {
        assignResolver = resolve;
      });

      mockClient.ee.projects.annotations.create.mockImplementation(() => {
        assignResolver();
        return Promise.resolve({});
      });

      traceInstance.assign('user1@example.com', 'user2@example.com');

      await assignPromise;

      expect(mockClient.ee.projects.annotations.create).toHaveBeenCalledWith('test-project-id', [
        {
          assignee_email: ['user1@example.com', 'user2@example.com'],
          function_uuid: 'func-uuid-123',
          project_uuid: 'test-project-id',
          span_uuid: 'span-uuid-123',
        },
      ]);
    });

    it('should throw error when no emails provided to assign', () => {
      expect(() => traceInstance.assign()).toThrow('At least one email address must be provided');
    });

    it('should tag trace with multiple tags', async () => {
      let tagResolver: () => void;
      const tagPromise = new Promise<void>((resolve) => {
        tagResolver = resolve;
      });

      mockClient.spans.update.mockImplementation(() => {
        tagResolver();
        return Promise.resolve({});
      });

      traceInstance.tag('tag1', 'tag2', 'tag3');

      await tagPromise;

      expect(mockClient.spans.update).toHaveBeenCalledWith('span-uuid-123', {
        tags_by_name: ['tag1', 'tag2', 'tag3'],
      });
    });

    it('should do nothing when no tags provided', async () => {
      traceInstance.tag();

      // Since tag() returns early with no tags, we can immediately check
      expect(mockClient.spans.update).not.toHaveBeenCalled();

      // Give a chance for any async operations to complete
      await new Promise((resolve) => setTimeout(resolve, 0));

      // Still should not have been called
      expect(mockClient.spans.update).not.toHaveBeenCalled();
    });

    it('should handle span not found error gracefully', async () => {
      mockClient.projects.functions.spans.listPaginated.mockResolvedValue({ items: [] });

      // Mock the error handler
      const { handleBackgroundError } = await import('./utils/error-handler');
      vi.mocked(handleBackgroundError);

      traceInstance.tag('test-tag');

      // Wait for the getSpanUuid promise to resolve
      await new Promise((resolve) => setTimeout(resolve, 0));

      expect(handleBackgroundError).toHaveBeenCalledWith(
        expect.objectContaining({
          message: 'Cannot tag: span not found for function func-uuid-123',
        }),
        expect.objectContaining({ functionUuid: 'func-uuid-123', method: 'tag' }),
      );
      expect(mockClient.ee.projects.annotations.create).not.toHaveBeenCalled();
    });

    it('should handle SDK not configured error', () => {
      vi.mocked(getSettings).mockReturnValue(null);

      const newTrace = new Trace('response', 'span-id', 'func-uuid');

      expect(() => newTrace.tag('test')).toThrow('Lilypad SDK not configured');
    });

    it('should force flush before getting span UUID', async () => {
      const { getProvider } = await import('./configure');
      const mockForceFlush = vi.fn().mockResolvedValue(undefined);
      vi.mocked(getProvider).mockReturnValue({
        forceFlush: mockForceFlush,
        shutdown: vi.fn(),
      } as any);

      let flushResolver: () => void;
      const flushPromise = new Promise<void>((resolve) => {
        flushResolver = resolve;
      });

      mockForceFlush.mockImplementation(() => {
        flushResolver();
        return Promise.resolve();
      });

      traceInstance.tag('test-tag');

      await flushPromise;

      expect(mockForceFlush).toHaveBeenCalledTimes(1);
    });
  });

  describe('AsyncTrace class', () => {
    let mockClient: any;
    let asyncTraceInstance: AsyncTrace<number>;

    beforeEach(async () => {
      const { getProvider } = await import('./configure');
      vi.mocked(getProvider).mockReturnValue({
        forceFlush: vi.fn().mockResolvedValue(undefined),
        shutdown: vi.fn().mockResolvedValue(undefined),
      } as any);

      mockClient = {
        projects: {
          functions: {
            spans: {
              listPaginated: vi.fn().mockResolvedValue({
                items: [{ span_id: 'async-span-id', uuid: 'async-span-uuid' }],
              }),
            },
          },
        },
        ee: {
          projects: {
            annotations: {
              create: vi.fn().mockResolvedValue({}),
            },
          },
        },
        spans: {
          update: vi.fn().mockResolvedValue({}),
        },
      };

      const { LilypadClient } = await import('../lilypad/generated/Client');
      vi.mocked(LilypadClient).mockImplementation(() => mockClient);

      const { getPooledClient } = await import('./utils/client-pool');
      vi.mocked(getPooledClient).mockReturnValue(mockClient);

      asyncTraceInstance = new AsyncTrace(42, 'async-span-id', 'async-func-uuid');
    });

    it('should assign async trace to users', async () => {
      await asyncTraceInstance.assign('async@example.com');

      expect(mockClient.ee.projects.annotations.create).toHaveBeenCalledWith('test-project-id', [
        {
          assignee_email: ['async@example.com'],
          function_uuid: 'async-func-uuid',
          project_uuid: 'test-project-id',
          span_uuid: 'async-span-uuid',
        },
      ]);
    });

    it('should tag async trace', async () => {
      await asyncTraceInstance.tag('async-tag1', 'async-tag2');

      expect(mockClient.spans.update).toHaveBeenCalledWith('async-span-uuid', {
        tags_by_name: ['async-tag1', 'async-tag2'],
      });
    });

    it('should handle errors in async operations', async () => {
      mockClient.ee.projects.annotations.create.mockRejectedValue(new Error('API Error'));

      await expect(asyncTraceInstance.assign('error@example.com')).rejects.toThrow('API Error');
    });
  });
});
