"""Tests for Google GenAI instrumentation."""

import os
import base64
import inspect
from io import BytesIO
from typing import TypedDict
from unittest.mock import Mock, patch
from importlib.metadata import PackageNotFoundError

import pytest
from PIL import Image
from wrapt import FunctionWrapper
from dotenv import load_dotenv
from pydantic import BaseModel
from google import genai
from google.genai.errors import ClientError, ServerError
from google.genai.models import Models, AsyncModels
from google.genai.types import (
    GenerateContentResponse,
    GenerateContentConfig,
    Tool,
    FunctionDeclaration,
    Part,
    Content,
    Blob,
    GenerateContentConfigDict,
    ContentDict,
    PartDict,
    Schema,
    Type,
    FunctionCallDict,
    FunctionResponseDict,
    ToolDict,
    FunctionDeclarationDict,
    SchemaDict,
    BlobDict,
    ContentListUnionDict,
)
from inline_snapshot import snapshot
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from lilypad._internal.otel.google.instrument import instrument_google

from ..test_utils import extract_span_data


@pytest.fixture
def google_api_key() -> str:
    """Get Google API key from environment or return dummy key."""
    load_dotenv()
    return os.getenv("GOOGLE_API_KEY", "test-api-key")


@pytest.fixture
def client(google_api_key: str) -> Models:
    """Create an instrumented Google GenAI models client."""
    os.environ["GOOGLE_API_KEY"] = google_api_key
    client = genai.Client(api_key=google_api_key)
    models = client.models
    instrument_google(models)
    return models


@pytest.fixture
def async_client(google_api_key: str) -> AsyncModels:
    """Create an instrumented Google GenAI async models client."""
    os.environ["GOOGLE_API_KEY"] = google_api_key
    client = genai.Client(api_key=google_api_key)
    models = client.aio.models
    instrument_google(models)
    return models


