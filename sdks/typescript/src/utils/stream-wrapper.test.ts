import { describe, it, expect, vi, beforeEach } from 'vitest';
import { StreamWrapper } from './stream-wrapper';
import { GEN_AI_ATTRIBUTES } from './attributes';

describe('StreamWrapper', () => {
  let mockSpan: any;
  let mockStream: any;

  beforeEach(() => {
    vi.clearAllMocks();
    mockSpan = {
      addEvent: vi.fn(),
      setAttribute: vi.fn(),
      setAttributes: vi.fn(),
      end: vi.fn(),
    };
  });

  function createMockStream(chunks: any[]) {
    return {
      async *[Symbol.asyncIterator]() {
        for (const chunk of chunks) {
          yield chunk;
        }
      },
    };
  }

  it('should wrap and iterate through stream chunks', async () => {
    const chunks = [
      {
        choices: [{ delta: { content: 'Hello' } }],
      },
      {
        choices: [{ delta: { content: ' world' } }],
      },
      {
        choices: [{ delta: { content: '!' }, finish_reason: 'stop' }],
      },
    ];

    mockStream = createMockStream(chunks);
    const wrapper = new StreamWrapper(mockSpan, mockStream);

    const receivedChunks = [];
    for await (const chunk of wrapper) {
      receivedChunks.push(chunk);
    }

    expect(receivedChunks).toEqual(chunks);
    expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
      'gen_ai.system': 'openai',
      index: 0,
      finish_reason: 'stop',
      message: JSON.stringify({
        role: 'assistant',
        content: 'Hello world!',
      }),
    });
    expect(mockSpan.setAttribute).toHaveBeenCalledWith(
      GEN_AI_ATTRIBUTES.GEN_AI_RESPONSE_FINISH_REASONS,
      ['stop']
    );
    expect(mockSpan.end).toHaveBeenCalled();
  });

  it('should handle stream with usage data', async () => {
    const chunks = [
      {
        choices: [{ delta: { content: 'Test' } }],
      },
      {
        usage: {
          prompt_tokens: 10,
          completion_tokens: 5,
          total_tokens: 15,
        },
      },
    ];

    mockStream = createMockStream(chunks);
    const wrapper = new StreamWrapper(mockSpan, mockStream);

    const receivedChunks = [];
    for await (const chunk of wrapper) {
      receivedChunks.push(chunk);
    }

    expect(mockSpan.setAttributes).toHaveBeenCalledWith({
      [GEN_AI_ATTRIBUTES.GEN_AI_USAGE_INPUT_TOKENS]: 10,
      [GEN_AI_ATTRIBUTES.GEN_AI_USAGE_OUTPUT_TOKENS]: 5,
      'gen_ai.usage.total_tokens': 15,
    });
  });

  it('should handle empty stream', async () => {
    mockStream = createMockStream([]);
    const wrapper = new StreamWrapper(mockSpan, mockStream);

    const receivedChunks = [];
    for await (const chunk of wrapper) {
      receivedChunks.push(chunk);
    }

    expect(receivedChunks).toEqual([]);
    expect(mockSpan.addEvent).not.toHaveBeenCalled();
    expect(mockSpan.setAttribute).not.toHaveBeenCalled();
    expect(mockSpan.setAttributes).not.toHaveBeenCalled();
    expect(mockSpan.end).toHaveBeenCalled();
  });

  it('should handle chunks without choices', async () => {
    const chunks = [
      { other: 'data' },
      {
        usage: {
          prompt_tokens: 10,
          completion_tokens: 5,
          total_tokens: 15,
        },
      },
    ];

    mockStream = createMockStream(chunks);
    const wrapper = new StreamWrapper(mockSpan, mockStream);

    const receivedChunks = [];
    for await (const chunk of wrapper) {
      receivedChunks.push(chunk);
    }

    expect(receivedChunks).toEqual(chunks);
    expect(mockSpan.addEvent).not.toHaveBeenCalled();
    expect(mockSpan.setAttributes).toHaveBeenCalled();
  });

  it('should handle chunks with empty choices array', async () => {
    const chunks = [
      { choices: [] },
      { choices: [{ delta: { content: 'Test' } }] },
    ];

    mockStream = createMockStream(chunks);
    const wrapper = new StreamWrapper(mockSpan, mockStream);

    const receivedChunks = [];
    for await (const chunk of wrapper) {
      receivedChunks.push(chunk);
    }

    expect(receivedChunks).toEqual(chunks);
    expect(mockSpan.addEvent).toHaveBeenCalledOnce();
  });

  it('should handle chunks with missing delta', async () => {
    const chunks = [
      { choices: [{}] },
      { choices: [{ delta: { content: 'Test' } }] },
    ];

    mockStream = createMockStream(chunks);
    const wrapper = new StreamWrapper(mockSpan, mockStream);

    const receivedChunks = [];
    for await (const chunk of wrapper) {
      receivedChunks.push(chunk);
    }

    expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
      'gen_ai.system': 'openai',
      index: 0,
      finish_reason: 'unknown',
      message: JSON.stringify({
        role: 'assistant',
        content: 'Test',
      }),
    });
  });

  it('should handle finish_reason without content', async () => {
    const chunks = [{ choices: [{ finish_reason: 'stop' }] }];

    mockStream = createMockStream(chunks);
    const wrapper = new StreamWrapper(mockSpan, mockStream);

    const receivedChunks = [];
    for await (const chunk of wrapper) {
      receivedChunks.push(chunk);
    }

    expect(mockSpan.setAttribute).toHaveBeenCalledWith(
      GEN_AI_ATTRIBUTES.GEN_AI_RESPONSE_FINISH_REASONS,
      ['stop']
    );
    expect(mockSpan.addEvent).not.toHaveBeenCalled();
  });

  it('should handle finish_reason with null value', async () => {
    const chunks = [
      { choices: [{ delta: { content: 'Test' }, finish_reason: null }] },
    ];

    mockStream = createMockStream(chunks);
    const wrapper = new StreamWrapper(mockSpan, mockStream);

    const receivedChunks = [];
    for await (const chunk of wrapper) {
      receivedChunks.push(chunk);
    }

    expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
      'gen_ai.system': 'openai',
      index: 0,
      finish_reason: 'unknown',
      message: JSON.stringify({
        role: 'assistant',
        content: 'Test',
      }),
    });
    expect(mockSpan.setAttribute).not.toHaveBeenCalledWith(
      GEN_AI_ATTRIBUTES.GEN_AI_RESPONSE_FINISH_REASONS,
      expect.any(Array)
    );
  });

  it('should concatenate content from multiple chunks', async () => {
    const chunks = [
      { choices: [{ delta: { content: 'The' } }] },
      { choices: [{ delta: { content: ' quick' } }] },
      { choices: [{ delta: { content: ' brown' } }] },
      { choices: [{ delta: { content: ' fox' }, finish_reason: 'stop' }] },
    ];

    mockStream = createMockStream(chunks);
    const wrapper = new StreamWrapper(mockSpan, mockStream);

    const receivedChunks = [];
    for await (const chunk of wrapper) {
      receivedChunks.push(chunk);
    }

    expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
      'gen_ai.system': 'openai',
      index: 0,
      finish_reason: 'stop',
      message: JSON.stringify({
        role: 'assistant',
        content: 'The quick brown fox',
      }),
    });
  });

  it('should handle stream errors', async () => {
    const error = new Error('Stream error');
    mockStream = {
      async *[Symbol.asyncIterator]() {
        yield { choices: [{ delta: { content: 'Hello' } }] };
        throw error;
      },
    };

    const wrapper = new StreamWrapper(mockSpan, mockStream);

    const receivedChunks = [];
    await expect(async () => {
      for await (const chunk of wrapper) {
        receivedChunks.push(chunk);
      }
    }).rejects.toThrow('Stream error');

    expect(receivedChunks).toHaveLength(1);
    expect(mockSpan.addEvent).toHaveBeenCalled();
    expect(mockSpan.end).toHaveBeenCalled();
  });

  it('should call end even when break is used', async () => {
    const chunks = [
      { choices: [{ delta: { content: 'Hello' } }] },
      { choices: [{ delta: { content: ' world' } }] },
      { choices: [{ delta: { content: '!' } }] },
    ];

    mockStream = createMockStream(chunks);
    const wrapper = new StreamWrapper(mockSpan, mockStream);

    const receivedChunks = [];
    for await (const chunk of wrapper) {
      receivedChunks.push(chunk);
      if (receivedChunks.length === 2) break;
    }

    expect(receivedChunks).toHaveLength(2);
    expect(mockSpan.end).toHaveBeenCalled();
  });

  it('should handle multiple choices in a single chunk', async () => {
    const chunks = [
      {
        choices: [
          { delta: { content: 'First' } },
          { delta: { content: 'Second' } },
        ],
      },
    ];

    mockStream = createMockStream(chunks);
    const wrapper = new StreamWrapper(mockSpan, mockStream);

    const receivedChunks = [];
    for await (const chunk of wrapper) {
      receivedChunks.push(chunk);
    }

    expect(mockSpan.addEvent).toHaveBeenCalledWith('gen_ai.choice', {
      'gen_ai.system': 'openai',
      index: 0,
      finish_reason: 'unknown',
      message: JSON.stringify({
        role: 'assistant',
        content: 'First',
      }),
    });
  });

  it('should handle usage with missing fields', async () => {
    const chunks = [
      {
        usage: {
          prompt_tokens: 10,
        },
      },
    ];

    mockStream = createMockStream(chunks);
    const wrapper = new StreamWrapper(mockSpan, mockStream);

    for await (const _chunk of wrapper) {
      // Consume the stream
    }

    expect(mockSpan.setAttributes).toHaveBeenCalledWith({
      [GEN_AI_ATTRIBUTES.GEN_AI_USAGE_INPUT_TOKENS]: 10,
      [GEN_AI_ATTRIBUTES.GEN_AI_USAGE_OUTPUT_TOKENS]: undefined,
      'gen_ai.usage.total_tokens': undefined,
    });
  });
});
