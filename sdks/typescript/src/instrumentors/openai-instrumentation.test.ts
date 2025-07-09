import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { trace, SpanStatusCode, SpanKind } from '@opentelemetry/api';
import { instrumentOpenAICall } from './openai-instrumentation';
import { isSDKShuttingDown } from '../shutdown';
import { StreamWrapper } from '../utils/stream-wrapper';

// Mock modules
vi.mock('../utils/logger', () => ({
  logger: {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock('../shutdown', () => ({
  isSDKShuttingDown: vi.fn(() => false),
}));

vi.mock('../utils/stream-wrapper', () => ({
  StreamWrapper: vi.fn().mockImplementation((stream, span, options) => {
    // Return an async iterable that processes chunks through callbacks
    return {
      async *[Symbol.asyncIterator]() {
        if (options?.onChunk) {
          for await (const chunk of stream) {
            options.onChunk(chunk);
            yield chunk;
          }
        } else {
          yield* stream;
        }
        if (options?.onFinalize) {
          options.onFinalize();
        }
      },
    };
  }),
  isAsyncIterable: (obj: any) => obj && typeof obj[Symbol.asyncIterator] === 'function',
}));

describe('OpenAI Instrumentation', () => {
  let mockTracer: any;
  let mockSpan: any;

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
      startActiveSpan: vi.fn((name, options, callback) => {
        return callback(mockSpan);
      }),
    };

    // Mock trace API
    vi.spyOn(trace, 'getTracer').mockReturnValue(mockTracer);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('instrumentOpenAICall', () => {
    it('should skip instrumentation when SDK is shutting down', async () => {
      vi.mocked(isSDKShuttingDown).mockReturnValue(true);
      const originalFn = vi.fn().mockResolvedValue({ result: 'test' });
      const params = { model: 'gpt-4' };

      const result = await instrumentOpenAICall(originalFn, [params]);

      expect(originalFn).toHaveBeenCalledWith(params);
      expect(mockTracer.startActiveSpan).not.toHaveBeenCalled();
      expect(result).toEqual({ result: 'test' });
    });

    it('should create span for non-streaming completion', async () => {
      const originalFn = vi.fn().mockResolvedValue({
        choices: [
          {
            message: { role: 'assistant', content: 'Hello!' },
            finish_reason: 'stop',
          },
        ],
        usage: {
          prompt_tokens: 10,
          completion_tokens: 5,
          total_tokens: 15,
        },
        model: 'gpt-4-0613',
      });

      const params = {
        model: 'gpt-4',
        messages: [
          { role: 'system', content: 'You are helpful' },
          { role: 'user', content: 'Hello' },
        ],
        temperature: 0.7,
        max_tokens: 100,
        top_p: 0.9,
        presence_penalty: 0.1,
        frequency_penalty: 0.2,
        response_format: { type: 'json' },
        seed: 12345,
        service_tier: 'default',
      };

      const result = await instrumentOpenAICall(originalFn, [params, { timeout: 5000 }]);

      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        'openai.chat.completions gpt-4',
        expect.objectContaining({
          kind: SpanKind.CLIENT,
          attributes: expect.objectContaining({
            'gen_ai.system': 'openai',
            'gen_ai.request.model': 'gpt-4',
            'gen_ai.request.temperature': 0.7,
            'gen_ai.request.max_tokens': 100,
            'gen_ai.request.top_p': 0.9,
            'gen_ai.request.presence_penalty': 0.1,
            'gen_ai.request.frequency_penalty': 0.2,
            'gen_ai.openai.request.response_format': 'json',
            'gen_ai.openai.request.seed': 12345,
            'gen_ai.openai.request.service_tier': 'default',
            'gen_ai.operation.name': 'chat',
            'lilypad.type': 'function',
          }),
        }),
        expect.any(Function),
      );

      // Check message events
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.system.message', {
        'gen_ai.system': 'openai',
        content: 'You are helpful',
      });
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.user.message', {
        'gen_ai.system': 'openai',
        content: 'Hello',
      });

      // Check completion event
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'openai',
        index: 0,
        finish_reason: 'stop',
        message: '{"role":"assistant","content":"Hello!"}',
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.finish_reasons', [
        'stop',
      ]);

      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.usage.input_tokens': 10,
        'gen_ai.usage.output_tokens': 5,
        'gen_ai.usage.total_tokens': 15,
      });

      expect(mockSpan.setStatus).toHaveBeenCalledWith({ code: SpanStatusCode.OK });
      expect(mockSpan.end).toHaveBeenCalled();
      expect(result).toBeDefined();
    });

    it('should handle streaming response', async () => {
      const mockStream = {
        [Symbol.asyncIterator]: vi.fn(() => ({
          next: vi
            .fn()
            .mockResolvedValueOnce({
              value: { choices: [{ delta: { content: 'Hello' } }] },
              done: false,
            })
            .mockResolvedValueOnce({
              value: { choices: [{ delta: { content: ' world' }, finish_reason: 'stop' }] },
              done: false,
            })
            .mockResolvedValueOnce({ done: true }),
        })),
      };

      const originalFn = vi.fn().mockResolvedValue(mockStream);
      const params = { model: 'gpt-4', stream: true };

      const result = await instrumentOpenAICall(originalFn, [params]);

      expect(vi.mocked(StreamWrapper)).toHaveBeenCalledWith(
        mockStream,
        expect.any(Object), // span
        expect.objectContaining({
          onChunk: expect.any(Function),
          onFinalize: expect.any(Function),
        }),
      );
      expect(result).toBeDefined();
    });

    it('should handle errors', async () => {
      const error = new Error('API Error');
      const originalFn = vi.fn().mockRejectedValue(error);
      const params = { model: 'gpt-4' };

      await expect(instrumentOpenAICall(originalFn, [params])).rejects.toThrow('API Error');

      expect(mockSpan.recordException).toHaveBeenCalledWith(error);
      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.error.type': 'Error',
        'gen_ai.error.message': 'API Error',
      });
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'API Error',
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should handle missing model', async () => {
      const originalFn = vi.fn().mockResolvedValue({});
      const params = { messages: [] };

      await instrumentOpenAICall(originalFn, [params]);

      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        'openai.chat.completions unknown',
        expect.any(Object),
        expect.any(Function),
      );
    });

    it('should filter out null/undefined attributes', async () => {
      const originalFn = vi.fn().mockResolvedValue({});
      const params = {
        model: 'gpt-4',
        temperature: null,
        max_tokens: undefined,
        service_tier: 'auto', // Should be filtered out
      };

      await instrumentOpenAICall(originalFn, [params]);

      const attributes = mockTracer.startActiveSpan.mock.calls[0][1].attributes;
      expect(attributes['gen_ai.request.temperature']).toBeUndefined();
      expect(attributes['gen_ai.request.max_tokens']).toBeUndefined();
      expect(attributes['gen_ai.openai.request.service_tier']).toBeUndefined();
    });

    it('should handle non-string message content', async () => {
      const originalFn = vi.fn().mockResolvedValue({});
      const params = {
        model: 'gpt-4',
        messages: [{ role: 'user', content: { type: 'text', text: 'Hello' } }],
      };

      await instrumentOpenAICall(originalFn, [params]);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.user.message', {
        'gen_ai.system': 'openai',
        content: '{"type":"text","text":"Hello"}',
      });
    });

    it('should handle response without choices', async () => {
      const originalFn = vi.fn().mockResolvedValue({
        usage: {
          prompt_tokens: 10,
          completion_tokens: 0,
          total_tokens: 10,
        },
      });

      const params = { model: 'gpt-4' };

      await instrumentOpenAICall(originalFn, [params]);

      // Should only have message events, no choice events
      expect(mockSpan.addEvent).not.toHaveBeenCalledWith('gen_ai.choice', expect.any(Object));
      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.usage.input_tokens': 10,
        'gen_ai.usage.output_tokens': 0,
        'gen_ai.usage.total_tokens': 10,
      });
    });

    it('should handle old top_p parameter name', async () => {
      const originalFn = vi.fn().mockResolvedValue({});
      const params = {
        model: 'gpt-4',
        p: 0.95, // Old parameter name
      };

      await instrumentOpenAICall(originalFn, [params]);

      const attributes = mockTracer.startActiveSpan.mock.calls[0][1].attributes;
      expect(attributes['gen_ai.request.top_p']).toBe(0.95);
    });

    it('should handle null response', async () => {
      const originalFn = vi.fn().mockResolvedValue(null);
      const params = { model: 'gpt-4' };

      await instrumentOpenAICall(originalFn, [params]);

      // Should not crash
      expect(mockSpan.setStatus).toHaveBeenCalledWith({ code: SpanStatusCode.OK });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should handle empty messages array', async () => {
      const originalFn = vi.fn().mockResolvedValue({});
      const params = {
        model: 'gpt-4',
        messages: [],
      };

      await instrumentOpenAICall(originalFn, [params]);

      // Should not call addEvent for messages
      expect(mockSpan.addEvent).not.toHaveBeenCalledWith(
        expect.stringMatching(/gen_ai\.\w+\.message/),
        expect.any(Object),
      );
    });

    it('should handle message without content', async () => {
      const originalFn = vi.fn().mockResolvedValue({});
      const params = {
        model: 'gpt-4',
        messages: [{ role: 'user' }], // No content
      };

      await instrumentOpenAICall(originalFn, [params]);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.user.message', {
        'gen_ai.system': 'openai',
      });
    });

    it('should handle non-Error exceptions', async () => {
      const error = 'String error';
      const originalFn = vi.fn().mockRejectedValue(error);
      const params = { model: 'gpt-4' };

      await expect(instrumentOpenAICall(originalFn, [params])).rejects.toBe(error);

      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.error.type': 'Error',
        'gen_ai.error.message': 'String error',
      });
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'String error',
      });
    });

    it('should handle response with empty choices array', async () => {
      const originalFn = vi.fn().mockResolvedValue({
        choices: [],
        usage: {
          prompt_tokens: 10,
          completion_tokens: 0,
          total_tokens: 10,
        },
      });

      const params = { model: 'gpt-4' };

      await instrumentOpenAICall(originalFn, [params]);

      // Should not call setAttribute for finish_reasons
      expect(mockSpan.setAttribute).not.toHaveBeenCalledWith(
        'gen_ai.response.finish_reasons',
        expect.any(Array),
      );
    });

    it('should handle choice without message', async () => {
      const originalFn = vi.fn().mockResolvedValue({
        choices: [
          {
            finish_reason: 'stop',
            // No message property
          },
        ],
      });

      const params = { model: 'gpt-4' };

      await instrumentOpenAICall(originalFn, [params]);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'openai',
        index: 0,
        finish_reason: 'stop',
        message: '{"role":"assistant"}',
      });
    });

    it('should record response ID', async () => {
      const originalFn = vi.fn().mockResolvedValue({
        id: 'chatcmpl-123',
        choices: [],
      });

      const params = { model: 'gpt-4' };

      await instrumentOpenAICall(originalFn, [params]);

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.id', 'chatcmpl-123');
    });

    it('should record service tier when not auto', async () => {
      const originalFn = vi.fn().mockResolvedValue({
        service_tier: 'default',
        choices: [],
      });

      const params = { model: 'gpt-4' };

      await instrumentOpenAICall(originalFn, [params]);

      expect(mockSpan.setAttribute).toHaveBeenCalledWith(
        'gen_ai.openai.response.service_tier',
        'default',
      );
    });

    it('should not record service tier when auto', async () => {
      const originalFn = vi.fn().mockResolvedValue({
        service_tier: 'auto',
        choices: [],
      });

      const params = { model: 'gpt-4' };

      await instrumentOpenAICall(originalFn, [params]);

      expect(mockSpan.setAttribute).not.toHaveBeenCalledWith(
        'gen_ai.openai.response.service_tier',
        'auto',
      );
    });

    it('should handle streaming response with complete flow', async () => {
      const chunks = [
        {
          choices: [
            {
              delta: { content: 'Hello' },
            },
          ],
        },
        {
          choices: [
            {
              delta: { content: ' world' },
              finish_reason: 'stop',
            },
          ],
        },
        {
          choices: [
            {
              delta: {},
              finish_reason: 'stop',
            },
          ],
        },
      ];

      const mockStream = {
        async *[Symbol.asyncIterator]() {
          for (const chunk of chunks) {
            yield chunk;
          }
        },
      };

      const originalFn = vi.fn().mockResolvedValue(mockStream);

      // Mock StreamWrapper to actually call callbacks
      vi.mocked(StreamWrapper).mockImplementationOnce((stream, span, options) => {
        // Process chunks through callbacks
        const processStream = async () => {
          for await (const chunk of stream) {
            if (options?.onChunk) {
              options.onChunk(chunk);
            }
          }
          if (options?.onFinalize) {
            options.onFinalize();
          }
        };
        processStream();
        return stream;
      });

      const params = { model: 'gpt-4', stream: true };
      const _result = await instrumentOpenAICall(originalFn, [params]);

      // Wait for async processing
      await new Promise((resolve) => setTimeout(resolve, 10));

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'openai',
        index: 0,
        finish_reason: 'stop',
        message: '{"role":"assistant","content":"Hello world"}',
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.finish_reasons', [
        'stop',
      ]);
      expect(mockSpan.setStatus).toHaveBeenCalledWith({ code: SpanStatusCode.OK });
    });

    it('should handle streaming response with no content', async () => {
      const chunks = [
        {
          choices: [
            {
              delta: {},
            },
          ],
        },
      ];

      const mockStream = {
        async *[Symbol.asyncIterator]() {
          for (const chunk of chunks) {
            yield chunk;
          }
        },
      };

      const originalFn = vi.fn().mockResolvedValue(mockStream);

      // Mock StreamWrapper to actually call callbacks
      vi.mocked(StreamWrapper).mockImplementationOnce((stream, span, options) => {
        const processStream = async () => {
          for await (const chunk of stream) {
            if (options?.onChunk) {
              options.onChunk(chunk);
            }
          }
          if (options?.onFinalize) {
            options.onFinalize();
          }
        };
        processStream();
        return stream;
      });

      const params = { model: 'gpt-4', stream: true };
      await instrumentOpenAICall(originalFn, [params]);

      // Wait for async processing
      await new Promise((resolve) => setTimeout(resolve, 10));

      // Should still complete without error
      expect(mockSpan.setStatus).toHaveBeenCalledWith({ code: SpanStatusCode.OK });
    });

    it('should handle streaming response with no choices', async () => {
      const chunks = [
        {
          // No choices property
        },
      ];

      const mockStream = {
        async *[Symbol.asyncIterator]() {
          for (const chunk of chunks) {
            yield chunk;
          }
        },
      };

      const originalFn = vi.fn().mockResolvedValue(mockStream);

      // Mock StreamWrapper to actually call callbacks
      vi.mocked(StreamWrapper).mockImplementationOnce((stream, span, options) => {
        const processStream = async () => {
          for await (const chunk of stream) {
            if (options?.onChunk) {
              options.onChunk(chunk);
            }
          }
          if (options?.onFinalize) {
            options.onFinalize();
          }
        };
        processStream();
        return stream;
      });

      const params = { model: 'gpt-4', stream: true };
      await instrumentOpenAICall(originalFn, [params]);

      // Wait for async processing
      await new Promise((resolve) => setTimeout(resolve, 10));

      // Should still complete without error
      expect(mockSpan.setStatus).toHaveBeenCalledWith({ code: SpanStatusCode.OK });
    });

    it('should handle choices without finish_reason', async () => {
      const originalFn = vi.fn().mockResolvedValue({
        choices: [
          {
            message: { role: 'assistant', content: 'Hello!' },
            // No finish_reason
          },
        ],
      });

      const params = { model: 'gpt-4' };

      await instrumentOpenAICall(originalFn, [params]);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'openai',
        index: 0,
        finish_reason: 'error', // Default value
        message: '{"role":"assistant","content":"Hello!"}',
      });

      // Should not set finish_reasons attribute with empty array
      expect(mockSpan.setAttribute).not.toHaveBeenCalledWith('gen_ai.response.finish_reasons', []);
    });
  });
});