@pytest.mark.vcr()
def test_sync_generate_content_simple(
    client: Models, span_exporter: InMemorySpanExporter
) -> None:
    """Test basic content generation with span verification."""
    response = client.generate_content(
        model="gemini-2.0-flash-exp",
        contents="Say hello back to me",
    )

    assert isinstance(response, GenerateContentResponse)
    assert response.text

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gemini-2.0-flash-exp",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gemini-2.0-flash-exp",
                "gen_ai.system": "google_genai",
                "gen_ai.response.model": "gemini-2.0-flash-exp",
                "gen_ai.response.id": "DLSeaLT9Esi9698PtLOnoA4",
                "gen_ai.response.finish_reasons": ("STOP",),
                "gen_ai.usage.input_tokens": 5,
                "gen_ai.usage.output_tokens": 5,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.content": "Say hello back to me",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.choice.index": 0,
                        "gen_ai.choice.finish_reason": "STOP",
                        "gen_ai.choice.message": '{"role": "model", "content": "Hello there! \\ud83d\\udc4b\\n"}',
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
@pytest.mark.asyncio
async def test_async_generate_content_simple(
    async_client: AsyncModels, span_exporter: InMemorySpanExporter
) -> None:
    """Test async content generation with span verification."""
    response = await async_client.generate_content(
        model="gemini-2.0-flash-exp",
        contents="Say hello back to me",
    )

    assert isinstance(response, GenerateContentResponse)
    assert response.text

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gemini-2.0-flash-exp",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gemini-2.0-flash-exp",
                "gen_ai.system": "google_genai",
                "gen_ai.response.model": "gemini-2.0-flash-exp",
                "gen_ai.response.id": "_9eiaNvzCfKonvgPm4qiIQ",
                "gen_ai.response.finish_reasons": ("STOP",),
                "gen_ai.usage.input_tokens": 5,
                "gen_ai.usage.output_tokens": 3,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.content": "Say hello back to me",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.choice.index": 0,
                        "gen_ai.choice.finish_reason": "STOP",
                        "gen_ai.choice.message": '{"role": "model", "content": "Hello!\\n"}',
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_generate_content_with_system(
    client: Models, span_exporter: InMemorySpanExporter
) -> None:
    """Test content generation with system instruction and span verification."""
    response = client.generate_content(
        model="gemini-2.0-flash-exp",
        contents="What is the capital of France?",
        config=GenerateContentConfig(
            system_instruction="You are a helpful assistant who speaks like a pirate.",
            temperature=0.7,
            max_output_tokens=100,
        ),
    )

    assert isinstance(response, GenerateContentResponse)
    assert response.text

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gemini-2.0-flash-exp",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gemini-2.0-flash-exp",
                "gen_ai.request.temperature": 0.7,
                "gen_ai.request.max_tokens": 100,
                "gen_ai.system": "google_genai",
                "gen_ai.response.model": "gemini-2.0-flash-exp",
                "gen_ai.response.id": "QrSeaP_PDZ3envgP8ZXlqAs",
                "gen_ai.response.finish_reasons": ("STOP",),
                "gen_ai.usage.input_tokens": 18,
                "gen_ai.usage.output_tokens": 27,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.system.message",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.content": "You are a helpful assistant who speaks like a pirate.",
                    },
                },
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.content": "What is the capital of France?",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.choice.index": 0,
                        "gen_ai.choice.finish_reason": "STOP",
                        "gen_ai.choice.message": '{"role": "model", "content": "Ahoy there, matey! The capital o\' France be Paris, a city o\' lights an\' romance, aye!\\n"}',
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_generate_content_with_tools(
    client: Models, span_exporter: InMemorySpanExporter
) -> None:
    """Test content generation with tools and span verification."""
    response = client.generate_content(
        model="gemini-2.0-flash-exp",
        contents="What's the weather in Tokyo today?",
        config=GenerateContentConfig(
            tools=[
                Tool(
                    function_declarations=[
                        FunctionDeclaration(
                            name="get_weather",
                            description="Get the weather for a location",
                            parameters=Schema(
                                type=Type.OBJECT,
                                properties={
                                    "location": Schema(
                                        type=Type.STRING, description="City and country"
                                    ),
                                    "units": Schema(
                                        type=Type.STRING,
                                        enum=["celsius", "fahrenheit"],
                                        description="Temperature units",
                                    ),
                                },
                                required=["location", "units"],
                            ),
                        )
                    ]
                )
            ]
        ),
    )

    assert isinstance(response, GenerateContentResponse)
    if response.candidates:
        first_candidate = response.candidates[0]
        if first_candidate.content and first_candidate.content.parts:
            assert any(
                hasattr(part, "function_call") for part in first_candidate.content.parts
            )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gemini-2.0-flash-exp",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gemini-2.0-flash-exp",
                "gen_ai.system": "google_genai",
                "gen_ai.request.functions": ("get_weather",),
                "gen_ai.response.model": "gemini-2.0-flash-exp",
                "gen_ai.response.id": "Q7SeaJ6WAci9698PtLOnoA4",
                "gen_ai.response.finish_reasons": ("STOP",),
                "gen_ai.usage.input_tokens": 34,
                "gen_ai.usage.output_tokens": 10,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.content": "What's the weather in Tokyo today?",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.choice.index": 0,
                        "gen_ai.choice.finish_reason": "STOP",
                        "gen_ai.choice.message": '{"role": "model", "tool_calls": [{"id": "tool_0", "type": "function", "function": {"name": "get_weather", "arguments": "{\\"units\\": \\"celsius\\", \\"location\\": \\"Tokyo, Japan\\"}"}}]}',
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_multi_turn_conversation(
    client: Models, span_exporter: InMemorySpanExporter
) -> None:
    """Test multi-turn conversation with span verification."""
    response = client.generate_content(
        model="gemini-2.0-flash-exp",
        contents=[
            {"role": "user", "parts": [{"text": "What's 2+2?"}]},
            {"role": "model", "parts": [{"text": "2 + 2 = 4"}]},
            {"role": "user", "parts": [{"text": "And what's 3+3?"}]},
        ],
    )

    assert isinstance(response, GenerateContentResponse)
    assert response.text

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gemini-2.0-flash-exp",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gemini-2.0-flash-exp",
                "gen_ai.system": "google_genai",
                "gen_ai.response.model": "gemini-2.0-flash-exp",
                "gen_ai.response.id": "Q7SeaITXMv-vnvgPiPLh4Qs",
                "gen_ai.response.finish_reasons": ("STOP",),
                "gen_ai.usage.input_tokens": 24,
                "gen_ai.usage.output_tokens": 8,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.content": "What's 2+2?",
                    },
                },
                {
                    "name": "gen_ai.model.message",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.content": "2 + 2 = 4",
                    },
                },
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.content": "And what's 3+3?",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.choice.index": 0,
                        "gen_ai.choice.finish_reason": "STOP",
                        "gen_ai.choice.message": '{"role": "model", "content": "3 + 3 = 6\\n"}',
                    },
                },
            ],
        }
    )


def test_preserves_method_signatures() -> None:
    """Test that instrumentation preserves original method signatures."""
    os.environ["GOOGLE_API_KEY"] = "test"
    fresh_client = genai.Client()
    fresh_models = fresh_client.models
    original_generate_sig = inspect.signature(fresh_models.generate_content)

    instrumented_client = genai.Client()
    instrumented_models = instrumented_client.models
    instrument_google(instrumented_models)

    assert (
        inspect.signature(instrumented_models.generate_content) == original_generate_sig
    )


