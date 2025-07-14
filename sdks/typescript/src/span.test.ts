import { describe, it, expect, beforeEach, vi } from 'vitest';
import type { Span as OTelSpan, Tracer, Context } from '@opentelemetry/api';

// Mock modules before imports
vi.mock('./utils/settings', () => ({
  isConfigured: vi.fn(),
  setSettings: vi.fn(),
  getSettings: vi.fn(),
}));

vi.mock('./utils/logger', () => ({
  logger: {
    warn: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    debug: vi.fn(),
    setLevel: vi.fn(),
  },
}));

vi.mock('@opentelemetry/api', () => ({
  trace: {
    getTracer: vi.fn(),
    setSpan: vi.fn(),
  },
  context: {
    active: vi.fn(),
    with: vi.fn(),
  },
  SpanKind: {
    INTERNAL: 0,
  },
  SpanStatusCode: {
    ERROR: 2,
  },
}));

// Import after mocking
import { Span, span, syncSpan } from './span';
import { session } from './session';
import { isConfigured } from './utils/settings';
import { logger } from './utils/logger';
import * as api from '@opentelemetry/api';

// Get mocked functions
const mockedIsConfigured = vi.mocked(isConfigured);
const mockedLogger = vi.mocked(logger);
const mockedApi = vi.mocked(api);

