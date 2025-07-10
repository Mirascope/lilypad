import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import * as otel from '@opentelemetry/api';
import { trace, getCurrentSpan, logToCurrentSpan, Trace, AsyncTrace } from './trace';
import { getSettings } from './utils/settings';
import { getCachedClosure } from './utils/closure';

// Mock dependencies
vi.mock('./utils/settings');
vi.mock('./utils/closure');
vi.mock('../lilypad/generated/Client', () => ({
  LilypadClient: vi.fn().mockImplementation(() => ({
    projects: {
      functions: {
        getByHash: vi.fn(),
        create: vi.fn(),
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

  describe('trace decorator', () => {
    it('should error when descriptor is undefined', () => {
      expect(() => {
        trace()(undefined as any, 'method', undefined);
      }).toThrow('trace decorator descriptor is undefined');
    });

    it('should error when applied to non-function', () => {
      const descriptor = { value: 'not-a-function' };
      expect(() => {
        trace()(undefined as any, 'method', descriptor);
      }).toThrow('trace decorator can only be applied to methods');
    });

    it('should wrap a synchronous method and create span', async () => {
      class TestClass {
        testMethod(arg1: string, arg2: number) {
          return `${arg1}-${arg2}`;
        }
      }

      const descriptor = Object.getOwnPropertyDescriptor(TestClass.prototype, 'testMethod')!;
      const tracedDescriptor = trace()(TestClass.prototype, 'testMethod', descriptor);
      TestClass.prototype.testMethod = tracedDescriptor.value;

      const instance = new TestClass();
      const result = await instance.testMethod('test', 123);

      expect(result).toBe('test-123');
      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        'TestClass.testMethod',
        expect.objectContaining({
          kind: otel.SpanKind.INTERNAL,
          attributes: expect.objectContaining({
            'lilypad.type': 'trace',
            'lilypad.project_uuid': 'test-project-id',
            'code.function': 'testMethod',
            'code.namespace': 'TestClass',
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

    it('should handle async methods', async () => {
      class TestClass {
        async testMethod(value: string) {
          await new Promise((resolve) => setTimeout(resolve, 10));
          return value.toUpperCase();
        }
      }

      const descriptor = Object.getOwnPropertyDescriptor(TestClass.prototype, 'testMethod')!;
      const tracedDescriptor = trace({ name: 'custom-name' })(
        TestClass.prototype,
        'testMethod',
        descriptor,
      );
      TestClass.prototype.testMethod = tracedDescriptor.value;

      const instance = new TestClass();
      const result = await instance.testMethod('hello');

      expect(result).toBe('HELLO');
      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        'custom-name',
        expect.any(Object),
        expect.any(Function),
      );
    });

    it('should handle errors and record exception', async () => {
      const testError = new Error('Test error');

      class TestClass {
        async failingMethod() {
          throw testError;
        }
      }

      const descriptor = Object.getOwnPropertyDescriptor(TestClass.prototype, 'failingMethod')!;
      const tracedDescriptor = trace()(TestClass.prototype, 'failingMethod', descriptor);
      TestClass.prototype.failingMethod = tracedDescriptor.value;

      const instance = new TestClass();

      await expect(instance.failingMethod()).rejects.toThrow('Test error');
      expect(mockSpan.recordException).toHaveBeenCalledWith(testError);
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: otel.SpanStatusCode.ERROR,
        message: 'Test error',
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should handle custom options', async () => {
      class TestClass {
        methodWithOptions() {
          return 'result';
        }
      }

      const descriptor = Object.getOwnPropertyDescriptor(TestClass.prototype, 'methodWithOptions')!;
      const tracedDescriptor = trace({
        name: 'custom-trace',
        tags: ['tag1', 'tag2'],
        attributes: { custom: 'attribute' },
      })(TestClass.prototype, 'methodWithOptions', descriptor);
      TestClass.prototype.methodWithOptions = tracedDescriptor.value;

      const instance = new TestClass();
      await instance.methodWithOptions();

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

      class TestClass {
        testMethod() {
          return 'no-trace';
        }
      }

      const descriptor = Object.getOwnPropertyDescriptor(TestClass.prototype, 'testMethod')!;
      const tracedDescriptor = trace()(TestClass.prototype, 'testMethod', descriptor);
      TestClass.prototype.testMethod = tracedDescriptor.value;

      const instance = new TestClass();
      const result = await instance.testMethod();

      expect(result).toBe('no-trace');
      expect(mockTracer.startActiveSpan).not.toHaveBeenCalled();
    });

    it('should return Trace wrapper in wrap mode', async () => {
      class TestClass {
        wrappedMethod() {
          return 'wrapped-result';
        }
      }

      const descriptor = Object.getOwnPropertyDescriptor(TestClass.prototype, 'wrappedMethod')!;
      const tracedDescriptor = trace({ mode: 'wrap' })(
        TestClass.prototype,
        'wrappedMethod',
        descriptor,
      );
      TestClass.prototype.wrappedMethod = tracedDescriptor.value;

      const instance = new TestClass();
      const result = await instance.wrappedMethod();

      expect(result).toBeInstanceOf(Trace);
      expect((result as any).response).toBe('wrapped-result');
    });

    it('should return AsyncTrace wrapper for async methods in wrap mode', async () => {
      class TestClass {
        async wrappedMethod() {
          return 'async-wrapped-result';
        }
      }

      const descriptor = Object.getOwnPropertyDescriptor(TestClass.prototype, 'wrappedMethod')!;
      const tracedDescriptor = trace({ mode: 'wrap' })(
        TestClass.prototype,
        'wrappedMethod',
        descriptor,
      );
      TestClass.prototype.wrappedMethod = tracedDescriptor.value;

      const instance = new TestClass();
      const result = await instance.wrappedMethod();

      expect(result).toBeInstanceOf(AsyncTrace);
      expect((result as any).response).toBe('async-wrapped-result');
    });

    it('should handle string options as name', async () => {
      class TestClass {
        namedMethod() {
          return 'result';
        }
      }

      const descriptor = Object.getOwnPropertyDescriptor(TestClass.prototype, 'namedMethod')!;
      const tracedDescriptor = trace('string-name')(TestClass.prototype, 'namedMethod', descriptor);
      TestClass.prototype.namedMethod = tracedDescriptor.value;

      const instance = new TestClass();
      await instance.namedMethod();

      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        'string-name',
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
      expect(() => {
        traceWrapper.annotate();
      }).toThrow('At least one annotation must be provided');
    });

    it('should throw error when no emails provided to assign', () => {
      expect(() => {
        traceWrapper.assign();
      }).toThrow('At least one email address must be provided');
    });

    it('should throw error when SDK not configured', () => {
      vi.mocked(getSettings).mockReturnValue(null);

      expect(() => {
        traceWrapper.annotate({ label: 'test' } as any);
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
      await expect(asyncTraceWrapper.annotate()).rejects.toThrow(
        'At least one annotation must be provided',
      );
    });

    it('should throw error when SDK not configured', async () => {
      vi.mocked(getSettings).mockReturnValue(null);

      await expect(asyncTraceWrapper.annotate({ label: 'test' } as any)).rejects.toThrow(
        'Lilypad SDK not configured',
      );
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

      await expect(asyncTraceWrapper.annotate({ label: 'test' } as any)).rejects.toThrow(
        'Cannot annotate: span not found',
      );
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

      class TestClass {
        cachedMethod() {
          return 'cached';
        }
      }

      const descriptor = Object.getOwnPropertyDescriptor(TestClass.prototype, 'cachedMethod')!;
      const tracedDescriptor = trace()(TestClass.prototype, 'cachedMethod', descriptor);
      TestClass.prototype.cachedMethod = tracedDescriptor.value;

      const instance = new TestClass();

      // Call twice
      await instance.cachedMethod();
      await instance.cachedMethod();

      // Should only call getByHash once due to caching
      expect(mockClient.projects.functions.getByHash).toHaveBeenCalledTimes(1);
    });
  });
});