def test_multiple_clients_independent() -> None:
    """Test that multiple clients can be instrumented independently."""
    os.environ["GOOGLE_API_KEY"] = "test"
    client1 = genai.Client()
    models1 = client1.models
    client2 = genai.Client()
    models2 = client2.models

    assert not isinstance(models1.generate_content, FunctionWrapper)
    assert not isinstance(models2.generate_content, FunctionWrapper)

    instrument_google(models1)

    assert isinstance(models1.generate_content, FunctionWrapper)

    assert not isinstance(models2.generate_content, FunctionWrapper)


@pytest.mark.vcr()
def test_error_handling(client: Models, span_exporter: InMemorySpanExporter) -> None:
    """Test error handling and span error recording."""
    with pytest.raises(ClientError):
        client.generate_content(
            model="invalid-model-name",
            contents="Hello",
        )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat invalid-model-name",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "invalid-model-name",
                "gen_ai.system": "google_genai",
                "error.type": "ClientError",
            },
            "status": {
                "status_code": "ERROR",
                "description": "400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'API key not valid. Please pass a valid API key.', 'status': 'INVALID_ARGUMENT', 'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'generativelanguage.googleapis.com'}}, {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage', 'locale': 'en-US', 'message': 'API key not valid. Please pass a valid API key.'}]}}",
            },
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.content": "Hello",
                    },
                }
            ],
        }
    )


def test_client_marked_as_instrumented() -> None:
    """Test that client is marked as instrumented after instrumentation."""
    os.environ["GOOGLE_API_KEY"] = "test"
    client = genai.Client()
    models = client.models

    assert not hasattr(models, "_lilypad_instrumented")

    instrument_google(models)

    assert hasattr(models, "_lilypad_instrumented")
    assert models._lilypad_instrumented is True  # pyright: ignore[reportAttributeAccessIssue]


def test_instrumentation_idempotent() -> None:
    """Test that instrumentation is truly idempotent."""
    os.environ["GOOGLE_API_KEY"] = "test"
    client = genai.Client()
    models = client.models

    instrument_google(models)
    first_generate = models.generate_content

    instrument_google(models)
    second_generate = models.generate_content

    assert second_generate is first_generate


def test_async_instrumentation_idempotent() -> None:
    """Test that async instrumentation is truly idempotent."""
    os.environ["GOOGLE_API_KEY"] = "test"
    client = genai.Client()
    models = client.aio.models

    instrument_google(models)
    first_generate = models.generate_content

    instrument_google(models)
    second_generate = models.generate_content

    assert second_generate is first_generate


def test_preserves_async_nature() -> None:
    """Test that async methods remain async after patching."""
    os.environ["GOOGLE_API_KEY"] = "test"
    client = genai.Client()
    models = client.aio.models

    generate_result_before = models.generate_content(model="test", contents="test")
    assert inspect.iscoroutine(generate_result_before)
    generate_result_before.close()

    instrument_google(models)

    generate_result_after = models.generate_content(model="test", contents="test")
    assert inspect.iscoroutine(generate_result_after)
    generate_result_after.close()


def test_sync_generate_content_client_error(
    span_exporter: InMemorySpanExporter,
) -> None:
    """Test sync generation with ClientError."""
    mock_models = Mock(spec=Models)

    original_generate = Mock(
        side_effect=ClientError(
            code=400,
            response_json={
                "error": {"message": "Invalid request", "status": "INVALID_ARGUMENT"}
            },
        )
    )
    mock_models.generate_content = original_generate

    instrument_google(mock_models)

    with pytest.raises(ClientError):
        mock_models.generate_content(
            model="gemini-2.0-flash-exp",
            contents="Hello",
        )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gemini-2.0-flash-exp",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gemini-2.0-flash-exp",
                "gen_ai.system": "google_genai",
                "error.type": "ClientError",
            },
            "status": {
                "status_code": "ERROR",
                "description": "400 INVALID_ARGUMENT. {'error': {'message': 'Invalid request', 'status': 'INVALID_ARGUMENT'}}",
            },
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.content": "Hello",
                    },
                }
            ],
        }
    )


@pytest.mark.asyncio
async def test_async_generate_content_server_error(
    span_exporter: InMemorySpanExporter,
) -> None:
    """Test async generation with ServerError."""
    mock_models = Mock(spec=AsyncModels)

    async def generate_error(*args, **kwargs):
        raise ServerError(
            code=500,
            response_json={
                "error": {"message": "Internal server error", "status": "INTERNAL"}
            },
        )

    original_generate = Mock(side_effect=generate_error)
    mock_models.generate_content = original_generate

    instrument_google(mock_models)

    with pytest.raises(ServerError):
        await mock_models.generate_content(
            model="gemini-2.0-flash-exp",
            contents="Hello",
        )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gemini-2.0-flash-exp",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gemini-2.0-flash-exp",
                "gen_ai.system": "google_genai",
                "error.type": "ServerError",
            },
            "status": {
                "status_code": "ERROR",
                "description": "500 INTERNAL. {'error': {'message': 'Internal server error', 'status': 'INTERNAL'}}",
            },
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.content": "Hello",
                    },
                }
            ],
        }
    )


