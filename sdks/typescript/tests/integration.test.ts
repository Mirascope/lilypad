import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

describe('Integration tests', () => {
  let consoleLogSpy: any;
  let consoleDebugSpy: any;
  let consoleErrorSpy: any;

  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();

    consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    consoleDebugSpy = vi.spyOn(console, 'debug').mockImplementation(() => {});
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleLogSpy.mockRestore();
    consoleDebugSpy.mockRestore();
    consoleErrorSpy.mockRestore();
  });

  it('should trace OpenAI completion with console export in debug mode', async () => {
    const { configure, instrument_openai } = await import('../src/index');

    configure({ mode: 'debug' });

    const mockClient = {
      chat: {
        completions: {
          create: vi.fn().mockResolvedValue({
            id: 'chatcmpl-123',
            model: 'gpt-4',
            choices: [
              {
                message: {
                  role: 'assistant',
                  content: 'Hello! How can I help you?',
                },
                finish_reason: 'stop',
              },
            ],
            usage: {
              prompt_tokens: 10,
              completion_tokens: 15,
              total_tokens: 25,
            },
          }),
        },
      },
      baseURL: 'https://api.openai.com',
    };

    instrument_openai(mockClient);

    const response = await mockClient.chat.completions.create({
      model: 'gpt-4',
      messages: [{ role: 'user', content: 'Hello!' }],
      temperature: 0.7,
    });

    expect(response).toBeDefined();
    expect(response.choices[0].message.content).toBe(
      'Hello! How can I help you?'
    );
    expect(consoleDebugSpy).toHaveBeenCalledWith(
      'Configuring lilypad SDK in debug mode.'
    );
  });

  it('should handle streaming responses', async () => {
    const { configure, instrument_openai } = await import('../src/index');

    configure({ mode: 'debug' });

    const chunks = [
      { choices: [{ delta: { content: 'Hello' } }] },
      { choices: [{ delta: { content: ' there' } }] },
      { choices: [{ delta: { content: '!', finish_reason: 'stop' } }] },
      { usage: { prompt_tokens: 5, completion_tokens: 3, total_tokens: 8 } },
    ];

    const mockStream = {
      async *[Symbol.asyncIterator]() {
        for (const chunk of chunks) {
          yield chunk;
        }
      },
    };

    const mockClient = {
      chat: {
        completions: {
          create: vi.fn().mockResolvedValue(mockStream),
        },
      },
    };

    instrument_openai(mockClient);

    const stream = await mockClient.chat.completions.create({
      model: 'gpt-4',
      messages: [{ role: 'user', content: 'Hi' }],
      stream: true,
    });

    const collectedChunks = [];
    for await (const chunk of stream) {
      collectedChunks.push(chunk);
    }

    expect(collectedChunks).toHaveLength(4);
    expect(collectedChunks[0].choices[0].delta.content).toBe('Hello');
  });

  it('should handle errors gracefully', async () => {
    const { configure, instrument_openai } = await import('../src/index');

    configure({ mode: 'debug' });

    const mockClient = {
      chat: {
        completions: {
          create: vi.fn().mockRejectedValue(new Error('API Error')),
        },
      },
    };

    instrument_openai(mockClient);

    await expect(
      mockClient.chat.completions.create({
        model: 'gpt-4',
        messages: [{ role: 'user', content: 'Hello' }],
      })
    ).rejects.toThrow('API Error');
  });

  it('should work without debug mode', async () => {
    const { configure, instrument_openai } = await import('../src/index');

    configure();

    const mockClient = {
      chat: {
        completions: {
          create: vi.fn().mockResolvedValue({
            id: 'chatcmpl-123',
            model: 'gpt-4',
            choices: [
              {
                message: { role: 'assistant', content: 'Hello!' },
                finish_reason: 'stop',
              },
            ],
          }),
        },
      },
    };

    instrument_openai(mockClient);

    const response = await mockClient.chat.completions.create({
      model: 'gpt-4',
      messages: [{ role: 'user', content: 'Hello!' }],
    });

    expect(response).toBeDefined();
    expect(consoleDebugSpy).not.toHaveBeenCalled();
  });

  it('should handle multiple sequential requests', async () => {
    const { configure, instrument_openai } = await import('../src/index');

    configure({ mode: 'debug' });

    const mockClient = {
      chat: {
        completions: {
          create: vi
            .fn()
            .mockResolvedValueOnce({
              id: 'chatcmpl-1',
              model: 'gpt-3.5-turbo',
              choices: [
                {
                  message: { role: 'assistant', content: 'First response' },
                  finish_reason: 'stop',
                },
              ],
            })
            .mockResolvedValueOnce({
              id: 'chatcmpl-2',
              model: 'gpt-4',
              choices: [
                {
                  message: { role: 'assistant', content: 'Second response' },
                  finish_reason: 'stop',
                },
              ],
            }),
        },
      },
    };

    instrument_openai(mockClient);

    const response1 = await mockClient.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: [{ role: 'user', content: 'First question' }],
    });

    const response2 = await mockClient.chat.completions.create({
      model: 'gpt-4',
      messages: [{ role: 'user', content: 'Second question' }],
    });

    expect(response1.choices[0].message.content).toBe('First response');
    expect(response2.choices[0].message.content).toBe('Second response');
  });

  it('should handle openrouter configuration', async () => {
    const { configure, instrument_openai } = await import('../src/index');

    configure({ mode: 'debug' });

    const mockClient = {
      chat: {
        completions: {
          create: vi.fn().mockResolvedValue({
            id: 'or-123',
            model: 'gpt-4',
            choices: [
              {
                message: { role: 'assistant', content: 'OpenRouter response' },
                finish_reason: 'stop',
              },
            ],
          }),
        },
      },
      baseURL: 'https://openrouter.ai/api/v1',
    };

    instrument_openai(mockClient);

    const result = await mockClient.chat.completions.create({
      model: 'gpt-4',
      messages: [{ role: 'user', content: 'Test' }],
    });

    expect(result.choices[0].message.content).toBe('OpenRouter response');
  });
});