describe('Span', () => {
  let mockOTelSpan: {
    spanContext: ReturnType<typeof vi.fn>;
    setAttribute: ReturnType<typeof vi.fn>;
    addEvent: ReturnType<typeof vi.fn>;
    setStatus: ReturnType<typeof vi.fn>;
    recordException: ReturnType<typeof vi.fn>;
    end: ReturnType<typeof vi.fn>;
  };

  let mockTracer: {
    startSpan: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    vi.clearAllMocks();

    // Create fresh mocks for each test
    mockOTelSpan = {
      spanContext: vi.fn(() => ({ spanId: 'test-span-id' })),
      setAttribute: vi.fn(),
      addEvent: vi.fn(),
      setStatus: vi.fn(),
      recordException: vi.fn(),
      end: vi.fn(),
    };

    mockTracer = {
      startSpan: vi.fn<[string, api.SpanOptions?], OTelSpan>(() => mockOTelSpan as OTelSpan),
    };

    // Setup API mocks
    mockedApi.trace.getTracer = vi.fn<[string, string?], Tracer>(() => mockTracer as Tracer);
    mockedApi.trace.setSpan = vi.fn<[Context, OTelSpan], Context>((ctx) => ctx);
    mockedApi.context.active = vi.fn<[], Context>(() => ({}) as Context);
    mockedApi.context.with = vi.fn(<T>(ctx: Context, fn: () => T) => fn());

    // Default to configured state
    mockedIsConfigured.mockReturnValue(true);
  });

  describe('constructor', () => {
    it('should warn when SDK is not configured', () => {
      mockedIsConfigured.mockReturnValue(false);

      new Span('test-span');

      expect(mockedLogger.warn).toHaveBeenCalledWith(
        'Span created but Lilypad SDK not configured. Call configure() first. This span will be a no-op.',
      );
      expect(mockTracer.startSpan).not.toHaveBeenCalled();
    });

    it('should create OpenTelemetry span when configured', () => {
      new Span('test-span');

      expect(mockTracer.startSpan).toHaveBeenCalledWith(
        'test-span',
        {
          kind: api.SpanKind.INTERNAL,
        },
        expect.any(Object), // The active context
      );
      expect(mockOTelSpan.setAttribute).toHaveBeenCalledWith('lilypad.type', 'trace');
      expect(mockOTelSpan.setAttribute).toHaveBeenCalledWith(
        'lilypad.timestamp',
        expect.stringMatching(/^\d{4}-\d{2}-\d{2}T/),
      );
    });

    it('should attach session ID if available', () => {
      session('test-session-123', () => {
        new Span('test-span');

        expect(mockOTelSpan.setAttribute).toHaveBeenCalledWith(
          'lilypad.session_id',
          'test-session-123',
        );
      });
    });
  });

  describe('span_id property', () => {
    it('should return span ID when span exists', () => {
      const testSpan = new Span('test-span');
      expect(testSpan.span_id).toBe('test-span-id');
    });

    it('should return null when span does not exist', () => {
      mockedIsConfigured.mockReturnValue(false);

      const testSpan = new Span('test-span');
      expect(testSpan.span_id).toBe(null);
    });
  });

  describe('metadata', () => {
    it('should set metadata as object', () => {
      const testSpan = new Span('test-span');
      testSpan.metadata({ userId: 123, action: 'test' });

      expect(mockOTelSpan.setAttribute).toHaveBeenCalledWith('userId', 123);
      expect(mockOTelSpan.setAttribute).toHaveBeenCalledWith('action', 'test');
    });

    it('should set metadata as key-value pair', () => {
      const testSpan = new Span('test-span');
      testSpan.metadata('key', 'value');

      expect(mockOTelSpan.setAttribute).toHaveBeenCalledWith('key', 'value');
    });

    it('should handle special metadata attribute', () => {
      const testSpan = new Span('test-span');
      const metadataObj = { nested: { data: 'value' } };
      testSpan.metadata({ metadata: metadataObj });

      expect(mockOTelSpan.setAttribute).toHaveBeenCalledWith(
        'lilypad.metadata',
        JSON.stringify(metadataObj),
      );
    });

    it('should serialize complex objects', () => {
      const testSpan = new Span('test-span');
      const complexObj = { array: [1, 2, 3], nested: { key: 'value' } };
      testSpan.metadata({ complex: complexObj });

      expect(mockOTelSpan.setAttribute).toHaveBeenCalledWith('complex', JSON.stringify(complexObj));
    });

    it('should handle null values', () => {
      const testSpan = new Span('test-span');
      testSpan.metadata({ nullValue: null });

      expect(mockOTelSpan.setAttribute).toHaveBeenCalledWith('nullValue', 'null');
    });

    it('should skip undefined values', () => {
      const testSpan = new Span('test-span');
      testSpan.metadata({ undefinedValue: undefined });

      // Should skip the undefined value
      const calls = mockOTelSpan.setAttribute.mock.calls;
      const hasUndefinedCall = calls.some((call) => call[0] === 'undefinedValue');
      expect(hasUndefinedCall).toBe(false);
    });

    it('should support method chaining', () => {
      const testSpan = new Span('test-span');
      const result = testSpan.metadata({ a: 1 }).metadata({ b: 2 });

      expect(result).toBe(testSpan);
      expect(mockOTelSpan.setAttribute).toHaveBeenCalledWith('a', 1);
      expect(mockOTelSpan.setAttribute).toHaveBeenCalledWith('b', 2);
    });
  });

  describe('logging methods', () => {
    it('should add debug log event', () => {
      const testSpan = new Span('test-span');
      testSpan.debug('Debug message', { extra: 'data' });

      expect(mockOTelSpan.addEvent).toHaveBeenCalledWith('debug', {
        'debug.message': 'Debug message',
        extra: 'data',
      });
    });

    it('should add info log event', () => {
      const testSpan = new Span('test-span');
      testSpan.info('Info message');

      expect(mockOTelSpan.addEvent).toHaveBeenCalledWith('info', {
        'info.message': 'Info message',
      });
    });

    it('should add warning log event', () => {
      const testSpan = new Span('test-span');
      testSpan.warning('Warning message');

      expect(mockOTelSpan.addEvent).toHaveBeenCalledWith('warning', {
        'warning.message': 'Warning message',
      });
    });

    it('should add error log event and set span status', () => {
      const testSpan = new Span('test-span');
      testSpan.error('Error message');

      expect(mockOTelSpan.addEvent).toHaveBeenCalledWith('error', {
        'error.message': 'Error message',
      });
      expect(mockOTelSpan.setStatus).toHaveBeenCalledWith({
        code: api.SpanStatusCode.ERROR,
        message: 'Error message',
      });
    });

    it('should add critical log event and set span status', () => {
      const testSpan = new Span('test-span');
      testSpan.critical('Critical message');

      expect(mockOTelSpan.addEvent).toHaveBeenCalledWith('critical', {
        'critical.message': 'Critical message',
      });
      expect(mockOTelSpan.setStatus).toHaveBeenCalledWith({
        code: api.SpanStatusCode.ERROR,
        message: 'Critical message',
      });
    });
  });

  describe('recordException', () => {
    it('should record Error instances', () => {
      const testSpan = new Span('test-span');
      const error = new Error('Test error');
      testSpan.recordException(error);

      expect(mockOTelSpan.recordException).toHaveBeenCalledWith(error);
      expect(mockOTelSpan.setStatus).toHaveBeenCalledWith({
        code: api.SpanStatusCode.ERROR,
        message: 'Test error',
      });
    });

    it('should convert non-Error to Error', () => {
      const testSpan = new Span('test-span');
      testSpan.recordException('String error');

      expect(mockOTelSpan.recordException).toHaveBeenCalledWith(
        expect.objectContaining({
          message: 'String error',
        }),
      );
      expect(mockOTelSpan.setStatus).toHaveBeenCalledWith({
        code: api.SpanStatusCode.ERROR,
        message: 'String error',
      });
    });
  });

  describe('finish', () => {
    it('should end the span', () => {
      const testSpan = new Span('test-span');
      testSpan.finish();

      expect(mockOTelSpan.end).toHaveBeenCalled();
    });

    it('should not end span multiple times', () => {
      const testSpan = new Span('test-span');
      testSpan.finish();
      testSpan.finish();

      expect(mockOTelSpan.end).toHaveBeenCalledTimes(1);
    });
  });

  describe('Symbol.dispose', () => {
    it('should finish span when disposed', () => {
      const testSpan = new Span('test-span');
      testSpan[Symbol.dispose]();

      expect(mockOTelSpan.end).toHaveBeenCalled();
    });
  });

  describe('Symbol.asyncDispose', () => {
    it('should finish span when async disposed', async () => {
      const testSpan = new Span('test-span');
      await testSpan[Symbol.asyncDispose]();

      expect(mockOTelSpan.end).toHaveBeenCalled();
    });
  });
});

