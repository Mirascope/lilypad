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
  StreamWrapper: vi.fn().mockImplementation((stream) => {
    const handlers: Record<string, Function[]> = {};
    return {
      on: (event: string, handler: Function) => {
        if (!handlers[event]) handlers[event] = [];
        handlers[event].push(handler);
      },
      emit: (event: string, ...args: any[]) => {
        if (handlers[event]) {
          handlers[event].forEach((h) => h(...args));
        }
      },
      [Symbol.asyncIterator]: () => stream[Symbol.asyncIterator](),
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
  });
});
