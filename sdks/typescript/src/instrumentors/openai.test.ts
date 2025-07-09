import { describe, it, expect, beforeEach, vi, afterEach, Mock } from 'vitest';
import { trace, SpanStatusCode, SpanKind } from '@opentelemetry/api';
import { OpenAIInstrumentor } from './openai';

// Mock logger
vi.mock('../utils/logger', () => ({
  logger: {
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    debug: vi.fn(),
  },
}));

// Mock settings
vi.mock('../utils/settings', () => ({
  getSettings: vi.fn(() => ({
    projectId: 'test-project-id',
  })),
}));

// Mock shutdown
vi.mock('../shutdown', () => ({
  isSDKShuttingDown: vi.fn(() => false),
}));

// Mock utils
vi.mock('../utils/json', () => ({
  safeStringify: vi.fn((obj) => JSON.stringify(obj)),
}));

vi.mock('../utils/stream-wrapper', () => ({
  StreamWrapper: vi.fn((stream, span, options) => {
    // Simulate processing chunks
    const chunks = [
      { choices: [{ delta: { content: 'Hello' } }] },
      {
        choices: [{ delta: { content: ' world' }, finish_reason: 'stop' }],
        usage: { prompt_tokens: 10, completion_tokens: 20, total_tokens: 30 },
      },
    ];

    setTimeout(() => {
      chunks.forEach((chunk) => options?.onChunk?.(chunk));
      options?.onFinalize?.();
    }, 0);

    return stream;
  }),
  isAsyncIterable: vi.fn((obj) => obj && typeof obj[Symbol.asyncIterator] === 'function'),
}));

import { logger } from '../utils/logger';
import { isSDKShuttingDown } from '../shutdown';
import { StreamWrapper, isAsyncIterable } from '../utils/stream-wrapper';
// safeStringify is mocked but not used directly in tests

