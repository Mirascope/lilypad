import type { Span } from '@opentelemetry/api';
import { GEN_AI_ATTRIBUTES } from './attributes';

export interface StreamChunk {
  choices?: Array<{
    delta?: {
      content?: string;
      role?: string;
    };
    finish_reason?: string | null;
  }>;
  usage?: {
    prompt_tokens?: number;
    completion_tokens?: number;
    total_tokens?: number;
  };
}

export class StreamWrapper<T extends StreamChunk> implements AsyncIterable<T> {
  private content = '';
  private finishReason: string | null = null;
  private usage: StreamChunk['usage'] = undefined;

  constructor(
    private span: Span,
    private stream: AsyncIterable<T>
  ) {}

  async *[Symbol.asyncIterator](): AsyncIterator<T> {
    try {
      for await (const chunk of this.stream) {
        if (chunk.choices && chunk.choices.length > 0) {
          const choice = chunk.choices[0];
          if (choice.delta?.content) {
            this.content += choice.delta.content;
          }
          if (choice.finish_reason) {
            this.finishReason = choice.finish_reason;
          }
        }
        if (chunk.usage) {
          this.usage = chunk.usage;
        }
        yield chunk;
      }
    } finally {
      this.recordFinalAttributes();
      this.span.end();
    }
  }

  private recordFinalAttributes(): void {
    if (this.content) {
      this.span.addEvent('gen_ai.choice', {
        'gen_ai.system': 'openai',
        index: 0,
        finish_reason: this.finishReason || 'unknown',
        message: JSON.stringify({
          role: 'assistant',
          content: this.content,
        }),
      });
    }

    if (this.finishReason) {
      this.span.setAttribute(GEN_AI_ATTRIBUTES.GEN_AI_RESPONSE_FINISH_REASONS, [
        this.finishReason,
      ]);
    }

    if (this.usage) {
      this.span.setAttributes({
        [GEN_AI_ATTRIBUTES.GEN_AI_USAGE_INPUT_TOKENS]: this.usage.prompt_tokens,
        [GEN_AI_ATTRIBUTES.GEN_AI_USAGE_OUTPUT_TOKENS]:
          this.usage.completion_tokens,
        'gen_ai.usage.total_tokens': this.usage.total_tokens,
      });
    }
  }
}
