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

vi.mock('./utils/stream-wrapper', () => ({
  isAsyncIterable: vi.fn(),
}));

vi.mock('./utils/error-handler', () => ({
  ensureError: vi.fn(),
}));

// Import after mocking
import { wrapGoogle } from './wrap-google';
import { trace, context, SpanKind, SpanStatusCode } from '@opentelemetry/api';
import { logger } from './utils/logger';
import { isAsyncIterable } from './utils/stream-wrapper';
import { ensureError } from './utils/error-handler';

// Get mocked functions
const mockedTrace = vi.mocked(trace);
const mockedContext = vi.mocked(context);
const mockedLogger = vi.mocked(logger);
const mockedIsAsyncIterable = vi.mocked(isAsyncIterable);
const mockedEnsureError = vi.mocked(ensureError);

describe('wrapGoogle', () => {
  let mockSpan: any;
  let mockTracer: any;
  let mockGenerateContent: any;
  let mockGenerateContentStream: any;
  let GoogleClass: any;

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
    mockedIsAsyncIterable.mockImplementation((value) => {
      return value != null && typeof value === 'object' && Symbol.asyncIterator in value;
    });
    mockedEnsureError.mockImplementation((error) => {
      if (error instanceof Error) return error;
      return new Error(String(error));
    });

    // Mock original methods
    mockGenerateContent = vi.fn();
    mockGenerateContentStream = vi.fn();

    // Create base Google class
    GoogleClass = class {
      getGenerativeModel(config: { model: string }) {
        return {
          generateContent: mockGenerateContent,
          generateContentStream: mockGenerateContentStream,
          model: config.model,
        };
      }
    };
  });

  describe('class wrapping', () => {
    it('should create a wrapped class that extends the original', () => {
      const WrappedGoogle = wrapGoogle(GoogleClass);
      const instance = new WrappedGoogle();

      expect(instance).toBeInstanceOf(GoogleClass);
      expect(instance.getGenerativeModel).toBeDefined();
    });

    it('should log debug message when wrapping', () => {
      wrapGoogle(GoogleClass);

      expect(mockedLogger.debug).toHaveBeenCalledWith('[wrapGoogle] Wrapping Google instance');
    });

    it('should handle missing getGenerativeModel gracefully', () => {
      const EmptyClass = class {};
      const WrappedClass = wrapGoogle(EmptyClass);
      const instance = new WrappedClass();

      expect(instance).toBeInstanceOf(EmptyClass);
    });
  });

  describe('generateContent wrapping', () => {
    it('should create a span with correct attributes', async () => {
      const WrappedGoogle = wrapGoogle(GoogleClass);
      const instance = new WrappedGoogle();
      const model = instance.getGenerativeModel({ model: 'gemini-pro' });

      const params = {
        contents: [{ role: 'user', parts: [{ text: 'Hello' }] }],
        generation_config: {
          temperature: 0.7,
          max_output_tokens: 100,
          top_p: 0.9,
          top_k: 20,
        },
      };

      mockGenerateContent.mockResolvedValue({ candidates: [] });

      await model.generateContent(params);

      expect(mockTracer.startSpan).toHaveBeenCalledWith('chat gemini-pro', {
        kind: SpanKind.CLIENT,
        attributes: {
          'gen_ai.system': 'gemini',
          'server.address': 'generativelanguage.googleapis.com',
          'gen_ai.request.model': 'gemini-pro',
          'gen_ai.request.temperature': 0.7,
          'gen_ai.request.max_tokens': 100,
          'gen_ai.request.top_p': 0.9,
          'gen_ai.request.top_k': 20,
          'gen_ai.operation.name': 'chat',
        },
      });
    });

    it('should handle string input', async () => {
      const WrappedGoogle = wrapGoogle(GoogleClass);
      const instance = new WrappedGoogle();
      const model = instance.getGenerativeModel({ model: 'gemini-pro' });

      mockGenerateContent.mockResolvedValue({ candidates: [] });

      await model.generateContent('Hello Google!');

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.user.message', {
        'gen_ai.system': 'gemini',
        content: 'Hello Google!',
      });
    });

    it('should record message events', async () => {
      const WrappedGoogle = wrapGoogle(GoogleClass);
      const instance = new WrappedGoogle();
      const model = instance.getGenerativeModel({ model: 'gemini-pro' });

      const params = {
        contents: [
          { role: 'system', parts: [{ text: 'You are helpful' }] },
          { role: 'user', parts: [{ text: 'Hello' }] },
          { role: 'model', parts: [{ text: 'Hi there!' }] },
          { role: 'user', parts: [{ text: 'How are you?' }] },
        ],
      };

      mockGenerateContent.mockResolvedValue({ candidates: [] });

      await model.generateContent(params);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.system.message', {
        'gen_ai.system': 'gemini',
        content: 'You are helpful',
      });
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.user.message', {
        'gen_ai.system': 'gemini',
        content: 'Hello',
      });
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.assistant.message', {
        'gen_ai.system': 'gemini',
        content: 'Hi there!',
      });
    });

    it('should handle image content', async () => {
      const WrappedGoogle = wrapGoogle(GoogleClass);
      const instance = new WrappedGoogle();
      const model = instance.getGenerativeModel({ model: 'gemini-pro-vision' });

      const params = {
        contents: [
          {
            role: 'user',
            parts: [
              { text: 'What is in this image?' },
              { inline_data: { mime_type: 'image/jpeg', data: 'base64data' } },
            ],
          },
        ],
      };

      mockGenerateContent.mockResolvedValue({ candidates: [] });

      await model.generateContent(params);

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.user.message', {
        'gen_ai.system': 'gemini',
        content: 'What is in this image?[binary data]',
      });
    });

    it('should record response data', async () => {
      const WrappedGoogle = wrapGoogle(GoogleClass);
      const instance = new WrappedGoogle();
      const model = instance.getGenerativeModel({ model: 'gemini-pro' });

      const response = {
        candidates: [
          {
            content: {
              parts: [{ text: 'Hello! ' }, { text: 'How can I help?' }],
              role: 'model',
            },
            finish_reason: 'STOP',
            index: 0,
            safety_ratings: [{ category: 'HARM_CATEGORY_HARASSMENT', probability: 'NEGLIGIBLE' }],
          },
        ],
        usage_metadata: {
          prompt_token_count: 10,
          candidates_token_count: 20,
          total_token_count: 30,
        },
      };

      mockGenerateContent.mockResolvedValue(response);

      await model.generateContent('Hello');

      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'gemini',
        index: 0,
        finish_reason: 'STOP',
        message: JSON.stringify({ role: 'model', content: 'Hello! How can I help?' }),
      });

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.finish_reasons', [
        'STOP',
      ]);

      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.usage.input_tokens': 10,
        'gen_ai.usage.output_tokens': 20,
        'gen_ai.usage.total_tokens': 30,
      });
    });

    it('should handle errors', async () => {
      const WrappedGoogle = wrapGoogle(GoogleClass);
      const instance = new WrappedGoogle();
      const model = instance.getGenerativeModel({ model: 'gemini-pro' });

      const error = new Error('API Error');
      mockGenerateContent.mockRejectedValue(error);

      await expect(model.generateContent('Hello')).rejects.toThrow('API Error');

      expect(mockSpan.recordException).toHaveBeenCalledWith(error);
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'API Error',
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should pass through all arguments to original method', async () => {
      const WrappedGoogle = wrapGoogle(GoogleClass);
      const instance = new WrappedGoogle();
      const model = instance.getGenerativeModel({ model: 'gemini-pro' });

      const params = { contents: [] };
      const options = { timeout: 30000 };

      mockGenerateContent.mockResolvedValue({ candidates: [] });

      await model.generateContent(params, options);

      expect(mockGenerateContent).toHaveBeenCalledWith(params, options);
    });
  });

  describe('generateContentStream wrapping', () => {
    it('should handle streaming responses', async () => {
      const WrappedGoogle = wrapGoogle(GoogleClass);
      const instance = new WrappedGoogle();
      const model = instance.getGenerativeModel({ model: 'gemini-pro' });

      // Create a mock async iterable
      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield {
            candidates: [
              {
                content: { parts: [{ text: 'Hello' }] },
                index: 0,
              },
            ],
          };
          yield {
            candidates: [
              {
                content: { parts: [{ text: ' world!' }] },
                finish_reason: 'STOP',
                index: 0,
              },
            ],
            usage_metadata: {
              prompt_token_count: 5,
              candidates_token_count: 10,
              total_token_count: 15,
            },
          };
        },
      };

      mockGenerateContentStream.mockResolvedValue(mockStream);

      const streamPromise = model.generateContentStream('Hello');
      const stream = await streamPromise;

      // Consume the stream
      const chunks = [];
      for await (const chunk of stream) {
        chunks.push(chunk);
      }

      expect(chunks).toHaveLength(2);
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'gemini',
        index: 0,
        finish_reason: 'STOP',
        message: JSON.stringify({ role: 'model', content: 'Hello world!' }),
      });
      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.finish_reasons', [
        'STOP',
      ]);
      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.usage.input_tokens': 5,
        'gen_ai.usage.output_tokens': 10,
        'gen_ai.usage.total_tokens': 15,
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should handle streaming errors', async () => {
      const WrappedGoogle = wrapGoogle(GoogleClass);
      const instance = new WrappedGoogle();
      const model = instance.getGenerativeModel({ model: 'gemini-pro' });

      const error = new Error('Stream error');
      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield {
            candidates: [
              {
                content: { parts: [{ text: 'Hello' }] },
                index: 0,
              },
            ],
          };
          throw error;
        },
      };

      mockGenerateContentStream.mockResolvedValue(mockStream);

      const streamPromise = model.generateContentStream('Hello');
      const stream = await streamPromise;

      const chunks = [];
      await expect(async () => {
        for await (const chunk of stream) {
          chunks.push(chunk);
        }
      }).rejects.toThrow('Stream error');

      expect(mockSpan.recordException).toHaveBeenCalledWith(error);
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'Stream error',
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });

    it('should handle error during stream creation', async () => {
      const WrappedGoogle = wrapGoogle(GoogleClass);
      const instance = new WrappedGoogle();
      const model = instance.getGenerativeModel({ model: 'gemini-pro' });

      const error = new Error('Stream creation error');
      mockGenerateContentStream.mockRejectedValue(error);

      await expect(model.generateContentStream('Hello')).rejects.toThrow('Stream creation error');

      expect(mockSpan.recordException).toHaveBeenCalledWith(error);
      expect(mockSpan.setStatus).toHaveBeenCalledWith({
        code: SpanStatusCode.ERROR,
        message: 'Stream creation error',
      });
      expect(mockSpan.end).toHaveBeenCalled();
    });
  });

  describe('isGenerateContentResponse type guard', () => {
    it('should handle non-response objects', async () => {
      const WrappedGoogle = wrapGoogle(GoogleClass);
      const instance = new WrappedGoogle();
      const model = instance.getGenerativeModel({ model: 'gemini-pro' });

      mockGenerateContent.mockResolvedValue(null);

      await model.generateContent('Hello');

      expect(mockSpan.addEvent).not.toHaveBeenCalledWith('gen_ai.choice', expect.any(Object));
    });

    it('should handle response without candidates', async () => {
      const WrappedGoogle = wrapGoogle(GoogleClass);
      const instance = new WrappedGoogle();
      const model = instance.getGenerativeModel({ model: 'gemini-pro' });

      mockGenerateContent.mockResolvedValue({ candidates: null });

      await model.generateContent('Hello');

      expect(mockSpan.addEvent).not.toHaveBeenCalledWith('gen_ai.choice', expect.any(Object));
    });
  });

  describe('instance wrapping', () => {
    it('should wrap an existing Google instance', () => {
      const instance = new GoogleClass();
      const originalGetModel = instance.getGenerativeModel;

      const wrappedInstance = wrapGoogle(instance);

      expect(wrappedInstance).toBe(instance); // Modified in-place
      expect(instance.getGenerativeModel).not.toBe(originalGetModel);
      expect(instance.getGenerativeModel).toBeDefined();
    });

    it('should wrap GenerativeModel methods', () => {
      const instance = new GoogleClass();
      const wrappedInstance = wrapGoogle(instance);

      const model = wrappedInstance.getGenerativeModel({ model: 'gemini-pro' });

      expect(model.generateContent).toBeDefined();
      expect(model.generateContent).not.toBe(mockGenerateContent);
      expect(model.generateContentStream).toBeDefined();
      expect(model.generateContentStream).not.toBe(mockGenerateContentStream);
    });

    it('should handle instance without getGenerativeModel', () => {
      const instance = {};
      const wrappedInstance = wrapGoogle(instance);

      expect(wrappedInstance).toBe(instance);
      // Should not throw
    });
  });

  describe('recordResponse helper', () => {
    it('should handle empty response', async () => {
      const WrappedGoogle = wrapGoogle(GoogleClass);
      const instance = new WrappedGoogle();
      const model = instance.getGenerativeModel({ model: 'gemini-pro' });

      mockGenerateContent.mockResolvedValue({});

      await model.generateContent('Hello');

      expect(mockSpan.addEvent).not.toHaveBeenCalledWith('gen_ai.choice', expect.any(Object));
    });

    it('should handle candidates with missing content', async () => {
      const WrappedGoogle = wrapGoogle(GoogleClass);
      const instance = new WrappedGoogle();
      const model = instance.getGenerativeModel({ model: 'gemini-pro' });

      const response = {
        candidates: [
          {
            content: null, // content exists but is null
            finish_reason: 'STOP',
          },
        ],
      };

      mockGenerateContent.mockResolvedValue(response);

      await model.generateContent('Hello');

      // Should not add event for candidate with null content
      expect(mockSpan.addEvent).not.toHaveBeenCalledWith('gen_ai.choice', expect.any(Object));
    });

    it('should filter out falsy finish reasons', async () => {
      const WrappedGoogle = wrapGoogle(GoogleClass);
      const instance = new WrappedGoogle();
      const model = instance.getGenerativeModel({ model: 'gemini-pro' });

      const response = {
        candidates: [
          { content: { parts: [{ text: 'a' }] }, finish_reason: 'STOP' },
          { content: { parts: [{ text: 'b' }] }, finish_reason: null },
          { content: { parts: [{ text: 'c' }] }, finish_reason: '' },
          { content: { parts: [{ text: 'd' }] }, finish_reason: 'MAX_TOKENS' },
        ],
      };

      mockGenerateContent.mockResolvedValue(response);

      await model.generateContent('Hello');

      expect(mockSpan.setAttribute).toHaveBeenCalledWith('gen_ai.response.finish_reasons', [
        'STOP',
        'MAX_TOKENS',
      ]);
    });

    it('should record server.address attribute', async () => {
      const WrappedGoogle = wrapGoogle(GoogleClass);
      const instance = new WrappedGoogle();
      const model = instance.getGenerativeModel({ model: 'gemini-pro' });

      const response = {
        candidates: [{ content: { parts: [{ text: 'test' }] } }],
      };

      mockGenerateContent.mockResolvedValue(response);

      await model.generateContent('Hello');

      expect(mockSpan.setAttribute).toHaveBeenCalledWith(
        'server.address',
        'generativelanguage.googleapis.com',
      );
    });
  });

  describe('wrapStream helper', () => {
    it('should handle stream with usage in chunks', async () => {
      const WrappedGoogle = wrapGoogle(GoogleClass);
      const instance = new WrappedGoogle();
      const model = instance.getGenerativeModel({ model: 'gemini-pro' });

      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield {
            candidates: [
              {
                content: { parts: [{ text: 'Hello' }] },
                index: 0,
              },
            ],
            usage_metadata: {
              prompt_token_count: 5,
              candidates_token_count: 5,
              total_token_count: 10,
            },
          };
          yield {
            candidates: [
              {
                content: { parts: [{ text: ' world!' }] },
                finish_reason: 'STOP',
                index: 0,
              },
            ],
            usage_metadata: {
              prompt_token_count: 5,
              candidates_token_count: 10,
              total_token_count: 15,
            },
          };
        },
      };

      mockGenerateContentStream.mockResolvedValue(mockStream);

      const streamPromise = model.generateContentStream('Hello');
      const stream = await streamPromise;

      const chunks = [];
      for await (const chunk of stream) {
        chunks.push(chunk);
      }

      expect(mockSpan.setAttributes).toHaveBeenCalledWith({
        'gen_ai.usage.input_tokens': 5,
        'gen_ai.usage.output_tokens': 10,
        'gen_ai.usage.total_tokens': 15,
      });
    });

    it('should handle malformed streaming chunks', async () => {
      const WrappedGoogle = wrapGoogle(GoogleClass);
      const instance = new WrappedGoogle();
      const model = instance.getGenerativeModel({ model: 'gemini-pro' });

      const mockStream = {
        async *[Symbol.asyncIterator]() {
          yield null;
          yield undefined;
          yield {};
          yield { candidates: null };
          yield { candidates: [] };
          yield { candidates: [null] };
          yield { candidates: [{ content: { parts: [{ text: 'Valid' }] } }] };
        },
      };

      mockGenerateContentStream.mockResolvedValue(mockStream);

      const streamPromise = model.generateContentStream('Hello');
      const stream = await streamPromise;

      const chunks = [];
      for await (const chunk of stream) {
        chunks.push(chunk);
      }

      // null and undefined chunks are skipped, so we get 5 instead of 7
      expect(chunks).toHaveLength(5);
      expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
        'gen_ai.system': 'gemini',
        index: 0,
        finish_reason: 'error',
        message: JSON.stringify({ role: 'model', content: 'Valid' }),
      });
    });
  });

  describe('error handling with ensureError', () => {
    it('should handle non-Error exceptions', async () => {
      const WrappedGoogle = wrapGoogle(GoogleClass);
      const instance = new WrappedGoogle();
      const model = instance.getGenerativeModel({ model: 'gemini-pro' });

      const nonErrorValue = { message: 'object error', code: 'ERR_001' };
      mockGenerateContent.mockRejectedValue(nonErrorValue);

      await expect(model.generateContent('Hello')).rejects.toThrow();

      expect(mockedEnsureError).toHaveBeenCalledWith(nonErrorValue);
      expect(mockSpan.recordException).toHaveBeenCalledWith(expect.any(Error));
    });
  });
});
