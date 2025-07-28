import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock modules before imports
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
    CLIENT: 2,
  },
  SpanStatusCode: {
    OK: 1,
    ERROR: 2,
  },
}));

vi.mock('./utils/logger', () => ({
  logger: {
    debug: vi.fn(),
  },
}));

vi.mock('./utils/error-handler', () => ({
  ensureError: vi.fn(),
}));

// Import after mocking
import { wrapBedrock } from './wrap-bedrock';
import { trace, context, SpanKind, SpanStatusCode } from '@opentelemetry/api';
import { logger } from './utils/logger';
import { ensureError } from './utils/error-handler';
import type {
  BedrockInvokeModelParams,
  BedrockInvokeModelResponse,
  BedrockResponseStreamChunk,
} from './types/bedrock';

// Get mocked functions
const mockedTrace = vi.mocked(trace);
const mockedContext = vi.mocked(context);
const mockedLogger = vi.mocked(logger);
const mockedEnsureError = vi.mocked(ensureError);

describe('wrapBedrock', () => {
  let mockSpan: any;
  let mockTracer: any;
  let mockInvokeModel: any;
  let mockInvokeModelStream: any;
  let BedrockClass: any;

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
    };

    // Mock tracer
    mockTracer = {
      startSpan: vi.fn().mockReturnValue(mockSpan),
    };

    // Set up mock implementations
    mockedTrace.getTracer.mockReturnValue(mockTracer);
    mockedTrace.setSpan.mockImplementation((ctx, span) => ({ ...ctx, span }));
    mockedContext.active.mockReturnValue({});
    mockedContext.with.mockImplementation((ctx, fn) => fn());
    mockedEnsureError.mockImplementation((error) => {
      if (error instanceof Error) return error;
      return new Error(String(error));
    });

    // Mock original methods
    mockInvokeModel = vi.fn();
    mockInvokeModelStream = vi.fn();

    // Create base Bedrock class
    BedrockClass = class {
      config = {
        region: 'us-east-1',
      };
      invokeModel = mockInvokeModel;
      invokeModelWithResponseStream = mockInvokeModelStream;
    };
  });

  describe('class wrapping', () => {
    it('should create a wrapped class that extends the original', () => {
      const WrappedBedrock = wrapBedrock(BedrockClass);
      const instance = new WrappedBedrock();

      expect(instance).toBeInstanceOf(BedrockClass);
      expect(instance.invokeModel).toBeDefined();
      expect(instance.invokeModel).not.toBe(mockInvokeModel);
      expect(instance.invokeModelWithResponseStream).toBeDefined();
      expect(instance.invokeModelWithResponseStream).not.toBe(mockInvokeModelStream);
    });

    it('should log debug message when wrapping', () => {
      wrapBedrock(BedrockClass);

      expect(mockedLogger.debug).toHaveBeenCalledWith(
        '[wrapBedrock] Wrapping Bedrock Runtime instance',
      );
    });

    it('should handle missing methods gracefully', () => {
      const EmptyClass = class {};
      const WrappedClass = wrapBedrock(EmptyClass);
      const instance = new WrappedClass();

      expect(instance).toBeInstanceOf(EmptyClass);
    });
  });

  describe('invokeModel wrapping - Anthropic', () => {
    it('should create a span with correct attributes for Anthropic Claude', async () => {
      const WrappedBedrock = wrapBedrock(BedrockClass);
      const instance = new WrappedBedrock();

      const anthropicRequest = {
        anthropic_version: 'bedrock-2023-05-31',
        max_tokens: 1000,
        messages: [{ role: 'user', content: 'Hello Claude!' }],
        temperature: 0.7,
        top_p: 0.9,
        top_k: 20,
      };

      const params: BedrockInvokeModelParams = {
        modelId: 'anthropic.claude-3-opus-20240229',
        contentType: 'application/json',
        body: JSON.stringify(anthropicRequest),
      };

      const response: BedrockInvokeModelResponse = {
        body: new TextEncoder().encode(
          JSON.stringify({
            id: 'msg_123',
            type: 'message',
            role: 'assistant',
            content: [{ type: 'text', text: 'Hello! How can I help you?' }],
            stop_reason: 'end_turn',
            usage: { input_tokens: 10, output_tokens: 20 },
          }),
        ),
      };

      mockInvokeModel.mockResolvedValue(response);

      await instance.invokeModel(params);

      expect(mockTracer.startSpan).toHaveBeenCalledWith('chat anthropic.claude-3-opus-20240229', {
        kind: SpanKind.CLIENT,
        attributes: {
          'gen_ai.system': 'bedrock',
          'server.address': 'bedrock-runtime.us-east-1.amazonaws.com',
          'gen_ai.request.model': 'anthropic.claude-3-opus-20240229',
          'gen_ai.operation.name': 'chat',
          'aws.region': 'us-east-1',
          'gen_ai.bedrock.provider': 'anthropic',
        },
      });

      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.request.max_tokens': 1000,
        'gen_ai.request.temperature': 0.7,
        'gen_ai.request.top_p': 0.9,
        'gen_ai.request.top_k': 20,
      });

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.user.message', {
        'gen_ai.system': 'bedrock_anthropic',
        content: 'Hello Claude!',
      });
    });

    it('should record Anthropic response data', async () => {
      const WrappedBedrock = wrapBedrock(BedrockClass);
      const instance = new WrappedBedrock();

      const params: BedrockInvokeModelParams = {
        modelId: 'anthropic.claude-3-opus-20240229',
        body: JSON.stringify({ messages: [] }),
      };

      const response: BedrockInvokeModelResponse = {
        body: new TextEncoder().encode(
          JSON.stringify({
            id: 'msg_123',
            type: 'message',
            role: 'assistant',
            model: 'claude-3-opus-20240229',
            content: [{ type: 'text', text: 'Hello! How can I help you?' }],
            stop_reason: 'end_turn',
            usage: { input_tokens: 10, output_tokens: 20 },
          }),
        ),
      };

      mockInvokeModel.mockResolvedValue(response);

      await instance.invokeModel(params);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'bedrock_anthropic',
        index: 0,
        finish_reason: 'end_turn',
        message: JSON.stringify({
          role: 'assistant',
          content: 'Hello! How can I help you?',
        }),
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.finish_reasons', [
        'end_turn',
      ]);

      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.usage.input_tokens': 10,
        'gen_ai.usage.output_tokens': 20,
        'gen_ai.usage.total_tokens': 30,
      });
    });

    it('should handle Anthropic system messages', async () => {
      const WrappedBedrock = wrapBedrock(BedrockClass);
      const instance = new WrappedBedrock();

      const params: BedrockInvokeModelParams = {
        modelId: 'anthropic.claude-3-opus-20240229',
        body: JSON.stringify({
          system: 'You are a helpful assistant',
          messages: [{ role: 'user', content: 'Hi' }],
        }),
      };

      mockInvokeModel.mockResolvedValue({ body: new Uint8Array() });

      await instance.invokeModel(params);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.system.message', {
        'gen_ai.system': 'bedrock_anthropic',
        content: 'You are a helpful assistant',
      });
    });
  });

  describe('invokeModel wrapping - Amazon Titan', () => {
    it('should create a span with correct attributes for Titan', async () => {
      const WrappedBedrock = wrapBedrock(BedrockClass);
      const instance = new WrappedBedrock();

      const titanRequest = {
        inputText: 'Hello Titan!',
        textGenerationConfig: {
          temperature: 0.7,
          topP: 0.9,
          maxTokenCount: 512,
        },
      };

      const params: BedrockInvokeModelParams = {
        modelId: 'amazon.titan-text-express-v1',
        body: JSON.stringify(titanRequest),
      };

      const response: BedrockInvokeModelResponse = {
        body: new TextEncoder().encode(
          JSON.stringify({
            inputTextTokenCount: 5,
            results: [
              {
                tokenCount: 10,
                outputText: 'Hello! I am Titan.',
                completionReason: 'FINISH',
              },
            ],
          }),
        ),
      };

      mockInvokeModel.mockResolvedValue(response);

      await instance.invokeModel(params);

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.bedrock.provider', 'amazon');

      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.request.temperature': 0.7,
        'gen_ai.request.top_p': 0.9,
        'gen_ai.request.max_tokens': 512,
      });

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.user.message', {
        'gen_ai.system': 'bedrock_titan',
        content: 'Hello Titan!',
      });
    });

    it('should record Titan response data', async () => {
      const WrappedBedrock = wrapBedrock(BedrockClass);
      const instance = new WrappedBedrock();

      const params: BedrockInvokeModelParams = {
        modelId: 'amazon.titan-text-express-v1',
        body: JSON.stringify({ inputText: 'test' }),
      };

      const response: BedrockInvokeModelResponse = {
        body: new TextEncoder().encode(
          JSON.stringify({
            inputTextTokenCount: 5,
            results: [
              {
                tokenCount: 10,
                outputText: 'Test response',
                completionReason: 'FINISH',
              },
            ],
          }),
        ),
      };

      mockInvokeModel.mockResolvedValue(response);

      await instance.invokeModel(params);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'bedrock_titan',
        index: 0,
        finish_reason: 'FINISH',
        message: JSON.stringify({
          role: 'assistant',
          content: 'Test response',
        }),
      });

      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.usage.input_tokens': 5,
        'gen_ai.usage.output_tokens': 10,
        'gen_ai.usage.total_tokens': 15,
      });
    });
  });

  describe('invokeModel wrapping - Meta Llama', () => {
    it('should create a span with correct attributes for Llama', async () => {
      const WrappedBedrock = wrapBedrock(BedrockClass);
      const instance = new WrappedBedrock();

      const llamaRequest = {
        prompt: 'Hello Llama!',
        max_gen_len: 256,
        temperature: 0.7,
        top_p: 0.9,
      };

      const params: BedrockInvokeModelParams = {
        modelId: 'meta.llama2-70b-chat-v1',
        body: JSON.stringify(llamaRequest),
      };

      const response: BedrockInvokeModelResponse = {
        body: new TextEncoder().encode(
          JSON.stringify({
            generation: 'Hello! I am Llama.',
            prompt_token_count: 5,
            generation_token_count: 10,
            stop_reason: 'stop',
          }),
        ),
      };

      mockInvokeModel.mockResolvedValue(response);

      await instance.invokeModel(params);

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.bedrock.provider', 'meta');

      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.request.max_tokens': 256,
        'gen_ai.request.temperature': 0.7,
        'gen_ai.request.top_p': 0.9,
      });

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.user.message', {
        'gen_ai.system': 'bedrock_llama',
        content: 'Hello Llama!',
      });
    });
  });

  describe('invokeModelWithResponseStream wrapping', () => {
    it('should handle Anthropic streaming', async () => {
      const WrappedBedrock = wrapBedrock(BedrockClass);
      const instance = new WrappedBedrock();

      const params: BedrockInvokeModelParams = {
        modelId: 'anthropic.claude-3-opus-20240229',
        body: JSON.stringify({ messages: [], stream: true }),
      };

      // Create mock stream
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
                  type: 'content_block_delta',
                  delta: { text: ' world!' },
                }),
              ),
            },
          };
          yield {
            chunk: {
              bytes: new TextEncoder().encode(
                JSON.stringify({
                  type: 'message_delta',
                  delta: { stop_reason: 'end_turn' },
                }),
              ),
            },
          };
          yield {
            chunk: {
              bytes: new TextEncoder().encode(
                JSON.stringify({
                  type: 'message_stop',
                  usage: { input_tokens: 5, output_tokens: 10 },
                }),
              ),
            },
          };
        },
      };

      mockInvokeModelStream.mockResolvedValue(mockStream);

      const result = await instance.invokeModelWithResponseStream(params);

      // Consume the stream
      const chunks: BedrockResponseStreamChunk[] = [];
      for await (const chunk of result) {
        chunks.push(chunk);
      }

      expect(chunks).toHaveLength(4);
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'bedrock_anthropic',
        index: 0,
        finish_reason: 'end_turn',
        message: JSON.stringify({ role: 'assistant', content: 'Hello world!' }),
      });
    });

    it('should handle streaming errors', async () => {
      const WrappedBedrock = wrapBedrock(BedrockClass);
      const instance = new WrappedBedrock();

      const params: BedrockInvokeModelParams = {
        modelId: 'anthropic.claude-3-opus-20240229',
        body: JSON.stringify({ messages: [] }),
      };

      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield {
            throttlingException: {
              message: 'Request throttled',
            },
          };
        },
      };

      mockInvokeModelStream.mockResolvedValue(mockStream);

      const result = await instance.invokeModelWithResponseStream(params);

      await expect(async () => {
        for await (const _chunk of result) {
          // Process chunk
        }
      }).rejects.toThrow('Bedrock ThrottlingException');

      expect(mockSpan.recordException).toHaveBeenCalled();
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'Bedrock ThrottlingException',
      });
    });

    it('should handle different stream error types', async () => {
      const WrappedBedrock = wrapBedrock(BedrockClass);
      const instance = new WrappedBedrock();

      const errorTypes = [
        { internalServerException: {} },
        { modelStreamErrorException: {} },
        { validationException: {} },
      ];

      for (const errorType of errorTypes) {
        const mockStream = {
          async *[Symbol.asyncIterator]() {
            yield errorType;
          },
        };

        mockInvokeModelStream.mockResolvedValue(mockStream);

        const result = await instance.invokeModelWithResponseStream({
          modelId: 'test-model',
          body: '{}',
        });

        await expect(async () => {
          for await (const _chunk of result) {
            // Process chunk
          }
        }).rejects.toThrow(/Bedrock.*Exception/);
      }
    });
  });

  describe('error handling', () => {
    it('should handle errors in invokeModel', async () => {
      const WrappedBedrock = wrapBedrock(BedrockClass);
      const instance = new WrappedBedrock();

      const error = new Error('Bedrock API Error');
      mockInvokeModel.mockRejectedValue(error);

      await expect(
        instance.invokeModel({
          modelId: 'test-model',
          body: '{}',
        }),
      ).rejects.toThrow('Bedrock API Error');

      expect(mockSpan.recordException).toHaveBeenCalledWith(error);
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'Bedrock API Error',
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should handle malformed request bodies', async () => {
      const WrappedBedrock = wrapBedrock(BedrockClass);
      const instance = new WrappedBedrock();

      const params: BedrockInvokeModelParams = {
        modelId: 'test-model',
        body: 'invalid json',
      };

      mockInvokeModel.mockResolvedValue({ body: new Uint8Array() });

      await instance.invokeModel(params);

      // Should not throw, just log debug message
      expect(mockedLogger.debug).toHaveBeenCalledWith('[wrapBedrock] Failed to parse request body');
    });

    it('should handle malformed response bodies', async () => {
      const WrappedBedrock = wrapBedrock(BedrockClass);
      const instance = new WrappedBedrock();

      const params: BedrockInvokeModelParams = {
        modelId: 'test-model',
        body: '{}',
      };

      const response: BedrockInvokeModelResponse = {
        body: new TextEncoder().encode('invalid json'),
      };

      mockInvokeModel.mockResolvedValue(response);

      await instance.invokeModel(params);

      // Should not throw, just log debug message
      expect(mockedLogger.debug).toHaveBeenCalledWith(
        '[wrapBedrock] Failed to parse response body',
      );
    });
  });

  describe('instance wrapping', () => {
    it('should wrap an existing Bedrock instance', () => {
      const instance = new BedrockClass();
      const originalInvoke = instance.invokeModel;
      const originalStream = instance.invokeModelWithResponseStream;

      const wrappedInstance = wrapBedrock(instance);

      expect(wrappedInstance).toBe(instance); // Modified in-place
      expect(instance.invokeModel).not.toBe(originalInvoke);
      expect(instance.invokeModelWithResponseStream).not.toBe(originalStream);
    });

    it('should handle instance without methods', () => {
      const instance = {};
      const wrappedInstance = wrapBedrock(instance);

      expect(wrappedInstance).toBe(instance);
      // Should not throw
    });
  });

  describe('region extraction', () => {
    it('should extract region from _config', async () => {
      const instance = new BedrockClass();
      delete instance.config;
      instance._config = { region: 'eu-west-1' };

      const wrappedInstance = wrapBedrock(instance);
      mockInvokeModel.mockResolvedValue({ body: new Uint8Array() });

      await wrappedInstance.invokeModel({ modelId: 'test', body: '{}' });

      expect(mockTracer.startSpan).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          attributes: expect.objectContaining({
            'server.address': 'bedrock-runtime.eu-west-1.amazonaws.com',
            'aws.region': 'eu-west-1',
          }),
        }),
      );
    });

    it('should use unknown region when not found', async () => {
      const instance = {
        invokeModel: mockInvokeModel,
      };

      const wrappedInstance = wrapBedrock(instance);
      mockInvokeModel.mockResolvedValue({ body: new Uint8Array() });

      await wrappedInstance.invokeModel({ modelId: 'test', body: '{}' });

      expect(mockTracer.startSpan).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          attributes: expect.objectContaining({
            'server.address': 'bedrock-runtime.unknown.amazonaws.com',
            'aws.region': 'unknown',
          }),
        }),
      );
    });
  });

  describe('provider detection', () => {
    const testCases = [
      { modelId: 'anthropic.claude-3-opus-20240229', provider: 'anthropic' },
      { modelId: 'amazon.titan-text-express-v1', provider: 'amazon' },
      { modelId: 'meta.llama2-70b-chat-v1', provider: 'meta' },
      { modelId: 'cohere.command-text-v14', provider: 'cohere' },
      { modelId: 'ai21.j2-ultra-v1', provider: 'ai21' },
      { modelId: 'mistral.mistral-7b-instruct-v0:2', provider: 'mistral' },
      { modelId: 'unknown-model', provider: 'unknown' },
    ];

    testCases.forEach(({ modelId, provider }) => {
      it(`should detect ${provider} provider from model ID ${modelId}`, async () => {
        const WrappedBedrock = wrapBedrock(BedrockClass);
        const instance = new WrappedBedrock();

        mockInvokeModel.mockResolvedValue({ body: new Uint8Array() });

        await instance.invokeModel({ modelId, body: '{}' });

        expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.bedrock.provider', provider);
      });
    });
  });
});