@pytest.mark.asyncio
async def test_async_wrapping_failure_generate(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test async client when wrapping generate_content method fails."""
    mock_models = Mock(spec=AsyncModels)
    type(mock_models).generate_content = property(lambda self: Mock())

    with caplog.at_level("WARNING"):
        instrument_google(mock_models)

    assert hasattr(mock_models, "_lilypad_instrumented")
    assert mock_models._lilypad_instrumented is True
    assert "Failed to wrap generate_content: AttributeError" in caplog.text


@pytest.mark.vcr()
def test_structured_content_is_jsonified(
    client: Models, span_exporter: InMemorySpanExporter
) -> None:
    """Test that structured content is properly JSON serialized."""
    response = client.generate_content(
        model="gemini-2.0-flash-exp",
        contents={
            "parts": [
                {"text": "Reply with OK"},
            ]
        },
        config=GenerateContentConfig(max_output_tokens=5),
    )
    assert isinstance(response, GenerateContentResponse)

    spans = span_exporter.get_finished_spans()
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gemini-2.0-flash-exp",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gemini-2.0-flash-exp",
                "gen_ai.request.max_tokens": 5,
                "gen_ai.system": "google_genai",
                "gen_ai.response.model": "gemini-2.0-flash-exp",
                "gen_ai.response.id": "erSeaNu6Nfu5nvgP74K2gAo",
                "gen_ai.response.finish_reasons": ("STOP",),
                "gen_ai.usage.input_tokens": 3,
                "gen_ai.usage.output_tokens": 2,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.content": "Reply with OK",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.choice.index": 0,
                        "gen_ai.choice.finish_reason": "STOP",
                        "gen_ai.choice.message": '{"role": "model", "content": "OK\\n"}',
                    },
                },
            ],
        }
    )


def test_package_not_found_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test handling of PackageNotFoundError when determining lilypad-sdk version."""
    with patch(
        "lilypad._internal.otel.google.instrument.version",
        side_effect=PackageNotFoundError("Package lilypad-sdk not found"),
    ):
        mock_models = Mock(spec=Models)

        with caplog.at_level("DEBUG"):
            instrument_google(mock_models)

        assert hasattr(mock_models, "_lilypad_instrumented")
        assert mock_models._lilypad_instrumented is True
        assert "Could not determine lilypad-sdk version" in caplog.text
        assert isinstance(mock_models.generate_content, FunctionWrapper)


def test_sync_generate_content_api_connection_error(
    span_exporter: InMemorySpanExporter,
) -> None:
    """Test sync generation with connection error."""
    mock_models = Mock(spec=Models)

    original_generate = Mock(
        side_effect=ClientError(
            code=503,
            response_json={
                "error": {"message": "Connection failed", "status": "UNAVAILABLE"}
            },
        )
    )
    mock_models.generate_content = original_generate

    instrument_google(mock_models)

    with pytest.raises(ClientError):
        mock_models.generate_content(
            model="gemini-2.0-flash-exp",
            contents="Hello",
        )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gemini-2.0-flash-exp",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gemini-2.0-flash-exp",
                "gen_ai.system": "google_genai",
                "error.type": "ClientError",
            },
            "status": {
                "status_code": "ERROR",
                "description": "503 UNAVAILABLE. {'error': {'message': 'Connection failed', 'status': 'UNAVAILABLE'}}",
            },
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.content": "Hello",
                    },
                }
            ],
        }
    )


