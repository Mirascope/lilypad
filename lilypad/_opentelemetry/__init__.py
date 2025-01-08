from contextlib import suppress

with suppress(ImportError):
    from ._opentelemetry_anthropic import AnthropicInstrumentor
    from ._opentelemetry_bedrock import BedrockInstrumentor
    from ._opentelemetry_google_generative_ai import GoogleGenerativeAIInstrumentor
    from ._opentelemetry_openai import OpenAIInstrumentor
    from ._opentelemetry_outlines import OutlinesInstrumentor

__all__ = [
    "AnthropicInstrumentor",
    "BedrockInstrumentor",
    "GoogleGenerativeAIInstrumentor",
    "OpenAIInstrumentor",
    "OutlinesInstrumentor",
]
