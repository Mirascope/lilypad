import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock modules before imports
vi.mock('@opentelemetry/api', () => ({
  trace: {
    getTracer: vi.fn(),
    setSpan: vi.fn(),
    getSpan: vi.fn(),
  },
  context: {
    active: vi.fn(),
    with: vi.fn(),
  },
  SpanKind: {
    CLIENT: 2,
  },
  SpanStatusCode: {
    OK: 1,
    ERROR: 2,
  },
}));

vi.mock('shimmer', () => ({
  default: {
    wrap: vi.fn(),
    unwrap: vi.fn(),
  },
}));

vi.mock('@opentelemetry/instrumentation', () => ({
  InstrumentationBase: class {
    constructor(_name: string, _version: string, _config?: any) {}
    tracer = { startSpan: vi.fn() };
  },
  InstrumentationNodeModuleDefinition: vi.fn(),
  isWrapped: vi.fn(),
}));

vi.mock('../utils/logger', () => ({
  logger: {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock('../utils/stream-wrapper', () => ({
  StreamWrapper: vi.fn(),
  isAsyncIterable: vi.fn(),
}));

vi.mock('../shutdown', () => ({
  isSDKShuttingDown: vi.fn(),
}));

// Import after mocking
import { BedrockInstrumentation } from './bedrock-otel-instrumentation';
import { trace, context, SpanKind, SpanStatusCode } from '@opentelemetry/api';
import shimmer from 'shimmer';
import { InstrumentationNodeModuleDefinition, isWrapped } from '@opentelemetry/instrumentation';
import { logger } from '../utils/logger';
import { StreamWrapper } from '../utils/stream-wrapper';
import { isSDKShuttingDown } from '../shutdown';

// Get mocked functions
const mockedTrace = vi.mocked(trace);
const mockedContext = vi.mocked(context);
const mockedShimmer = vi.mocked(shimmer);
const mockedLogger = vi.mocked(logger);
const mockedIsWrapped = vi.mocked(isWrapped);
const mockedIsSDKShuttingDown = vi.mocked(isSDKShuttingDown);
const mockedStreamWrapper = vi.mocked(StreamWrapper);

describe('BedrockInstrumentation', () => {
  let mockSpan: any;
  let mockTracer: any;
  let mockOriginalSend: any;
  let BedrockRuntimeClient: any;
  let instrumentation: BedrockInstrumentation;
  let mockCommand: any;

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock span
    mockSpan = {
      setAttribute: vi.fn(),
      setAttributes: vi.fn(),
      addEvent: vi.fn(),
      setStatus: vi.fn(),
      recordException: vi.fn(),
      end: vi.fn(),
      spanContext: vi.fn().mockReturnValue({
        spanId: 'span-123',
        traceId: 'trace-456',
      }),
    };

    // Mock tracer
    mockTracer = {
      startSpan: vi.fn().mockReturnValue(mockSpan),
    };

    // Set up mock implementations
    mockedTrace.getTracer.mockReturnValue(mockTracer);
    mockedTrace.setSpan.mockImplementation((ctx, span) => ({ ...ctx, span }));
    mockedTrace.getSpan.mockReturnValue(null);
    mockedContext.active.mockReturnValue({});
    mockedContext.with.mockImplementation((ctx, fn) => fn());
    mockedIsSDKShuttingDown.mockReturnValue(false);

    // Mock original send method
    mockOriginalSend = vi.fn();

    // Create base BedrockRuntimeClient class
    BedrockRuntimeClient = class {
      config = { region: 'us-east-1' };
      send = mockOriginalSend;
    };

    // Create instrumentation instance
    instrumentation = new BedrockInstrumentation({
      requestHook: vi.fn(),
      responseHook: vi.fn(),
    });

    // Mock the tracer
    (instrumentation as any).tracer = mockTracer;
  });

  describe('init', () => {
    it('should create instrumentation module definition', () => {
      const modules = (instrumentation as any).init();

      expect(modules).toHaveLength(1);
      expect(InstrumentationNodeModuleDefinition).toHaveBeenCalledWith(
        '@aws-sdk/client-bedrock-runtime',
        ['>=3.0.0'],
        expect.any(Function),
        expect.any(Function),
      );
    });

    it('should log initialization', () => {
      (instrumentation as any).init();

      expect(mockedLogger.info).toHaveBeenCalledWith(
        '[BedrockInstrumentation] Initializing Bedrock instrumentation',
      );
    });
  });

  describe('_applyPatch', () => {
    it('should patch BedrockRuntimeClient prototype', () => {
      const moduleExports = { BedrockRuntimeClient };

      mockedIsWrapped.mockReturnValue(false);
      mockedShimmer.wrap.mockImplementation((obj, method, wrapper) => {
        obj[method] = wrapper(obj[method]);
      });

      (instrumentation as any)._applyPatch(moduleExports);

      expect(mockedShimmer.wrap).toHaveBeenCalledWith(
        BedrockRuntimeClient.prototype,
        'send',
        expect.any(Function),
      );
    });

    it('should skip if already instrumented', () => {
      const moduleExports = {
        BedrockRuntimeClient,
        [Symbol.for('lilypad.bedrock.instrumented')]: true,
      };

      const result = (instrumentation as any)._applyPatch(moduleExports);

      expect(mockedLogger.warn).toHaveBeenCalledWith(
        '[BedrockInstrumentation] Module already instrumented by Lilypad, skipping',
      );
      expect(mockedShimmer.wrap).not.toHaveBeenCalled();
      expect(result).toBe(moduleExports);
    });

    it('should handle missing BedrockRuntimeClient', () => {
      const moduleExports = {};

      const result = (instrumentation as any)._applyPatch(moduleExports);

      expect(mockedLogger.error).toHaveBeenCalledWith(
        '[BedrockInstrumentation] BedrockRuntimeClient not found in module exports',
      );
      expect(result).toBe(moduleExports);
    });
  });

  describe('send wrapping', () => {
    let wrappedSend: any;
    let mockConfig: any;

    beforeEach(() => {
      // Set up wrapped send method
      mockedShimmer.wrap.mockImplementation((obj, method, wrapper) => {
        wrappedSend = wrapper(mockOriginalSend);
      });

      mockConfig = {
        requestHook: vi.fn(),
        responseHook: vi.fn(),
      };

      (instrumentation as any)._config = mockConfig;
    });

    it('should create a span for InvokeModelCommand', async () => {
      mockCommand = {
        constructor: { name: 'InvokeModelCommand' },
        input: {
          modelId: 'anthropic.claude-3-haiku-20240307',
          body: JSON.stringify({
            anthropic_version: 'bedrock-2023-05-31',
            max_tokens: 100,
            temperature: 0.7,
            messages: [{ role: 'user', content: 'Hello' }],
          }),
        },
      };

      const mockResponse = {
        body: new TextEncoder().encode(
          JSON.stringify({
            content: [{ type: 'text', text: 'Hello response' }],
            stop_reason: 'end_turn',
            usage: { input_tokens: 10, output_tokens: 5 },
          }),
        ),
      };

      mockOriginalSend.mockResolvedValue(mockResponse);

      // Apply patch to get wrapped method
      (instrumentation as any)._applyPatch({ BedrockRuntimeClient });

      const client = new BedrockRuntimeClient();
      await wrappedSend.call(client, mockCommand);

      expect(mockTracer.startSpan).toHaveBeenCalledWith(
        'bedrock.invoke anthropic.claude-3-haiku-20240307',
        {
          kind: SpanKind.CLIENT,
          attributes: {
            'gen_ai.system': 'bedrock',
            'gen_ai.request.model': 'anthropic.claude-3-haiku-20240307',
            'gen_ai.request.temperature': 0.7,
            'gen_ai.request.max_tokens': 100,
            'gen_ai.request.top_p': undefined,
            'gen_ai.operation.name': 'chat',
            'bedrock.provider': 'anthropic',
            'bedrock.region': 'us-east-1',
            'lilypad.type': 'trace',
          },
        },
        {},
      );
    });

    it('should pass through non-model commands', async () => {
      mockCommand = { input: {} }; // No modelId
      const mockResponse = { data: 'test' };

      mockOriginalSend.mockResolvedValue(mockResponse);

      (instrumentation as any)._applyPatch({ BedrockRuntimeClient });

      const client = new BedrockRuntimeClient();
      const result = await wrappedSend.call(client, mockCommand);

      expect(result).toBe(mockResponse);
      expect(mockTracer.startSpan).not.toHaveBeenCalled();
    });

    it('should handle errors', async () => {
      mockCommand = {
        constructor: { name: 'InvokeModelCommand' },
        input: {
          modelId: 'anthropic.claude-3-haiku-20240307',
          body: JSON.stringify({ messages: [] }),
        },
      };

      const error = new Error('Bedrock API Error');
      mockOriginalSend.mockRejectedValue(error);

      (instrumentation as any)._applyPatch({ BedrockRuntimeClient });

      const client = new BedrockRuntimeClient();
      await expect(wrappedSend.call(client, mockCommand)).rejects.toThrow('Bedrock API Error');

      expect(mockSpan.recordException).toHaveBeenCalledWith(error);
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'Bedrock API Error',
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should handle streaming responses', async () => {
      mockCommand = {
        constructor: { name: 'InvokeModelWithResponseStreamCommand' },
        input: {
          modelId: 'anthropic.claude-3-haiku-20240307',
          body: JSON.stringify({ messages: [], stream: true }),
        },
      };

      // Create a mock async iterable
      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield {
            chunk: {
              bytes: new TextEncoder().encode(
                JSON.stringify({
                  type: 'content_block_delta',
                  delta: { text: 'Hello' },
                }),
              ),
            },
          };
          yield {
            chunk: {
              bytes: new TextEncoder().encode(
                JSON.stringify({
                  type: 'message_stop',
                  stop_reason: 'end_turn',
                }),
              ),
            },
          };
        },
      };

      const mockResponse = { body: mockStream };
      mockOriginalSend.mockResolvedValue(mockResponse);

      // Mock StreamWrapper to return the stream
      mockedStreamWrapper.mockImplementation((stream, _span, _options) => stream);

      (instrumentation as any)._applyPatch({ BedrockRuntimeClient });

      const client = new BedrockRuntimeClient();
      const result = await wrappedSend.call(client, mockCommand);

      expect(result.body).toBeDefined();
      expect(mockedStreamWrapper).toHaveBeenCalledWith(mockStream, mockSpan, expect.any(Object));
    });

    it('should detect different model providers', async () => {
      const providers = [
        { modelId: 'amazon.titan-text-express-v1', expected: 'amazon' },
        { modelId: 'meta.llama2-70b-chat-v1', expected: 'meta' },
        { modelId: 'cohere.command-text-v14', expected: 'cohere' },
        { modelId: 'ai21.j2-ultra-v1', expected: 'ai21' },
        { modelId: 'mistral.mistral-7b-instruct-v0:2', expected: 'mistral' },
        { modelId: 'unknown.model', expected: 'unknown' },
      ];

      (instrumentation as any)._applyPatch({ BedrockRuntimeClient });
      const client = new BedrockRuntimeClient();

      for (const { modelId, expected } of providers) {
        mockTracer.startSpan.mockClear();

        mockCommand = {
          constructor: { name: 'InvokeModelCommand' },
          input: {
            modelId,
            body: JSON.stringify({}),
          },
        };

        mockOriginalSend.mockResolvedValue({
          body: new TextEncoder().encode(JSON.stringify({})),
        });

        await wrappedSend.call(client, mockCommand);

        expect(mockTracer.startSpan).toHaveBeenCalledWith(
          `bedrock.invoke ${modelId}`,
          expect.objectContaining({
            attributes: expect.objectContaining({
              'bedrock.provider': expected,
            }),
          }),
          expect.any(Object),
        );
      }
    });

    it('should record messages for different providers', async () => {
      const testCases = [
        {
          provider: 'anthropic',
          modelId: 'anthropic.claude-3-haiku-20240307',
          body: {
            messages: [
              { role: 'user', content: 'Hello' },
              { role: 'assistant', content: 'Hi there' },
            ],
          },
          expectedEvents: 2,
        },
        {
          provider: 'amazon',
          modelId: 'amazon.titan-text-express-v1',
          body: {
            inputText: 'Hello Titan',
          },
          expectedEvents: 1,
        },
        {
          provider: 'meta',
          modelId: 'meta.llama2-70b-chat-v1',
          body: {
            prompt: 'Hello Llama',
          },
          expectedEvents: 1,
        },
      ];

      (instrumentation as any)._applyPatch({ BedrockRuntimeClient });
      const client = new BedrockRuntimeClient();

      for (const testCase of testCases) {
        mockSpan.addEvent.mockClear();

        mockCommand = {
          constructor: { name: 'InvokeModelCommand' },
          input: {
            modelId: testCase.modelId,
            body: JSON.stringify(testCase.body),
          },
        };

        mockOriginalSend.mockResolvedValue({
          body: new TextEncoder().encode(JSON.stringify({})),
        });

        await wrappedSend.call(client, mockCommand);

        // Check that the correct number of message events were recorded
        const messageEvents = mockSpan.addEvent.mock.calls.filter((call) =>
          call[0].includes('message'),
        );
        expect(messageEvents).toHaveLength(testCase.expectedEvents);
      }
    });
  });

  describe('_removePatch', () => {
    it('should unwrap send method', () => {
      const moduleExports = {
        BedrockRuntimeClient,
        [Symbol.for('lilypad.bedrock.instrumented')]: true,
      };

      mockedIsWrapped.mockReturnValue(true);

      (instrumentation as any)._removePatch(moduleExports);

      expect(mockedShimmer.unwrap).toHaveBeenCalledWith(BedrockRuntimeClient.prototype, 'send');
      expect(moduleExports[Symbol.for('lilypad.bedrock.instrumented')]).toBeUndefined();
    });
  });

  describe('SDK shutdown handling', () => {
    it('should skip instrumentation when SDK is shutting down', async () => {
      mockedIsSDKShuttingDown.mockReturnValue(true);

      mockCommand = {
        input: {
          modelId: 'anthropic.claude-3-haiku-20240307',
          body: JSON.stringify({}),
        },
      };

      let wrappedSend: any;
      mockedShimmer.wrap.mockImplementation((obj, method, wrapper) => {
        // Store the wrapped function
        wrappedSend = wrapper(mockOriginalSend);
        // Actually replace the method on the prototype
        obj[method] = wrappedSend;
      });

      (instrumentation as any)._applyPatch({ BedrockRuntimeClient });

      const client = new BedrockRuntimeClient();

      // Call the wrapped method directly from the client
      await client.send(mockCommand);

      expect(mockOriginalSend).toHaveBeenCalledWith(mockCommand);
      expect(mockTracer.startSpan).not.toHaveBeenCalled();
    });
  });
});