def test_sync_generate_content_rate_limit_error(
    span_exporter: InMemorySpanExporter,
) -> None:
    """Test sync generation with rate limit error."""
    mock_models = Mock(spec=Models)

    original_generate = Mock(
        side_effect=ClientError(
            code=429,
            response_json={
                "error": {
                    "message": "Rate limit exceeded",
                    "status": "RESOURCE_EXHAUSTED",
                }
            },
        )
    )
    mock_models.generate_content = original_generate

    instrument_google(mock_models)

    with pytest.raises(ClientError):
        mock_models.generate_content(
            model="gemini-2.0-flash-exp",
            contents="Hello",
        )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gemini-2.0-flash-exp",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gemini-2.0-flash-exp",
                "gen_ai.system": "google_genai",
                "error.type": "ClientError",
            },
            "status": {
                "status_code": "ERROR",
                "description": "429 RESOURCE_EXHAUSTED. {'error': {'message': 'Rate limit exceeded', 'status': 'RESOURCE_EXHAUSTED'}}",
            },
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.content": "Hello",
                    },
                }
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_generate_content_with_advanced_config(
    client: Models, span_exporter: InMemorySpanExporter
) -> None:
    """Test generation with advanced configuration parameters."""
    response = client.generate_content(
        model="gemini-2.0-flash-exp",
        contents="Say hello",
        config=GenerateContentConfig(
            temperature=0.9,
            top_p=0.95,
            top_k=40,
            max_output_tokens=50,
            stop_sequences=[".", "!"],
            presence_penalty=0.1,
            frequency_penalty=0.2,
        ),
    )

    assert isinstance(response, GenerateContentResponse)
    assert response.text

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gemini-2.0-flash-exp",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gemini-2.0-flash-exp",
                "gen_ai.request.temperature": 0.9,
                "gen_ai.request.top_p": 0.95,
                "gen_ai.request.top_k": 40.0,
                "gen_ai.request.max_tokens": 50,
                "gen_ai.request.stop_sequences": (".", "!"),
                "gen_ai.request.presence_penalty": 0.1,
                "gen_ai.request.frequency_penalty": 0.2,
                "gen_ai.system": "google_genai",
                "gen_ai.response.model": "gemini-2.0-flash-exp",
                "gen_ai.response.id": "irSeaPriK_-vnvgPiPLh4Qs",
                "gen_ai.response.finish_reasons": ("STOP",),
                "gen_ai.usage.input_tokens": 2,
                "gen_ai.usage.output_tokens": 1,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.content": "Say hello",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.choice.index": 0,
                        "gen_ai.choice.finish_reason": "STOP",
                        "gen_ai.choice.message": '{"role": "model", "content": "Hello"}',
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_generate_content_with_function_call_response(
    client: Models, span_exporter: InMemorySpanExporter
) -> None:
    """Test content generation with tool response handling."""
    response = client.generate_content(
        model="gemini-2.0-flash-exp",
        contents=[
            {"role": "user", "parts": [{"text": "What's the weather in Tokyo?"}]},
            {
                "role": "model",
                "parts": [
                    {
                        "function_call": {
                            "name": "get_weather",
                            "args": {"location": "Tokyo", "units": "celsius"},
                        }
                    }
                ],
            },
            {
                "role": "user",
                "parts": [
                    {
                        "function_response": {
                            "name": "get_weather",
                            "response": {"temperature": 22, "conditions": "sunny"},
                        }
                    }
                ],
            },
        ],
        config=GenerateContentConfig(
            tools=[
                Tool(
                    function_declarations=[
                        FunctionDeclaration(
                            name="get_weather",
                            description="Get the weather for a location",
                            parameters=Schema(
                                type=Type.OBJECT,
                                properties={
                                    "location": Schema(type=Type.STRING),
                                    "units": Schema(type=Type.STRING),
                                },
                                required=["location"],
                            ),
                        )
                    ]
                )
            ]
        ),
    )

    assert isinstance(response, GenerateContentResponse)
    assert response.text

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gemini-2.0-flash-exp",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gemini-2.0-flash-exp",
                "gen_ai.system": "google_genai",
                "gen_ai.request.functions": ("get_weather",),
                "gen_ai.response.model": "gemini-2.0-flash-exp",
                "gen_ai.response.id": "jbSeaO33Hci9698PtLOnoA4",
                "gen_ai.response.finish_reasons": ("STOP",),
                "gen_ai.usage.input_tokens": 38,
                "gen_ai.usage.output_tokens": 17,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.content": "What's the weather in Tokyo?",
                    },
                },
                {
                    "name": "gen_ai.model.message",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.tool_calls": '[{"id": "tool_0", "type": "function", "function": {"name": "get_weather", "arguments": "{\\"location\\": \\"Tokyo\\", \\"units\\": \\"celsius\\"}"}}]',
                    },
                },
                {
                    "name": "gen_ai.user.message",
                    "attributes": {"gen_ai.system": "google_genai"},
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.choice.index": 0,
                        "gen_ai.choice.finish_reason": "STOP",
                        "gen_ai.choice.message": '{"role": "model", "content": "The weather in Tokyo is sunny with a temperature of 22 degrees Celsius.\\n"}',
                    },
                },
            ],
        }
    )


class WeatherToolPydantic(BaseModel):
    """Pydantic model for weather tool."""

    location: str
    units: str = "celsius"


class WeatherToolTypedDict(TypedDict):
    """TypedDict for weather tool."""

    location: str
    units: str


