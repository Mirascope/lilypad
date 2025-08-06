import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { SpanKind, SpanStatusCode } from '@opentelemetry/api';
import { instrument_openai } from './instrument-openai';
import { StreamWrapper } from '../utils/stream-wrapper';

vi.mock('../configure');

vi.mock('../utils/stream-wrapper');

describe('instrument_openai', () => {
  let mockClient: any;
  let mockTracer: any;
  let mockSpan: any;
  let consoleWarnSpy: any;

  beforeEach(async () => {
    vi.clearAllMocks();
    consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    mockSpan = {
      addEvent: vi.fn(),
      setAttribute: vi.fn(),
      setAttributes: vi.fn(),
      setStatus: vi.fn(),
      end: vi.fn(),
    };

    mockTracer = {
      startActiveSpan: vi.fn((name, options, callback) => {
        return callback(mockSpan);
      }),
    };

    const { getTracer } = await import('../configure');
    vi.mocked(getTracer).mockReturnValue(mockTracer);

    mockClient = {
      chat: {
        completions: {
          create: vi.fn().mockResolvedValue({
            id: 'test-id',
            model: 'gpt-4',
            choices: [
              {
                message: { role: 'assistant', content: 'Hello!' },
                finish_reason: 'stop',
              },
            ],
            usage: {
              prompt_tokens: 10,
              completion_tokens: 20,
              total_tokens: 30,
            },
          }),
        },
      },
      baseURL: 'https://api.openai.com',
    };
  });

  afterEach(() => {
    consoleWarnSpy.mockRestore();
  });

  describe('client validation', () => {
    it('should throw error for invalid client', () => {
      expect(() => instrument_openai(null as any)).toThrow(
        'Invalid client: must be an OpenAI client instance'
      );
      expect(() => instrument_openai(undefined as any)).toThrow(
        'Invalid client: must be an OpenAI client instance'
      );
      expect(() => instrument_openai('string' as any)).toThrow(
        'Invalid client: must be an OpenAI client instance'
      );
    });

    it('should throw error if client missing chat property', () => {
      expect(() => instrument_openai({} as any)).toThrow(
        'Invalid client structure: missing chat property'
      );
    });

    it('should throw error if chat is not an object', () => {
      expect(() => instrument_openai({ chat: 'string' } as any)).toThrow(
        'Invalid client structure: missing chat property'
      );
    });

    it('should throw error if client missing chat.completions', () => {
      expect(() => instrument_openai({ chat: {} } as any)).toThrow(
        'Invalid client structure: missing chat.completions property'
      );
    });

    it('should throw error if chat.completions is not an object', () => {
      expect(() =>
        instrument_openai({ chat: { completions: 'string' } } as any)
      ).toThrow('Invalid client structure: missing chat.completions property');
    });

    it('should throw error if create is not a function', () => {
      expect(() =>
        instrument_openai({
          chat: { completions: { create: 'not-a-function' } },
        } as any)
      ).toThrow(
        'Invalid client structure: chat.completions.create must be a function'
      );
    });

    it('should skip re-instrumentation', () => {
      const createFn = vi.fn();
      Object.defineProperty(createFn, '_lilypad_instrumented', {
        value: true,
        writable: false,
        enumerable: false,
        configurable: false,
      });

      const client = {
        chat: {
          completions: {
            create: createFn,
          },
        },
      };

      instrument_openai(client);

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'OpenAI client is already instrumented, skipping re-instrumentation'
      );
    });
  });

  describe('parameter validation', () => {
    beforeEach(() => {
      instrument_openai(mockClient);
    });

    it('should throw error for invalid parameters', async () => {
      await expect(mockClient.chat.completions.create(null)).rejects.toThrow(
        'Invalid parameters: must be an object'
      );
      await expect(
        mockClient.chat.completions.create(undefined)
      ).rejects.toThrow('Invalid parameters: must be an object');
      await expect(
        mockClient.chat.completions.create('string')
      ).rejects.toThrow('Invalid parameters: must be an object');
    });

    it('should throw error for missing model', async () => {
      await expect(
        mockClient.chat.completions.create({ messages: [] })
      ).rejects.toThrow(
        'Invalid parameters: model is required and must be a string'
      );
      await expect(
        mockClient.chat.completions.create({ model: null, messages: [] })
      ).rejects.toThrow(
        'Invalid parameters: model is required and must be a string'
      );
      await expect(
        mockClient.chat.completions.create({ model: 123, messages: [] })
      ).rejects.toThrow(
        'Invalid parameters: model is required and must be a string'
      );
    });

    it('should throw error for invalid messages', async () => {
      await expect(
        mockClient.chat.completions.create({ model: 'gpt-4' })
      ).rejects.toThrow('Invalid parameters: messages must be an array');
      await expect(
        mockClient.chat.completions.create({
          model: 'gpt-4',
          messages: 'string',
        })
      ).rejects.toThrow('Invalid parameters: messages must be an array');
    });

    it('should throw error for empty messages', async () => {
      await expect(
        mockClient.chat.completions.create({ model: 'gpt-4', messages: [] })
      ).rejects.toThrow('Invalid parameters: messages array cannot be empty');
    });

    it('should throw error for invalid message structure', async () => {
      await expect(
        mockClient.chat.completions.create({
          model: 'gpt-4',
          messages: ['string'],
        })
      ).rejects.toThrow('Invalid message at index 0: must be an object');

      await expect(
        mockClient.chat.completions.create({
          model: 'gpt-4',
          messages: [{ content: 'hello' }],
        })
      ).rejects.toThrow('Invalid message at index 0: role is required');
    });
  });

  describe('successful instrumentation', () => {
    beforeEach(() => {
      instrument_openai(mockClient);
    });

    it('should instrument basic chat completion', async () => {
      const params = {
        model: 'gpt-4',
        messages: [{ role: 'user', content: 'Hello!' }],
      };

      const result = await mockClient.chat.completions.create(params);

      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        'chat gpt-4',
        {
          kind: SpanKind.CLIENT,
          attributes: expect.objectContaining({
            'gen_ai.operation.name': 'chat',
            'gen_ai.request.model': 'gpt-4',
            'gen_ai.system': 'openai',
            'server.address': 'api.openai.com',
          }),
        },
        expect.any(Function)
      );

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.content.prompt', {
        'gen_ai.prompt': JSON.stringify({ role: 'user', content: 'Hello!' }),
      });

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'openai',
        index: 0,
        finish_reason: 'stop',
        message: JSON.stringify({ role: 'assistant', content: 'Hello!' }),
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith(
        'gen_ai.response.finish_reasons',
        ['stop']
      );

      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.usage.input_tokens': 10,
        'gen_ai.usage.output_tokens': 20,
        'gen_ai.usage.total_tokens': 30,
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith(
        'gen_ai.response.model',
        'gpt-4'
      );

      expect(mockSpan.setAttribute).toHaveBeenCalledWith(
        'gen_ai.response.id',
        'test-id'
      );

      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.OK,
      });

      expect(mockSpan.end).toHaveBeenCalled();
      expect(result).toEqual({
        id: 'test-id',
        model: 'gpt-4',
        choices: [
          {
            message: { role: 'assistant', content: 'Hello!' },
            finish_reason: 'stop',
          },
        ],
        usage: {
          prompt_tokens: 10,
          completion_tokens: 20,
          total_tokens: 30,
        },
      });
    });

    it('should handle optional parameters', async () => {
      const params = {
        model: 'gpt-4',
        messages: [{ role: 'user', content: 'Hello!' }],
        temperature: 0.7,
        max_tokens: 100,
        top_p: 0.9,
        presence_penalty: 0.1,
        frequency_penalty: 0.2,
        response_format: { type: 'json_object' },
        seed: 42,
        service_tier: 'premium',
      };

      await mockClient.chat.completions.create(params);

      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        'chat gpt-4',
        {
          kind: SpanKind.CLIENT,
          attributes: expect.objectContaining({
            'gen_ai.request.temperature': 0.7,
            'gen_ai.request.max_tokens': 100,
            'gen_ai.request.top_p': 0.9,
            'gen_ai.request.presence_penalty': 0.1,
            'gen_ai.request.frequency_penalty': 0.2,
            'gen_ai.openai.request.response_format': 'json_object',
            'gen_ai.openai.request.seed': 42,
            'gen_ai.openai.response.service_tier': 'premium',
          }),
        },
        expect.any(Function)
      );
    });

    it('should handle response_format object without type', async () => {
      const params = {
        model: 'gpt-4',
        messages: [{ role: 'user', content: 'Hello!' }],
        response_format: { someOtherProperty: 'value' },
      };

      await mockClient.chat.completions.create(params);

      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        expect.any(String),
        {
          kind: SpanKind.CLIENT,
          attributes: expect.not.objectContaining({
            'gen_ai.openai.request.response_format': expect.anything(),
          }),
        },
        expect.any(Function)
      );
    });

    it('should skip auto service tier', async () => {
      const params = {
        model: 'gpt-4',
        messages: [{ role: 'user', content: 'Hello!' }],
        service_tier: 'auto',
      };

      await mockClient.chat.completions.create(params);

      const attributes = mockTracer.startActiveSpan.mock.calls[0][1].attributes;
      expect(attributes).not.toHaveProperty(
        'gen_ai.openai.response.service_tier'
      );
    });

    it('should handle openrouter base URL', async () => {
      mockClient.baseURL = 'https://openrouter.ai/api/v1';
      instrument_openai(mockClient);

      const params = {
        model: 'gpt-4',
        messages: [{ role: 'user', content: 'Hello!' }],
      };

      await mockClient.chat.completions.create(params);

      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        'chat gpt-4',
        {
          kind: SpanKind.CLIENT,
          attributes: expect.objectContaining({
            'gen_ai.system': 'openrouter',
            'server.address': 'openrouter.ai',
          }),
        },
        expect.any(Function)
      );
    });

    it('should handle streaming response', async () => {
      const mockStream = { async *[Symbol.asyncIterator]() {} };
      mockClient.chat.completions.create.mockResolvedValue(mockStream);

      const params = {
        model: 'gpt-4',
        messages: [{ role: 'user', content: 'Hello!' }],
        stream: true,
      };

      const result = await mockClient.chat.completions.create(params);

      expect(StreamWrapper).toHaveBeenCalledWith(mockSpan, mockStream);
      expect(result).toBeInstanceOf(StreamWrapper);
      expect(mockSpan.end).not.toHaveBeenCalled();
    });

    it('should handle multiple messages', async () => {
      const params = {
        model: 'gpt-4',
        messages: [
          { role: 'system', content: 'You are a helpful assistant.' },
          { role: 'user', content: 'Hello!' },
          { role: 'assistant', content: 'Hi there!' },
          { role: 'user', content: 'How are you?' },
        ],
      };

      await mockClient.chat.completions.create(params);

      expect(mockSpan.addEvent).toHaveBeenCalledTimes(5);
      params.messages.forEach((message, index) => {
        expect(mockSpan.addEvent).toHaveBeenNthCalledWith(
          index + 1,
          'gen_ai.content.prompt',
          {
            'gen_ai.prompt': JSON.stringify(message),
          }
        );
      });
    });

    it('should handle response without optional fields', async () => {
      mockClient.chat.completions.create.mockResolvedValue({
        choices: [],
      });

      const params = {
        model: 'gpt-4',
        messages: [{ role: 'user', content: 'Hello!' }],
      };

      await mockClient.chat.completions.create(params);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.content.prompt', {
        'gen_ai.prompt': JSON.stringify({ role: 'user', content: 'Hello!' }),
      });
      expect(mockSpan.setAttribute).not.toHaveBeenCalledWith(
        'gen_ai.response.model',
        expect.any(String)
      );
      expect(mockSpan.setAttribute).not.toHaveBeenCalledWith(
        'gen_ai.response.id',
        expect.any(String)
      );
    });

    it('should handle choice with missing finish_reason', async () => {
      mockClient.chat.completions.create.mockResolvedValue({
        choices: [
          {
            message: { role: 'assistant', content: 'Hello!' },
          },
        ],
      });

      const params = {
        model: 'gpt-4',
        messages: [{ role: 'user', content: 'Hello!' }],
      };

      await mockClient.chat.completions.create(params);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'openai',
        index: 0,
        finish_reason: 'error',
        message: JSON.stringify({ role: 'assistant', content: 'Hello!' }),
      });

      expect(mockSpan.setAttribute).not.toHaveBeenCalledWith(
        'gen_ai.response.finish_reasons',
        expect.any(Array)
      );
    });

    it('should handle choice with missing message content', async () => {
      mockClient.chat.completions.create.mockResolvedValue({
        choices: [
          {
            message: { role: 'assistant' },
            finish_reason: 'stop',
          },
        ],
      });

      const params = {
        model: 'gpt-4',
        messages: [{ role: 'user', content: 'Hello!' }],
      };

      await mockClient.chat.completions.create(params);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'openai',
        index: 0,
        finish_reason: 'stop',
        message: JSON.stringify({ role: 'assistant', content: '' }),
      });
    });

    it('should handle choice with missing message', async () => {
      mockClient.chat.completions.create.mockResolvedValue({
        choices: [
          {
            finish_reason: 'stop',
          },
        ],
      });

      const params = {
        model: 'gpt-4',
        messages: [{ role: 'user', content: 'Hello!' }],
      };

      await mockClient.chat.completions.create(params);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'openai',
        index: 0,
        finish_reason: 'stop',
        message: JSON.stringify({ role: 'assistant', content: '' }),
      });
    });

    it('should maintain original function properties', async () => {
      const originalCreate = mockClient.chat.completions.create;
      originalCreate.customProperty = 'test';
      originalCreate.customMethod = vi.fn();

      instrument_openai(mockClient);

      expect(mockClient.chat.completions.create.customProperty).toBe('test');
      expect(mockClient.chat.completions.create.customMethod).toBe(
        originalCreate.customMethod
      );
    });

    it('should preserve this context', async () => {
      const originalCreate = vi.fn().mockResolvedValue({
        id: 'test-id',
        model: 'gpt-4',
        choices: [
          {
            message: { role: 'assistant', content: 'Hello!' },
            finish_reason: 'stop',
          },
        ],
      });

      mockClient.chat.completions.create = originalCreate;
      instrument_openai(mockClient);

      const params = {
        model: 'gpt-4',
        messages: [{ role: 'user', content: 'Hello!' }],
      };

      await mockClient.chat.completions.create(params);

      expect(originalCreate).toHaveBeenCalled();
    });
  });

  describe('error handling', () => {
    beforeEach(() => {
      instrument_openai(mockClient);
    });

    it('should handle errors properly', async () => {
      const error = new Error('API request failed');
      const originalCreate = mockClient.chat.completions.create;
      originalCreate.mockRejectedValue(error);

      const params = {
        model: 'gpt-4',
        messages: [{ role: 'user', content: 'Hello!' }],
      };

      await expect(mockClient.chat.completions.create(params)).rejects.toThrow(
        'API request failed'
      );

      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'API request failed',
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('error.type', 'Error');

      expect(mockSpan.addEvent).toHaveBeenCalledWith('error', {
        'error.type': 'Error',
        'error.message': 'API request failed',
        'error.stack': error.stack,
      });

      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should handle non-Error objects', async () => {
      mockClient.chat.completions.create.mockRejectedValue('String error');

      const params = {
        model: 'gpt-4',
        messages: [{ role: 'user', content: 'Hello!' }],
      };

      await expect(mockClient.chat.completions.create(params)).rejects.toThrow(
        'String error'
      );

      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'String error',
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith(
        'error.type',
        'UnknownError'
      );

      expect(mockSpan.addEvent).toHaveBeenCalledWith('error', {
        'error.type': 'UnknownError',
        'error.message': 'String error',
        'error.stack': 'No stack trace available',
      });

      expect(mockSpan.end).toHaveBeenCalled();
    });
  });
});
