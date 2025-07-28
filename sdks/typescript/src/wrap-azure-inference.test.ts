import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { wrapAzureInference } from './wrap-azure-inference';
import { getTracerProvider } from './configure';
import { SpanKind, SpanStatusCode } from '@opentelemetry/api';
import { BasicTracerProvider, InMemorySpanExporter } from '@opentelemetry/sdk-trace-base';
import { isConfigured } from './utils/settings';

// Mock the SDK state
vi.mock('./utils/settings', () => ({
  isConfigured: vi.fn(() => false),
  setSettings: vi.fn(),
  getSettings: vi.fn(),
}));

// Mock getTracerProvider
vi.mock('./configure', async () => {
  const actual = await vi.importActual('./configure');
  return {
    ...actual,
    getTracerProvider: vi.fn(),
  };
});

// Mock logger to suppress output during tests
vi.mock('./utils/logger', () => ({
  logger: {
    info: vi.fn(),
    debug: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    setLevel: vi.fn(),
  },
}));

describe('wrapAzureInference', () => {
  let provider: BasicTracerProvider;
  let exporter: InMemorySpanExporter;

  beforeEach(() => {
    // Setup test tracer
    exporter = new InMemorySpanExporter();
    provider = new BasicTracerProvider();
    provider.addSpanProcessor({
      forceFlush: () => Promise.resolve(),
      onStart: () => {},
      onEnd: (span) => exporter.export([span], () => {}),
      shutdown: () => Promise.resolve(),
    });

    // Initialize SDK for tests
    (isConfigured as any).mockReturnValue(true);

    // Mock getTracerProvider to return our test provider
    (getTracerProvider as any).mockReturnValue(provider);
  });

  afterEach(() => {
    exporter.reset();
    provider.shutdown();
    vi.clearAllMocks();
  });

  describe('with uninitialized SDK', () => {
    it('should return unwrapped client when SDK not initialized', () => {
      (isConfigured as any).mockReturnValue(false);

      const mockClient = {
        complete: vi.fn(),
      };

      const wrapped = wrapAzureInference(mockClient);
      expect(wrapped).toBe(mockClient);
    });
  });

  describe('with REST client pattern', () => {
    it('should wrap REST client post method', async () => {
      const mockResponse = {
        body: {
          id: 'test-completion-id',
          object: 'chat.completion',
          created: Date.now(),
          model: 'Mistral-large',
          choices: [
            {
              index: 0,
              message: {
                role: 'assistant',
                content: 'Test response',
              },
              finish_reason: 'stop',
            },
          ],
          usage: {
            prompt_tokens: 10,
            completion_tokens: 5,
            total_tokens: 15,
          },
        },
      };

      const mockPost = vi.fn().mockResolvedValue(mockResponse);
      const mockPath = vi.fn().mockReturnValue({ post: mockPost });
      const mockClient = { path: mockPath };

      const wrapped = wrapAzureInference(mockClient);
      const pathClient = wrapped.path('/chat/completions');

      await pathClient.post({
        body: {
          model: 'Mistral-large',
          messages: [{ role: 'user', content: 'Hello' }],
          temperature: 0.7,
          max_tokens: 100,
        },
      });

      expect(mockPost).toHaveBeenCalled();

      // Wait for spans to be exported
      await new Promise((resolve) => setTimeout(resolve, 100));

      const spans = exporter.getFinishedSpans();
      expect(spans.length).toBe(1);

      const span = spans[0];
      expect(span.name).toBe('azure.ai.inference.chat Mistral-large');
      expect(span.kind).toBe(SpanKind.CLIENT);
      expect(span.attributes['gen_ai.system']).toBe('az_ai_inference');
      expect(span.attributes['gen_ai.request.model']).toBe('Mistral-large');
      expect(span.attributes['gen_ai.operation.name']).toBe('chat');
    });

    it('should handle streaming responses', async () => {
      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield {
            id: 'test-stream-id',
            object: 'chat.completion.chunk',
            created: Date.now(),
            model: 'Mistral-large',
            choices: [
              {
                index: 0,
                delta: { content: 'Test ' },
                finish_reason: null,
              },
            ],
          };
          yield {
            id: 'test-stream-id',
            object: 'chat.completion.chunk',
            created: Date.now(),
            model: 'Mistral-large',
            choices: [
              {
                index: 0,
                delta: { content: 'response' },
                finish_reason: 'stop',
              },
            ],
            usage: {
              prompt_tokens: 10,
              completion_tokens: 5,
              total_tokens: 15,
            },
          };
        },
      };

      const mockResponse = {
        asNodeStream: () => mockStream,
      };

      const mockPost = vi.fn().mockResolvedValue(mockResponse);
      const mockPath = vi.fn().mockReturnValue({ post: mockPost });
      const mockClient = { path: mockPath };

      const wrapped = wrapAzureInference(mockClient, { captureResponseData: true });
      const pathClient = wrapped.path('/chat/completions');

      const response = await pathClient.post({
        body: {
          model: 'Mistral-large',
          messages: [{ role: 'user', content: 'Hello' }],
          stream: true,
        },
      });

      // Consume the stream
      const stream = response.asNodeStream();
      let fullContent = '';
      for await (const chunk of stream) {
        if (chunk.choices?.[0]?.delta?.content) {
          fullContent += chunk.choices[0].delta.content;
        }
      }

      expect(fullContent).toBe('Test response');

      // Wait for spans to be exported
      await new Promise((resolve) => setTimeout(resolve, 100));

      const spans = exporter.getFinishedSpans();
      expect(spans.length).toBe(1);

      const span = spans[0];
      expect(span.attributes['gen_ai.usage.input_tokens']).toBe(10);
      expect(span.attributes['gen_ai.usage.output_tokens']).toBe(5);
    });
  });

  describe('with ChatCompletionsClient pattern', () => {
    it('should wrap complete method', async () => {
      const mockClient = {
        complete: vi.fn().mockResolvedValue({
          id: 'test-completion-id',
          object: 'chat.completion',
          created: Date.now(),
          model: 'test-model',
          choices: [
            {
              index: 0,
              message: {
                role: 'assistant',
                content: 'Test response',
              },
              finish_reason: 'stop',
            },
          ],
          usage: {
            prompt_tokens: 10,
            completion_tokens: 5,
            total_tokens: 15,
          },
        }),
        getModelInfo: vi.fn().mockResolvedValue({ model_name: 'test-model' }),
      };

      const wrapped = wrapAzureInference(mockClient, {
        captureRequestParams: true,
        captureResponseData: true,
      });

      await wrapped.complete({
        messages: [{ role: 'user', content: 'Hello' }],
        temperature: 0.7,
        max_tokens: 100,
      });

      expect(mockClient.complete).toHaveBeenCalled();

      // Wait for spans to be exported
      await new Promise((resolve) => setTimeout(resolve, 100));

      const spans = exporter.getFinishedSpans();
      expect(spans.length).toBe(1);

      const span = spans[0];
      expect(span.name).toBe('azure.ai.inference.chat test-model');
      expect(span.attributes['gen_ai.request.temperature']).toBe(0.7);
      expect(span.attributes['gen_ai.request.max_tokens']).toBe(100);
      expect(span.attributes['gen_ai.usage.input_tokens']).toBe(10);
      expect(span.attributes['gen_ai.usage.output_tokens']).toBe(5);
    });

    it('should handle streaming with complete method', async () => {
      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield {
            id: 'test-stream-id',
            object: 'chat.completion.chunk',
            created: Date.now(),
            model: 'test-model',
            choices: [
              {
                index: 0,
                delta: { content: 'Test ' },
                finish_reason: null,
              },
            ],
          };
          yield {
            id: 'test-stream-id',
            object: 'chat.completion.chunk',
            created: Date.now(),
            model: 'test-model',
            choices: [
              {
                index: 0,
                delta: { content: 'streaming' },
                finish_reason: 'stop',
              },
            ],
            usage: {
              prompt_tokens: 10,
              completion_tokens: 5,
              total_tokens: 15,
            },
          };
        },
      };

      const mockClient = {
        complete: vi.fn().mockResolvedValue(mockStream),
      };

      const wrapped = wrapAzureInference(mockClient, { captureResponseData: true });

      const stream = await wrapped.complete({
        model: 'test-model',
        messages: [{ role: 'user', content: 'Hello' }],
        stream: true,
      });

      let fullContent = '';
      for await (const chunk of stream) {
        if (chunk.choices?.[0]?.delta?.content) {
          fullContent += chunk.choices[0].delta.content;
        }
      }

      expect(fullContent).toBe('Test streaming');

      // Wait for spans to be exported
      await new Promise((resolve) => setTimeout(resolve, 100));

      const spans = exporter.getFinishedSpans();
      expect(spans.length).toBe(1);

      const span = spans[0];
      expect(span.attributes['gen_ai.usage.input_tokens']).toBe(10);
      expect(span.attributes['gen_ai.usage.output_tokens']).toBe(5);
    });
  });

  describe('error handling', () => {
    it('should handle errors properly', async () => {
      const mockError = new Error('API Error');
      const mockClient = {
        complete: vi.fn().mockRejectedValue(mockError),
      };

      const wrapped = wrapAzureInference(mockClient);

      await expect(
        wrapped.complete({
          model: 'test-model',
          messages: [{ role: 'user', content: 'Hello' }],
        }),
      ).rejects.toThrow('API Error');

      // Wait for spans to be exported
      await new Promise((resolve) => setTimeout(resolve, 100));

      const spans = exporter.getFinishedSpans();
      expect(spans.length).toBe(1);

      const span = spans[0];
      expect(span.status.code).toBe(SpanStatusCode.ERROR);
      expect(span.status.message).toBe('API Error');
    });
  });

  describe('custom options', () => {
    it('should use custom span name function', async () => {
      const mockClient = {
        complete: vi.fn().mockResolvedValue({
          id: 'test-id',
          choices: [{ message: { content: 'Test' }, finish_reason: 'stop' }],
        }),
      };

      const wrapped = wrapAzureInference(mockClient, {
        spanNameFn: (method, params) => `custom.${method}.${params.model || 'unknown'}`,
      });

      await wrapped.complete({
        model: 'custom-model',
        messages: [{ role: 'user', content: 'Hello' }],
      });

      // Wait for spans to be exported
      await new Promise((resolve) => setTimeout(resolve, 100));

      const spans = exporter.getFinishedSpans();
      expect(spans.length).toBe(1);
      expect(spans[0].name).toBe('custom.complete.custom-model');
    });
  });

  describe('message recording', () => {
    it('should record messages as events', async () => {
      const mockClient = {
        complete: vi.fn().mockResolvedValue({
          id: 'test-id',
          choices: [{ message: { content: 'Response' }, finish_reason: 'stop' }],
        }),
      };

      const wrapped = wrapAzureInference(mockClient);

      await wrapped.complete({
        model: 'test-model',
        messages: [
          { role: 'system', content: 'You are helpful' },
          { role: 'user', content: 'Hello' },
          { role: 'assistant', content: 'Hi there!' },
        ],
      });

      // Wait for spans to be exported
      await new Promise((resolve) => setTimeout(resolve, 100));

      const spans = exporter.getFinishedSpans();
      expect(spans.length).toBe(1);

      const span = spans[0];
      const events = span.events;

      // Should have message events for each input message
      const messageEvents = events.filter((e) => e.name.startsWith('gen_ai.'));
      expect(messageEvents.length).toBeGreaterThanOrEqual(3);
      expect(messageEvents[0].name).toBe('gen_ai.system.message');
      expect(messageEvents[0].attributes!['content']).toBe('You are helpful');
      expect(messageEvents[1].name).toBe('gen_ai.user.message');
      expect(messageEvents[1].attributes!['content']).toBe('Hello');
      expect(messageEvents[2].name).toBe('gen_ai.assistant.message');
      expect(messageEvents[2].attributes!['content']).toBe('Hi there!');
    });
  });

  describe('unsupported client', () => {
    it('should warn and return original client for unsupported types', () => {
      const mockClient = {
        someOtherMethod: vi.fn(),
      };

      const wrapped = wrapAzureInference(mockClient);
      expect(wrapped).toBe(mockClient);
    });
  });
});