@pytest.mark.vcr()
def test_sync_generate_content_with_typeddict_tool(
    client: Models, span_exporter: InMemorySpanExporter
) -> None:
    """Test generation with TypedDict-based tool."""
    weather_tool_typed: WeatherToolTypedDict = {
        "location": "London",
        "units": "fahrenheit",
    }

    response = client.generate_content(
        model="gemini-2.0-flash-exp",
        contents=f"The weather in {weather_tool_typed['location']} is 65 degrees {weather_tool_typed['units']}. Summarize this.",
    )

    assert isinstance(response, GenerateContentResponse)
    assert response.text

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gemini-2.0-flash-exp",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gemini-2.0-flash-exp",
                "gen_ai.system": "google_genai",
                "gen_ai.response.model": "gemini-2.0-flash-exp",
                "gen_ai.response.id": "jrSeaMj3MZvB698Pr82s8Ac",
                "gen_ai.response.finish_reasons": ("STOP",),
                "gen_ai.usage.input_tokens": 16,
                "gen_ai.usage.output_tokens": 16,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.content": "The weather in London is 65 degrees fahrenheit. Summarize this.",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.choice.index": 0,
                        "gen_ai.choice.finish_reason": "STOP",
                        "gen_ai.choice.message": '{"role": "model", "content": "The weather in London is mild and pleasant at 65 degrees Fahrenheit.\\n"}',
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_generate_content_with_dict_config(
    client: Models, span_exporter: InMemorySpanExporter
) -> None:
    """Test generation with dict-based config (TypedDict pattern)."""
    response = client.generate_content(
        model="gemini-2.0-flash-exp",
        contents="Say hello",
        config=GenerateContentConfigDict(
            temperature=0.5,
            top_p=0.9,
            top_k=30,
            max_output_tokens=50,
            system_instruction="You are a helpful assistant.",
        ),
    )

    assert isinstance(response, GenerateContentResponse)
    assert response.text

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gemini-2.0-flash-exp",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gemini-2.0-flash-exp",
                "gen_ai.request.temperature": 0.5,
                "gen_ai.request.top_p": 0.9,
                "gen_ai.request.top_k": 30,
                "gen_ai.request.max_tokens": 50,
                "gen_ai.system": "google_genai",
                "gen_ai.response.model": "gemini-2.0-flash-exp",
                "gen_ai.response.id": "j7SeaPPQGKn9698P0-izuAo",
                "gen_ai.response.finish_reasons": ("STOP",),
                "gen_ai.usage.input_tokens": 8,
                "gen_ai.usage.output_tokens": 10,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.system.message",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.content": "You are a helpful assistant.",
                    },
                },
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.content": "Say hello",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.choice.index": 0,
                        "gen_ai.choice.finish_reason": "STOP",
                        "gen_ai.choice.message": '{"role": "model", "content": "Hello! How can I help you today?\\n"}',
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_generate_content_with_content_dict(
    client: Models, span_exporter: InMemorySpanExporter
) -> None:
    """Test generation with ContentDict (TypedDict pattern)."""
    response = client.generate_content(
        model="gemini-2.0-flash-exp",
        contents=ContentDict(
            role="user",
            parts=[
                PartDict(text="What is 2+2?"),
            ],
        ),
    )

    assert isinstance(response, GenerateContentResponse)
    assert response.text

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat gemini-2.0-flash-exp",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gemini-2.0-flash-exp",
                "gen_ai.system": "google_genai",
                "gen_ai.response.model": "gemini-2.0-flash-exp",
                "gen_ai.response.id": "kLSeaNUNtYOb0g_6_eWBBg",
                "gen_ai.response.finish_reasons": ("STOP",),
                "gen_ai.usage.input_tokens": 7,
                "gen_ai.usage.output_tokens": 8,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.content": "What is 2+2?",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "google_genai",
                        "gen_ai.choice.index": 0,
                        "gen_ai.choice.finish_reason": "STOP",
                        "gen_ai.choice.message": '{"role": "model", "content": "2 + 2 = 4\\n"}',
                    },
                },
            ],
        }
    )


