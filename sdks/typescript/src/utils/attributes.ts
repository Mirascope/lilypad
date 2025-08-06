export const GEN_AI_ATTRIBUTES = {
  GEN_AI_OPERATION_NAME: 'gen_ai.operation.name',
  GEN_AI_REQUEST_MODEL: 'gen_ai.request.model',
  GEN_AI_REQUEST_TEMPERATURE: 'gen_ai.request.temperature',
  GEN_AI_REQUEST_TOP_P: 'gen_ai.request.top_p',
  GEN_AI_REQUEST_MAX_TOKENS: 'gen_ai.request.max_tokens',
  GEN_AI_REQUEST_PRESENCE_PENALTY: 'gen_ai.request.presence_penalty',
  GEN_AI_REQUEST_FREQUENCY_PENALTY: 'gen_ai.request.frequency_penalty',
  GEN_AI_RESPONSE_FINISH_REASONS: 'gen_ai.response.finish_reasons',
  GEN_AI_USAGE_INPUT_TOKENS: 'gen_ai.usage.input_tokens',
  GEN_AI_USAGE_OUTPUT_TOKENS: 'gen_ai.usage.output_tokens',
  GEN_AI_SYSTEM: 'gen_ai.system',
  GEN_AI_OPENAI_REQUEST_RESPONSE_FORMAT:
    'gen_ai.openai.request.response_format',
  GEN_AI_OPENAI_REQUEST_SEED: 'gen_ai.openai.request.seed',
  GEN_AI_OPENAI_RESPONSE_SERVICE_TIER: 'gen_ai.openai.response.service_tier',
} as const;

export const SERVER_ATTRIBUTES = {
  SERVER_ADDRESS: 'server.address',
  SERVER_PORT: 'server.port',
} as const;

export const ERROR_ATTRIBUTES = {
  ERROR_TYPE: 'error.type',
} as const;