describe('OpenAIInstrumentor', () => {
  let instrumentor: OpenAIInstrumentor;
  let mockTracer: any;
  let mockSpan: any;
  let mockOpenAIModule: any;
  let mockCreate: Mock;

  beforeEach(() => {
    vi.clearAllMocks();
    vi.resetModules();

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

    // Create mock create method
    mockCreate = vi.fn();

    // Create mock OpenAI module
    mockOpenAIModule = {
      default: vi.fn(function OpenAI() {
        this.chat = {
          completions: {
            create: mockCreate,
          },
        };
      }),
    };

    // Add prototype to the constructor
    mockOpenAIModule.default.prototype = {
      chat: {
        completions: {
          create: mockCreate,
        },
      },
    };

    // Mock require to return our module
    vi.doMock('openai', () => mockOpenAIModule);

    instrumentor = new OpenAIInstrumentor();
  });

  afterEach(() => {
    vi.doUnmock('openai');
    vi.restoreAllMocks();
  });

  describe('getName', () => {
    it('should return instrumentor name', () => {
      expect(instrumentor.getName()).toBe('OpenAI');
    });
  });

  describe('instrument', () => {
    it('should instrument OpenAI module', () => {
      instrumentor.instrument();

      expect(instrumentor.isInstrumented()).toBe(true);
      expect(logger.info).toHaveBeenCalledWith('OpenAI instrumentation enabled');
      expect(logger.debug).toHaveBeenCalledWith('Using OpenAI from default export');

      // The create method should be replaced
      expect(mockOpenAIModule.default.prototype.chat.completions.create).not.toBe(mockCreate);
    });

    it('should warn when already instrumented', () => {
      instrumentor.instrument();
      vi.clearAllMocks();

      instrumentor.instrument();

      expect(logger.warn).toHaveBeenCalledWith('OpenAI already instrumented');
    });

    it('should handle when openai module is not found', () => {
      vi.doUnmock('openai');
      vi.doMock('openai', () => {
        throw new Error('Module not found');
      });

      const newInstrumentor = new OpenAIInstrumentor();
      expect(() => newInstrumentor.instrument()).toThrow('OpenAI instrumentation failed');
      expect(logger.error).toHaveBeenCalledWith('Failed to instrument OpenAI:', expect.any(Error));
      expect(newInstrumentor.isInstrumented()).toBe(false);
    });

    it('should handle OpenAI from named export', () => {
      const namedExportCreate = vi.fn();
      const OpenAIClass = vi.fn(function OpenAI() {
        this.chat = {
          completions: {
            create: namedExportCreate,
          },
        };
      });

      OpenAIClass.prototype = {
        chat: {
          completions: {
            create: namedExportCreate,
          },
        },
      };

      vi.doUnmock('openai');
      vi.doMock('openai', () => ({
        OpenAI: OpenAIClass,
      }));

      const newInstrumentor = new OpenAIInstrumentor();
      newInstrumentor.instrument();

      expect(logger.debug).toHaveBeenCalledWith('Using OpenAI from named export');
      expect(newInstrumentor.isInstrumented()).toBe(true);
    });

    it('should handle OpenAI module directly', () => {
      const directCreate = vi.fn();
      const OpenAIClass = vi.fn(function OpenAI() {
        this.chat = {
          completions: {
            create: directCreate,
          },
        };
      });

      OpenAIClass.prototype = {
        chat: {
          completions: {
            create: directCreate,
          },
        },
      };

      vi.doUnmock('openai');
      vi.doMock('openai', () => OpenAIClass);

      const newInstrumentor = new OpenAIInstrumentor();
      newInstrumentor.instrument();

      expect(logger.debug).toHaveBeenCalledWith('Using OpenAI module directly');
      expect(newInstrumentor.isInstrumented()).toBe(true);
    });

    it('should handle missing prototype', () => {
      const OpenAIClass = {};

      vi.doUnmock('openai');
      vi.doMock('openai', () => ({
        default: OpenAIClass,
      }));

      const newInstrumentor = new OpenAIInstrumentor();
      newInstrumentor.instrument();

      expect(logger.error).toHaveBeenCalledWith('OpenAI.prototype is undefined');
      expect(newInstrumentor.isInstrumented()).toBe(true);
    });

    it('should handle missing chat property', () => {
      const OpenAIClass = vi.fn();
      OpenAIClass.prototype = {}; // No chat property

      vi.doUnmock('openai');
      vi.doMock('openai', () => ({
        default: OpenAIClass,
      }));

      const newInstrumentor = new OpenAIInstrumentor();
      newInstrumentor.instrument();

      expect(logger.error).toHaveBeenCalledWith('OpenAI.prototype.chat is undefined');
      expect(newInstrumentor.isInstrumented()).toBe(true);
    });

    it('should handle missing create method', () => {
      const OpenAIClass = vi.fn();
      OpenAIClass.prototype = {
        chat: {
          completions: {}, // No create method
        },
      };

      vi.doUnmock('openai');
      vi.doMock('openai', () => ({
        default: OpenAIClass,
      }));

      const newInstrumentor = new OpenAIInstrumentor();
      newInstrumentor.instrument();

      expect(logger.error).toHaveBeenCalledWith('Could not find chat.completions.create method');
      expect(newInstrumentor.isInstrumented()).toBe(true);
    });
  });

  describe('uninstrument', () => {
    it('should uninstrument OpenAI module', () => {
      instrumentor.instrument();
      vi.clearAllMocks();

      instrumentor.uninstrument();

      expect(instrumentor.isInstrumented()).toBe(false);
      expect(logger.info).toHaveBeenCalledWith('OpenAI instrumentation disabled');
    });

    it('should handle uninstrument when not instrumented', () => {
      instrumentor.uninstrument();

      expect(instrumentor.isInstrumented()).toBe(false);
      expect(logger.info).not.toHaveBeenCalled();
    });

    it('should handle errors during uninstrumentation', () => {
      instrumentor.instrument();

      // Force an error by making the module null
      (instrumentor as any).openaiModule = null;

      instrumentor.uninstrument();

      expect(instrumentor.isInstrumented()).toBe(false);
    });
  });

  describe('wrapChatCompletionsCreate', () => {
    let wrappedMethod: any;

    beforeEach(() => {
      instrumentor.instrument();

      // Get the wrapped method
      const OpenAI = mockOpenAIModule.default;
      wrappedMethod = OpenAI.prototype.chat.completions.create;
    });

    it('should skip instrumentation when SDK is shutting down', async () => {
      vi.mocked(isSDKShuttingDown).mockReturnValue(true);

      const params = { model: 'gpt-4', messages: [] };
      const expectedResult = { choices: [] };
      mockCreate.mockResolvedValue(expectedResult);

      const result = await wrappedMethod.call({}, params);

      expect(result).toBe(expectedResult);
      expect(mockTracer.startActiveSpan).not.toHaveBeenCalled();
    });

    it('should create span with all attributes', async () => {
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
        seed: 42,
        service_tier: 'custom',
      };

      mockCreate.mockResolvedValue({ choices: [] });

      await wrappedMethod.call({}, params);

      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        'openai.chat.completions gpt-4',
        expect.objectContaining({
          kind: SpanKind.CLIENT,
          attributes: expect.objectContaining({
            'gen_ai.system': 'openai',
            'gen_ai.request.model': 'gpt-4',
            'gen_ai.request.temperature': 0.7,
            'gen_ai.request.max_tokens': 100,
            'gen_ai.request.p': 0.9,
            'gen_ai.request.presence_penalty': 0.1,
            'gen_ai.request.frequency_penalty': 0.2,
            'gen_ai.openai.request.response_format': 'json',
            'gen_ai.openai.request.seed': 42,
            'gen_ai.openai.request.service_tier': 'custom',
            'gen_ai.operation.name': 'chat',
            'lilypad.type': 'llm',
          }),
        }),
        expect.any(Function),
      );
    });

    it('should record message events', async () => {
      const params = {
        model: 'gpt-4',
        messages: [
          { role: 'system', content: 'You are helpful' },
          { role: 'user', content: { type: 'text', text: 'Hello' } },
        ],
      };

      mockCreate.mockResolvedValue({ choices: [] });

      await wrappedMethod.call({}, params);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.system.message', {
        'gen_ai.system': 'openai',
        content: 'You are helpful',
      });

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.user.message', {
        'gen_ai.system': 'openai',
        content: '{"type":"text","text":"Hello"}',
      });
    });

    it('should handle streaming response', async () => {
      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield { choices: [{ delta: { content: 'Hello' } }] };
          yield { choices: [{ delta: { content: ' world' }, finish_reason: 'stop' }] };
        },
      };

      mockCreate.mockResolvedValue(mockStream);
      vi.mocked(isAsyncIterable).mockReturnValue(true);

      const params = { model: 'gpt-4', messages: [], stream: true };
      const result = await wrappedMethod.call({}, params);

      expect(StreamWrapper).toHaveBeenCalledWith(mockStream, mockSpan, expect.any(Object));
      expect(result).toBeDefined();
    });

    it('should record completion response', async () => {
      const response = {
        id: 'chatcmpl-123',
        model: 'gpt-4-0613',
        service_tier: 'custom',
        choices: [
          {
            message: { role: 'assistant', content: 'Hello!' },
            finish_reason: 'stop',
          },
          {
            message: { role: 'assistant', content: 'Hi!' },
            finish_reason: 'length',
          },
        ],
        usage: {
          prompt_tokens: 10,
          completion_tokens: 20,
          total_tokens: 30,
        },
      };

      mockCreate.mockResolvedValue(response);

      await wrappedMethod.call({}, { model: 'gpt-4', messages: [] });

      // Check choice events
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'openai',
        index: 0,
        finish_reason: 'stop',
        message: '{"role":"assistant","content":"Hello!"}',
      });

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'openai',
        index: 1,
        finish_reason: 'length',
        message: '{"role":"assistant","content":"Hi!"}',
      });

      // Check attributes
      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.finish_reasons', [
        'stop',
        'length',
      ]);

      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.usage.prompt_tokens': 10,
        'gen_ai.usage.completion_tokens': 20,
        'gen_ai.usage.total_tokens': 30,
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.model', 'gpt-4-0613');
      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.id', 'chatcmpl-123');
      expect(mockSpan.setAttribute).toHaveBeenCalledWith(
        'gen_ai.openai.response.service_tier',
        'custom',
      );

      expect(mockSpan.setStatus).toHaveBeenCalledWith({ code: SpanStatusCode.OK });
    });

    it('should handle errors', async () => {
      const error = new Error('API Error');
      mockCreate.mockRejectedValue(error);

      await expect(wrappedMethod.call({}, { model: 'gpt-4', messages: [] })).rejects.toThrow(
        'API Error',
      );

      expect(mockSpan.recordException).toHaveBeenCalledWith(error);
      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        error: true,
        'error.type': 'Error',
        'error.message': 'API Error',
      });
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'API Error',
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should handle non-Error exceptions', async () => {
      mockCreate.mockRejectedValue('String error');

      await expect(wrappedMethod.call({}, { model: 'gpt-4', messages: [] })).rejects.toBe(
        'String error',
      );

      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        error: true,
        'error.type': 'Error',
        'error.message': 'String error',
      });
    });

    it('should handle params with unknown model', async () => {
      mockCreate.mockResolvedValue({ choices: [] });

      await wrappedMethod.call({}, { messages: [] });

      expect(mockTracer.startActiveSpan).toHaveBeenCalledWith(
        'openai.chat.completions unknown',
        expect.any(Object),
        expect.any(Function),
      );
    });

    it('should filter out null/undefined attributes', async () => {
      const params = {
        model: 'gpt-4',
        messages: [],
        service_tier: 'auto', // Should be filtered out
      };

      mockCreate.mockResolvedValue({ choices: [] });

      await wrappedMethod.call({}, params);

      const call = mockTracer.startActiveSpan.mock.calls[0];
      const attributes = call[1].attributes;

      expect(attributes).not.toHaveProperty('gen_ai.openai.request.service_tier');
    });
  });

  describe('handleStreamingResponse', () => {
    it('should process streaming chunks and record completion', async () => {
      instrumentor.instrument();

      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield { choices: [{ delta: { content: 'Hello' } }] };
          yield {
            choices: [{ delta: { content: ' world' }, finish_reason: 'stop' }],
            usage: { prompt_tokens: 10, completion_tokens: 20, total_tokens: 30 },
          };
        },
      };

      mockCreate.mockResolvedValue(mockStream);
      vi.mocked(isAsyncIterable).mockReturnValue(true);

      const OpenAI = mockOpenAIModule.default;
      const wrappedMethod = OpenAI.prototype.chat.completions.create;

      await wrappedMethod.call({}, { model: 'gpt-4', messages: [], stream: true });

      // Wait for async operations
      await new Promise((resolve) => setTimeout(resolve, 10));

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'openai',
        index: 0,
        finish_reason: 'stop',
        message: '{"role":"assistant","content":"Hello world"}',
      });

      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.usage.prompt_tokens': 10,
        'gen_ai.usage.completion_tokens': 20,
        'gen_ai.usage.total_tokens': 30,
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.finish_reasons', [
        'stop',
      ]);
    });
  });

  describe('isCompletionsAPI', () => {
    it('should return true for valid completions API object', () => {
      const obj = {
        create: vi.fn(),
      };

      expect((instrumentor as any).isCompletionsAPI(obj)).toBe(true);
    });

    it('should return false for invalid objects', () => {
      expect((instrumentor as any).isCompletionsAPI(null)).toBe(false);
      expect((instrumentor as any).isCompletionsAPI(undefined)).toBe(false);
      expect((instrumentor as any).isCompletionsAPI({})).toBe(false);
      expect((instrumentor as any).isCompletionsAPI({ create: 'not a function' })).toBe(false);
    });
  });

  describe('recordCompletionResponse', () => {
    it('should handle response with no choices', () => {
      const response = {
        id: 'test',
        model: 'gpt-4',
      };

      (instrumentor as any).recordCompletionResponse(mockSpan, response);

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.model', 'gpt-4');
      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.id', 'test');
    });

    it('should handle null response', () => {
      (instrumentor as any).recordCompletionResponse(mockSpan, null);

      expect(mockSpan.addEvent).not.toHaveBeenCalled();
    });

    it('should handle choices without messages', () => {
      const response = {
        choices: [{ finish_reason: 'stop' }],
      };

      (instrumentor as any).recordCompletionResponse(mockSpan, response);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'openai',
        index: 0,
        finish_reason: 'stop',
        message: '{"role":"assistant"}',
      });
    });

    it('should handle auto service tier', () => {
      const response = {
        service_tier: 'auto',
      };

      (instrumentor as any).recordCompletionResponse(mockSpan, response);

      expect(mockSpan.setAttribute).not.toHaveBeenCalledWith(
        'gen_ai.openai.response.service_tier',
        expect.anything(),
      );
    });
  });
});