def test_instrument_unknown_client_class(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test instrumentation with unknown client class."""

    class UnknownClient:
        """A client class that is not Models or AsyncModels."""

        pass

    mock_client = UnknownClient()

    with caplog.at_level("WARNING"):
        instrument_google(mock_client)  # type: ignore[arg-type]

    assert "Unknown Google GenAI client class" in caplog.text
    assert not hasattr(mock_client, "_lilypad_instrumented")


def test_instrument_models_with_readonly_generate_content(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test instrumentation when generate_content is read-only to cover lines 52-53."""
    mock_models = Mock(spec=Models)
    type(mock_models).generate_content = property(lambda self: Mock())

    with caplog.at_level("WARNING"):
        instrument_google(mock_models)

    assert hasattr(mock_models, "_lilypad_instrumented")
    assert mock_models._lilypad_instrumented is True
    assert "Failed to wrap generate_content: AttributeError" in caplog.text


@pytest.mark.vcr()
def test_generate_with_typeddict_config_and_content(
    client: Models, span_exporter: InMemorySpanExporter
) -> None:
    """Test with TypedDict-based config and content."""
    config_dict = GenerateContentConfigDict(
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        max_output_tokens=100,
        stop_sequences=["END"],
        presence_penalty=0.1,
        frequency_penalty=0.2,
        system_instruction="You are a helpful assistant",
    )

    content_dict = ContentDict(
        role="user",
        parts=[
            PartDict(text="What is 1+1?"),
        ],
    )

    response = client.generate_content(
        model="gemini-2.0-flash-exp",
        contents=[content_dict],
        config=config_dict,
    )

    assert response.text
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1


@pytest.mark.vcr()
def test_generate_with_pydantic_config_and_content(
    client: Models, span_exporter: InMemorySpanExporter
) -> None:
    """Test with Pydantic-based config and content."""

    config = GenerateContentConfig(
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        max_output_tokens=100,
        stop_sequences=["END"],
        presence_penalty=0.1,
        frequency_penalty=0.2,
        system_instruction="You are a helpful assistant",
    )

    content = Content(
        role="user",
        parts=[
            Part(text="What is 1+1?"),
        ],
    )

    response = client.generate_content(
        model="gemini-2.0-flash-exp",
        contents=[content],
        config=config,
    )

    assert response.text
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1


@pytest.mark.vcr()
def test_sync_generate_with_no_contents(
    client: Models, span_exporter: InMemorySpanExporter
) -> None:
    """Test generation with missing contents to cover early return."""
    from contextlib import suppress

    with suppress(Exception):
        response = client.generate_content(
            model="gemini-2.0-flash-exp",
            contents="",
        )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1

    span_data = extract_span_data(spans[0])
    events = span_data.get("events", [])
    user_messages = [e for e in events if e["name"] == "gen_ai.user.message"]
    assert len(user_messages) == 0


@pytest.mark.vcr()
def test_multi_turn_with_function_response_typeddict(
    client: Models, span_exporter: InMemorySpanExporter
) -> None:
    """Test multi-turn conversation with function response using TypedDict."""
    get_weather = FunctionDeclaration(
        name="get_weather",
        description="Get the weather",
        parameters=Schema(
            type=Type.OBJECT,
            properties={
                "location": Schema(
                    type=Type.STRING,
                ),
            },
            required=["location"],
        ),
    )

    tool = Tool(function_declarations=[get_weather])

    contents_list: ContentListUnionDict = [
        ContentDict(role="user", parts=[PartDict(text="What's the weather in Paris?")]),
        ContentDict(
            role="model",
            parts=[
                PartDict(
                    function_call=FunctionCallDict(
                        name="get_weather", args={"location": "Paris"}
                    )
                )
            ],
        ),
        ContentDict(
            role="user",
            parts=[
                PartDict(
                    function_response=FunctionResponseDict(
                        name="get_weather",
                        response={"temperature": "15C", "conditions": "sunny"},
                    )
                )
            ],
        ),
    ]

    response = client.generate_content(
        model="gemini-2.0-flash-exp",
        contents=contents_list,
        config=GenerateContentConfig(tools=[tool]),
    )

    assert response
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1


@pytest.mark.vcr()
def test_generate_with_dict_tools(
    client: Models,
    span_exporter: InMemorySpanExporter,
) -> None:
    """Test dict-based tools to cover lines 155-171."""
    tool_dict = ToolDict(
        function_declarations=[
            FunctionDeclarationDict(
                name="search_database",
                description="Search for information in database",
                parameters=SchemaDict(
                    type=Type.OBJECT,
                    properties={
                        "query": SchemaDict(type=Type.STRING),
                        "limit": SchemaDict(type=Type.INTEGER),
                    },
                    required=["query"],
                ),
            ),
            FunctionDeclarationDict(
                name="get_user_info",
                description="Get user information",
                parameters=SchemaDict(
                    type=Type.OBJECT,
                    properties={
                        "user_id": SchemaDict(type=Type.STRING),
                    },
                    required=["user_id"],
                ),
            ),
        ]
    )

    config_dict = GenerateContentConfigDict(temperature=0.5, tools=[tool_dict])

    response = client.generate_content(
        model="gemini-2.0-flash-exp",
        contents="Search for AI news",
        config=config_dict,
    )

    assert response
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    span_data = extract_span_data(spans[0])
    assert span_data["attributes"]["gen_ai.request.functions"] == snapshot(
        ("search_database", "get_user_info")
    )


@pytest.mark.vcr()
def test_generate_with_inline_data_bytes(
    client: Models,
    span_exporter: InMemorySpanExporter,
) -> None:
    """Test inline_data with bytes to cover lines 370-377, 385-391."""

    image_bytes = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )

    contents: ContentListUnionDict = [
        ContentDict(
            role="user",
            parts=[
                PartDict(text="What is in this image?"),
                PartDict(inline_data=BlobDict(mime_type="image/png", data=image_bytes)),
            ],
        )
    ]

    response = client.generate_content(
        model="gemini-2.0-flash-exp",
        contents=contents,
    )

    assert response
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    span_data = extract_span_data(spans[0])
    events = span_data["events"]
    assert len(events) >= 1
    user_message_event = events[0]
    assert user_message_event["name"] == "gen_ai.user.message"
    user_message = user_message_event["attributes"]["gen_ai.content"]
    assert "What is in this image?" in user_message


