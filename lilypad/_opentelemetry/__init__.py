from contextlib import suppress

with suppress(ImportError):
    from ._opentelemetry_anthropic import AnthropicInstrumentor

with suppress(ImportError):
    from ._opentelemetry_bedrock import BedrockInstrumentor

with suppress(ImportError):
    from ._opentelemetry_google_genai import GoogleGenAiSdkInstrumentor

with suppress(ImportError):
    from ._opentelemetry_google_generative_ai import GoogleGenerativeAIInstrumentor

with suppress(ImportError):
    from ._opentelemetry_mistral import MistralInstrumentor

with suppress(ImportError):
    from ._opentelemetry_openai import OpenAIInstrumentor

with suppress(ImportError):
    from ._opentelemetry_outlines import OutlinesInstrumentor

with suppress(ImportError):
    from ._opentelemetry_vertex import VertexAIInstrumentor

__all__ = [
    "AnthropicInstrumentor",
    "BedrockInstrumentor",
    "GoogleGenerativeAIInstrumentor",
    "MistralInstrumentor",
    "OpenAIInstrumentor",
    "OutlinesInstrumentor",
    "VertexAIInstrumentor",
]
