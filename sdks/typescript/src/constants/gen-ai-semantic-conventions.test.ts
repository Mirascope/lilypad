import { describe, it, expect } from 'vitest';
import {
  SEMATTRS_GEN_AI_SYSTEM,
  SEMATTRS_GEN_AI_OPERATION_NAME,
  SEMATTRS_GEN_AI_REQUEST_MODEL,
  SEMATTRS_GEN_AI_REQUEST_TEMPERATURE,
  SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS,
  SEMATTRS_GEN_AI_REQUEST_TOP_P,
  SEMATTRS_GEN_AI_REQUEST_STOP_SEQUENCES,
  SEMATTRS_GEN_AI_REQUEST_FREQUENCY_PENALTY,
  SEMATTRS_GEN_AI_REQUEST_PRESENCE_PENALTY,
  SEMATTRS_GEN_AI_RESPONSE_ID,
  SEMATTRS_GEN_AI_RESPONSE_MODEL,
  SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS,
  SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS,
  SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS,
  SEMATTRS_GEN_AI_USAGE_TOTAL_TOKENS,
  SEMATTRS_GEN_AI_CONTENT_PROMPT,
  SEMATTRS_GEN_AI_CONTENT_COMPLETION,
  SEMATTRS_GEN_AI_CONVERSATION_ID,
  SEMATTRS_GEN_AI_MESSAGE_ROLE,
  SEMATTRS_GEN_AI_MESSAGE_CONTENT,
  FUTURE_MIGRATION_NOTE,
} from './gen-ai-semantic-conventions';

describe('GenAI Semantic Conventions', () => {
  it('should export correct system attribute', () => {
    expect(SEMATTRS_GEN_AI_SYSTEM).toBe('gen_ai.system');
  });

  it('should export correct operation name attribute', () => {
    expect(SEMATTRS_GEN_AI_OPERATION_NAME).toBe('gen_ai.operation.name');
  });

  it('should export correct request attributes', () => {
    expect(SEMATTRS_GEN_AI_REQUEST_MODEL).toBe('gen_ai.request.model');
    expect(SEMATTRS_GEN_AI_REQUEST_TEMPERATURE).toBe('gen_ai.request.temperature');
    expect(SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS).toBe('gen_ai.request.max_tokens');
    expect(SEMATTRS_GEN_AI_REQUEST_TOP_P).toBe('gen_ai.request.top_p');
    expect(SEMATTRS_GEN_AI_REQUEST_STOP_SEQUENCES).toBe('gen_ai.request.stop_sequences');
    expect(SEMATTRS_GEN_AI_REQUEST_FREQUENCY_PENALTY).toBe('gen_ai.request.frequency_penalty');
    expect(SEMATTRS_GEN_AI_REQUEST_PRESENCE_PENALTY).toBe('gen_ai.request.presence_penalty');
  });

  it('should export correct response attributes', () => {
    expect(SEMATTRS_GEN_AI_RESPONSE_ID).toBe('gen_ai.response.id');
    expect(SEMATTRS_GEN_AI_RESPONSE_MODEL).toBe('gen_ai.response.model');
    expect(SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS).toBe('gen_ai.response.finish_reasons');
  });

  it('should export correct usage attributes', () => {
    expect(SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS).toBe('gen_ai.usage.input_tokens');
    expect(SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS).toBe('gen_ai.usage.output_tokens');
    expect(SEMATTRS_GEN_AI_USAGE_TOTAL_TOKENS).toBe('gen_ai.usage.total_tokens');
  });

  it('should export correct content attributes', () => {
    expect(SEMATTRS_GEN_AI_CONTENT_PROMPT).toBe('gen_ai.content.prompt');
    expect(SEMATTRS_GEN_AI_CONTENT_COMPLETION).toBe('gen_ai.content.completion');
  });

  it('should export correct message attributes', () => {
    expect(SEMATTRS_GEN_AI_MESSAGE_ROLE).toBe('gen_ai.message.role');
    expect(SEMATTRS_GEN_AI_MESSAGE_CONTENT).toBe('gen_ai.message.content');
  });

  it('should export conversation ID attribute', () => {
    expect(SEMATTRS_GEN_AI_CONVERSATION_ID).toBe('gen_ai.conversation.id');
  });

  it('should export migration note', () => {
    expect(FUTURE_MIGRATION_NOTE).toContain('@opentelemetry/semantic-conventions');
  });

  it('should export all expected attributes', () => {
    // Ensure all exports are strings
    const allExports = [
      SEMATTRS_GEN_AI_SYSTEM,
      SEMATTRS_GEN_AI_OPERATION_NAME,
      SEMATTRS_GEN_AI_REQUEST_MODEL,
      SEMATTRS_GEN_AI_REQUEST_TEMPERATURE,
      SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS,
      SEMATTRS_GEN_AI_REQUEST_TOP_P,
      SEMATTRS_GEN_AI_REQUEST_STOP_SEQUENCES,
      SEMATTRS_GEN_AI_REQUEST_FREQUENCY_PENALTY,
      SEMATTRS_GEN_AI_REQUEST_PRESENCE_PENALTY,
      SEMATTRS_GEN_AI_RESPONSE_ID,
      SEMATTRS_GEN_AI_RESPONSE_MODEL,
      SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS,
      SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS,
      SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS,
      SEMATTRS_GEN_AI_USAGE_TOTAL_TOKENS,
      SEMATTRS_GEN_AI_CONTENT_PROMPT,
      SEMATTRS_GEN_AI_CONTENT_COMPLETION,
      SEMATTRS_GEN_AI_CONVERSATION_ID,
      SEMATTRS_GEN_AI_MESSAGE_ROLE,
      SEMATTRS_GEN_AI_MESSAGE_CONTENT,
    ];

    allExports.forEach((attr) => {
      expect(typeof attr).toBe('string');
      expect(attr).toMatch(/^gen_ai\./);
    });
  });
});
