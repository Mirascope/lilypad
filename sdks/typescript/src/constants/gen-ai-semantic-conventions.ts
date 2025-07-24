/**
 * GenAI Semantic Conventions
 *
 * These constants match the OpenTelemetry Semantic Conventions for GenAI/LLM operations.
 * Once these are included in @opentelemetry/semantic-conventions package, we can migrate
 * to using the official exports.
 *
 * Based on: https://github.com/open-telemetry/semantic-conventions/blob/main/docs/gen-ai/
 * Status: Development (as of 2024-01)
 */

// System and operation attributes
export const SEMATTRS_GEN_AI_SYSTEM = 'gen_ai.system';
export const SEMATTRS_GEN_AI_OPERATION_NAME = 'gen_ai.operation.name';

// Request attributes
export const SEMATTRS_GEN_AI_REQUEST_MODEL = 'gen_ai.request.model';
export const SEMATTRS_GEN_AI_REQUEST_TEMPERATURE = 'gen_ai.request.temperature';
export const SEMATTRS_GEN_AI_REQUEST_MAX_TOKENS = 'gen_ai.request.max_tokens';
export const SEMATTRS_GEN_AI_REQUEST_TOP_P = 'gen_ai.request.top_p';
export const SEMATTRS_GEN_AI_REQUEST_FREQUENCY_PENALTY = 'gen_ai.request.frequency_penalty';
export const SEMATTRS_GEN_AI_REQUEST_PRESENCE_PENALTY = 'gen_ai.request.presence_penalty';
export const SEMATTRS_GEN_AI_REQUEST_STOP_SEQUENCES = 'gen_ai.request.stop_sequences';

// Response attributes
export const SEMATTRS_GEN_AI_RESPONSE_MODEL = 'gen_ai.response.model';
export const SEMATTRS_GEN_AI_RESPONSE_FINISH_REASONS = 'gen_ai.response.finish_reasons';
export const SEMATTRS_GEN_AI_RESPONSE_ID = 'gen_ai.response.id';

// Usage attributes
export const SEMATTRS_GEN_AI_USAGE_INPUT_TOKENS = 'gen_ai.usage.input_tokens';
export const SEMATTRS_GEN_AI_USAGE_OUTPUT_TOKENS = 'gen_ai.usage.output_tokens';
export const SEMATTRS_GEN_AI_USAGE_TOTAL_TOKENS = 'gen_ai.usage.total_tokens';

// Content attributes
export const SEMATTRS_GEN_AI_CONTENT_PROMPT = 'gen_ai.content.prompt';
export const SEMATTRS_GEN_AI_CONTENT_COMPLETION = 'gen_ai.content.completion';

// Additional attributes
export const SEMATTRS_GEN_AI_CONVERSATION_ID = 'gen_ai.conversation.id';
export const SEMATTRS_GEN_AI_MESSAGE_ROLE = 'gen_ai.message.role';
export const SEMATTRS_GEN_AI_MESSAGE_CONTENT = 'gen_ai.message.content';

// Future migration helper
export const FUTURE_MIGRATION_NOTE = `
When @opentelemetry/semantic-conventions includes GenAI constants, replace imports:

FROM:
import { SEMATTRS_GEN_AI_REQUEST_MODEL } from '../constants/gen-ai-semantic-conventions';

TO:
import { SEMATTRS_GEN_AI_REQUEST_MODEL } from '@opentelemetry/semantic-conventions';
`;