@pytest.mark.vcr()
def test_generate_with_part_instance(
    client: Models,
    span_exporter: InMemorySpanExporter,
) -> None:
    """Test Part instance in content to cover line 313."""

    part = Part(text="Explain quantum computing in simple terms")

    response = client.generate_content(
        model="gemini-2.0-flash-exp",
        contents=part,
    )

    assert response
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    span_data = extract_span_data(spans[0])
    events = span_data["events"]
    assert len(events) >= 1
    user_message_event = events[0]
    assert user_message_event["name"] == "gen_ai.user.message"
    user_message = user_message_event["attributes"]["gen_ai.content"]
    assert "Explain quantum computing" in user_message


@pytest.mark.vcr()
def test_generate_with_mixed_content_types(
    client: Models,
    span_exporter: InMemorySpanExporter,
) -> None:
    """Test mixed content types to cover line 324."""

    contents = [
        "Simple string content",
        Content(parts=[Part(text="Content object with Part")], role="user"),
        {"parts": [{"text": "Dict-based content"}]},
        Part(text="Direct Part object"),
    ]

    for content in contents:
        response = client.generate_content(
            model="gemini-2.0-flash-exp",
            contents=content,
        )
        assert response

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 4


@pytest.mark.vcr()
def test_generate_with_part_dict_without_parts_wrapper(
    client: Models,
    span_exporter: InMemorySpanExporter,
) -> None:
    """Test part dict without parts wrapper to cover line 185 in _utils.py."""
    part = Part(text="Test content without parts wrapper")

    response = client.generate_content(
        model="gemini-2.0-flash-exp",
        contents=[part],
    )

    assert response
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1

    events = extract_span_data(spans[0])["events"]
    assert len(events) >= 1
    user_message_event = events[0]
    assert user_message_event["name"] == "gen_ai.user.message"
    assert (
        "Test content without parts wrapper"
        in user_message_event["attributes"]["gen_ai.content"]
    )


@pytest.mark.vcr()
def test_generate_with_base64_string_inline_data(
    client: Models,
    span_exporter: InMemorySpanExporter,
) -> None:
    """Test inline_data with base64 string to cover line 238 in _utils.py."""
    base64_string = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    content = Content(
        parts=[
            Part(text="Analyze this base64 encoded image"),
            Part(
                inline_data=Blob(
                    mime_type="image/png", data=base64.b64decode(base64_string)
                )
            ),
        ],
        role="user",
    )

    response = client.generate_content(
        model="gemini-2.0-flash-exp",
        contents=content,
    )

    assert response
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1

    events = extract_span_data(spans[0])["events"]
    assert len(events) >= 1
    user_message_event = events[0]
    assert user_message_event["name"] == "gen_ai.user.message"
    assert (
        "Analyze this base64 encoded image"
        in user_message_event["attributes"]["gen_ai.content"]
    )


@pytest.mark.vcr()
def test_generate_with_webp_image(
    client: Models,
    span_exporter: InMemorySpanExporter,
) -> None:
    """Test WebP image handling to cover lines 179-194 in _utils.py."""
    img = Image.new("RGB", (1, 1), color="red")
    buffer = BytesIO()
    img.save(buffer, format="WEBP")
    webp_bytes = buffer.getvalue()

    webp_img = Image.open(BytesIO(webp_bytes))

    response = client.generate_content(
        model="gemini-2.0-flash-exp",
        contents=[webp_img],
    )

    assert response
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1

    events = extract_span_data(spans[0])["events"]
    assert len(events) >= 1
    user_message_event = events[0]
    assert user_message_event["name"] == "gen_ai.user.message"
    assert user_message_event["attributes"]["gen_ai.system"] == "google_genai"