describe('syncSpan', () => {
  let mockOTelSpan: {
    spanContext: ReturnType<typeof vi.fn>;
    setAttribute: ReturnType<typeof vi.fn>;
    addEvent: ReturnType<typeof vi.fn>;
    setStatus: ReturnType<typeof vi.fn>;
    recordException: ReturnType<typeof vi.fn>;
    end: ReturnType<typeof vi.fn>;
  };
  let mockTracer: {
    startSpan: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    vi.clearAllMocks();

    mockOTelSpan = {
      spanContext: vi.fn(() => ({ spanId: 'test-span-id' })),
      setAttribute: vi.fn(),
      addEvent: vi.fn(),
      setStatus: vi.fn(),
      recordException: vi.fn(),
      end: vi.fn(),
    };

    mockTracer = {
      startSpan: vi.fn<[string, api.SpanOptions?], OTelSpan>(() => mockOTelSpan as OTelSpan),
    };

    mockedApi.trace.getTracer = vi.fn<[string, string?], Tracer>(() => mockTracer as Tracer);
    mockedApi.context.with = vi.fn(<T>(ctx: Context, fn: () => T) => fn());
    mockedIsConfigured.mockReturnValue(true);
  });

  it('should create span and run function', () => {
    const result = syncSpan('test-span', (span) => {
      span.metadata({ key: 'value' });
      return 'result';
    });

    expect(result).toBe('result');
    expect(mockOTelSpan.setAttribute).toHaveBeenCalledWith('key', 'value');
    expect(mockOTelSpan.end).toHaveBeenCalled();
  });

  it('should handle errors and record exception', () => {
    const error = new Error('Test error');

    expect(() => {
      syncSpan('test-span', () => {
        throw error;
      });
    }).toThrow(error);

    expect(mockOTelSpan.recordException).toHaveBeenCalledWith(error);
    expect(mockOTelSpan.setStatus).toHaveBeenCalledWith({
      code: api.SpanStatusCode.ERROR,
      message: 'Test error',
    });
    expect(mockOTelSpan.end).toHaveBeenCalled();
  });
});

describe('span (async)', () => {
  let mockOTelSpan: {
    spanContext: ReturnType<typeof vi.fn>;
    setAttribute: ReturnType<typeof vi.fn>;
    addEvent: ReturnType<typeof vi.fn>;
    setStatus: ReturnType<typeof vi.fn>;
    recordException: ReturnType<typeof vi.fn>;
    end: ReturnType<typeof vi.fn>;
  };
  let mockTracer: {
    startSpan: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    vi.clearAllMocks();

    mockOTelSpan = {
      spanContext: vi.fn(() => ({ spanId: 'test-span-id' })),
      setAttribute: vi.fn(),
      addEvent: vi.fn(),
      setStatus: vi.fn(),
      recordException: vi.fn(),
      end: vi.fn(),
    };

    mockTracer = {
      startSpan: vi.fn<[string, api.SpanOptions?], OTelSpan>(() => mockOTelSpan as OTelSpan),
    };

    mockedApi.trace.getTracer = vi.fn<[string, string?], Tracer>(() => mockTracer as Tracer);
    mockedApi.context.with = vi.fn(<T>(ctx: Context, fn: () => T) => fn());
    mockedIsConfigured.mockReturnValue(true);
  });

  it('should create span and run async function', async () => {
    const result = await span('test-span', async (testSpan) => {
      testSpan.metadata({ key: 'value' });
      await new Promise((resolve) => setTimeout(resolve, 10));
      return 'async-result';
    });

    expect(result).toBe('async-result');
    expect(mockOTelSpan.setAttribute).toHaveBeenCalledWith('key', 'value');
    expect(mockOTelSpan.end).toHaveBeenCalled();
  });

  it('should handle async errors and record exception', async () => {
    const error = new Error('Async error');

    await expect(
      span('test-span', async () => {
        await new Promise((resolve) => setTimeout(resolve, 10));
        throw error;
      }),
    ).rejects.toThrow(error);

    expect(mockOTelSpan.recordException).toHaveBeenCalledWith(error);
    expect(mockOTelSpan.setStatus).toHaveBeenCalledWith({
      code: api.SpanStatusCode.ERROR,
      message: 'Async error',
    });
    expect(mockOTelSpan.end).toHaveBeenCalled();
  });
});
