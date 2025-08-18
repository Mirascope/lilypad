import os
import json
import inspect
from unittest.mock import Mock, AsyncMock, patch
from importlib.metadata import PackageNotFoundError

import pytest
from wrapt import FunctionWrapper
from dotenv import load_dotenv
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.aio import ChatCompletionsClient as AsyncChatCompletionsClient
from azure.ai.inference.models import (
    ChatCompletions,
    StreamingChatCompletionsUpdate,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    ChatRequestMessage,
)
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import (
    ClientAuthenticationError,
    ResourceNotFoundError,
    ServiceRequestError,
)
from inline_snapshot import snapshot
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from lilypad._internal.otel.azure.instrument import instrument_azure

from ..test_utils import extract_span_data


@pytest.fixture
def azure_endpoint() -> str:
    load_dotenv()
    endpoint = os.getenv("AZURE_INFERENCE_ENDPOINT")
    if not endpoint:
        pytest.skip("AZURE_INFERENCE_ENDPOINT not set")
    return endpoint


@pytest.fixture
def azure_credential() -> str:
    load_dotenv()
    credential = os.getenv("AZURE_INFERENCE_CREDENTIAL")
    if not credential:
        pytest.skip("AZURE_INFERENCE_CREDENTIAL not set")
    return credential


@pytest.fixture
def client(azure_endpoint: str, azure_credential: str) -> ChatCompletionsClient:
    client = ChatCompletionsClient(
        endpoint=azure_endpoint,
        credential=AzureKeyCredential(azure_credential),
        api_version="2024-05-01-preview",
    )
    instrument_azure(client)
    return client


@pytest.fixture
def async_client(
    azure_endpoint: str, azure_credential: str
) -> AsyncChatCompletionsClient:
    client = AsyncChatCompletionsClient(
        endpoint=azure_endpoint,
        credential=AzureKeyCredential(azure_credential),
        api_version="2024-05-01-preview",
    )
    instrument_azure(client)
    return client


@pytest.mark.vcr()
def test_sync_completion_simple(
    client: ChatCompletionsClient, span_exporter: InMemorySpanExporter
) -> None:
    response = client.complete(
        model="Ministral-3B-hgtva",
        messages=[UserMessage(content="Hello, say 'Hi' back to me")],
        max_tokens=50,
    )

    assert isinstance(response, ChatCompletions)
    assert response.choices
    assert response.choices[0].message.content

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat Ministral-3B-hgtva",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.system": "az.ai.inference",
                "gen_ai.request.model": "Ministral-3B-hgtva",
                "gen_ai.request.max_tokens": 50,
                "gen_ai.response.model": "ministral-3b-2410",
                "gen_ai.response.finish_reasons": ("CompletionsFinishReason.STOPPED",),
                "gen_ai.response.id": "7b73bae5f1764e26bea6b3507cc2fd92",
                "gen_ai.usage.input_tokens": 12,
                "gen_ai.usage.output_tokens": 8,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "az.ai.inference",
                        "content": "Hello, say 'Hi' back to me",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "az.ai.inference",
                        "message": '{"role": "assistant", "content": "Hi! How are you today?"}',
                        "index": 0,
                        "finish_reason": "CompletionsFinishReason.STOPPED",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_completion_with_dict_messages(
    client: ChatCompletionsClient, span_exporter: InMemorySpanExporter
) -> None:
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Count from 1 to 3"},
    ]

    response = client.complete(
        model="Ministral-3B-hgtva",
        messages=messages,
        max_tokens=50,
        temperature=0.7,
    )

    assert isinstance(response, ChatCompletions)
    assert response.choices

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat Ministral-3B-hgtva",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.system": "az.ai.inference",
                "gen_ai.request.model": "Ministral-3B-hgtva",
                "gen_ai.request.temperature": 0.7,
                "gen_ai.request.max_tokens": 50,
                "gen_ai.response.model": "ministral-3b-2410",
                "gen_ai.response.finish_reasons": ("CompletionsFinishReason.STOPPED",),
                "gen_ai.response.id": "0513e63e018f423cb3e49541c9cf8d21",
                "gen_ai.usage.input_tokens": 16,
                "gen_ai.usage.output_tokens": 8,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.system.message",
                    "attributes": {
                        "gen_ai.system": "az.ai.inference",
                        "content": "You are a helpful assistant",
                    },
                },
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "az.ai.inference",
                        "content": "Count from 1 to 3",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "az.ai.inference",
                        "message": '{"role": "assistant", "content": "1, 2, 3"}',
                        "index": 0,
                        "finish_reason": "CompletionsFinishReason.STOPPED",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
@pytest.mark.asyncio
async def test_async_completion_simple(
    async_client: AsyncChatCompletionsClient, span_exporter: InMemorySpanExporter
) -> None:
    response = await async_client.complete(
        model="Ministral-3B-hgtva",
        messages=[UserMessage(content="Hello, say 'Hi' back to me")],
        max_tokens=50,
    )

    assert isinstance(response, ChatCompletions)
    assert response.choices
    assert response.choices[0].message.content

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat Ministral-3B-hgtva",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.system": "az.ai.inference",
                "gen_ai.request.model": "Ministral-3B-hgtva",
                "gen_ai.request.max_tokens": 50,
                "gen_ai.response.model": "ministral-3b-2410",
                "gen_ai.response.finish_reasons": ("CompletionsFinishReason.STOPPED",),
                "gen_ai.response.id": "9de60a436813471282c5f089b14d327e",
                "gen_ai.usage.input_tokens": 12,
                "gen_ai.usage.output_tokens": 10,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "az.ai.inference",
                        "content": "Hello, say 'Hi' back to me",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "az.ai.inference",
                        "message": '{"role": "assistant", "content": "Hello! How can I assist you today?"}',
                        "index": 0,
                        "finish_reason": "CompletionsFinishReason.STOPPED",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_completion_streaming(
    client: ChatCompletionsClient, span_exporter: InMemorySpanExporter
) -> None:
    stream = client.complete(
        model="Ministral-3B-hgtva",
        messages=[UserMessage(content="Count from 1 to 3")],
        max_tokens=50,
        stream=True,
    )

    chunks = []
    for chunk in stream:
        chunks.append(chunk)
        assert isinstance(chunk, StreamingChatCompletionsUpdate)

    assert len(chunks) > 0

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1

    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat Ministral-3B-hgtva",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.system": "az.ai.inference",
                "gen_ai.request.model": "Ministral-3B-hgtva",
                "gen_ai.request.max_tokens": 50,
                "gen_ai.response.model": "ministral-3b-2410",
                "gen_ai.response.finish_reasons": ("CompletionsFinishReason.STOPPED",),
                "gen_ai.response.id": "c1d28f6d0a1a4832833ef1312d169322",
                "gen_ai.usage.input_tokens": 10,
                "gen_ai.usage.output_tokens": 8,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "az.ai.inference",
                        "content": "Count from 1 to 3",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "az.ai.inference",
                        "message": '{"role": "assistant", "content": "1, 2, 3"}',
                        "index": 0,
                        "finish_reason": "CompletionsFinishReason.STOPPED",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_completion_with_system_message(
    client: ChatCompletionsClient, span_exporter: InMemorySpanExporter
) -> None:
    response = client.complete(
        model="Ministral-3B-hgtva",
        messages=[
            SystemMessage(content="You are a mathematician"),
            UserMessage(content="What is 2+2?"),
        ],
        max_tokens=50,
    )

    assert isinstance(response, ChatCompletions)
    assert response.choices

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1

    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat Ministral-3B-hgtva",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.system": "az.ai.inference",
                "gen_ai.request.model": "Ministral-3B-hgtva",
                "gen_ai.request.max_tokens": 50,
                "gen_ai.response.model": "ministral-3b-2410",
                "gen_ai.response.finish_reasons": ("CompletionsFinishReason.STOPPED",),
                "gen_ai.response.id": "eea60b280f7f4b5d99eb8cdc5d8313ca",
                "gen_ai.usage.input_tokens": 15,
                "gen_ai.usage.output_tokens": 13,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.system.message",
                    "attributes": {
                        "gen_ai.system": "az.ai.inference",
                        "content": "You are a mathematician",
                    },
                },
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "az.ai.inference",
                        "content": "What is 2+2?",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "az.ai.inference",
                        "message": '{"role": "assistant", "content": "The sum of 2 and 2 is 4."}',
                        "index": 0,
                        "finish_reason": "CompletionsFinishReason.STOPPED",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_completion_with_parameters(
    client: ChatCompletionsClient, span_exporter: InMemorySpanExporter
) -> None:
    response = client.complete(
        model="Ministral-3B-hgtva",
        messages=[UserMessage(content="Write a haiku about AI")],
        max_tokens=100,
        temperature=0.8,
        top_p=0.9,
        frequency_penalty=0.5,
        presence_penalty=0.2,
    )

    assert isinstance(response, ChatCompletions)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1

    attributes = spans[0].attributes or {}
    assert attributes["gen_ai.request.temperature"] == 0.8
    assert attributes["gen_ai.request.max_tokens"] == 100
    assert attributes["gen_ai.request.top_p"] == 0.9
    assert attributes["gen_ai.request.frequency_penalty"] == 0.5
    assert attributes["gen_ai.request.presence_penalty"] == 0.2


@pytest.mark.vcr()
def test_sync_completion_multi_turn(
    client: ChatCompletionsClient, span_exporter: InMemorySpanExporter
) -> None:
    messages = [
        UserMessage(content="My name is Alice"),
        AssistantMessage(content="Nice to meet you, Alice!"),
        UserMessage(content="What's my name?"),
    ]

    response = client.complete(
        model="Ministral-3B-hgtva",
        messages=messages,
        max_tokens=50,
    )

    assert isinstance(response, ChatCompletions)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1

    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat Ministral-3B-hgtva",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.system": "az.ai.inference",
                "gen_ai.request.model": "Ministral-3B-hgtva",
                "gen_ai.request.max_tokens": 50,
                "gen_ai.response.model": "ministral-3b-2410",
                "gen_ai.response.finish_reasons": ("CompletionsFinishReason.STOPPED",),
                "gen_ai.response.id": "f1973f1278a44395b7679bd248c10279",
                "gen_ai.usage.input_tokens": 22,
                "gen_ai.usage.output_tokens": 6,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "az.ai.inference",
                        "content": "My name is Alice",
                    },
                },
                {
                    "name": "gen_ai.assistant.message",
                    "attributes": {
                        "gen_ai.system": "az.ai.inference",
                        "content": "Nice to meet you, Alice!",
                    },
                },
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "az.ai.inference",
                        "content": "What's my name?",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "az.ai.inference",
                        "message": '{"role": "assistant", "content": "Your name is Alice."}',
                        "index": 0,
                        "finish_reason": "CompletionsFinishReason.STOPPED",
                    },
                },
            ],
        }
    )


def test_sync_completion_error_not_found(span_exporter: InMemorySpanExporter) -> None:
    mock_client = Mock(spec=ChatCompletionsClient)

    error = ResourceNotFoundError("Model not found")
    original_complete = Mock(side_effect=error)
    mock_client.complete = original_complete

    instrument_azure(mock_client)

    with pytest.raises(ResourceNotFoundError):
        mock_client.complete(
            model="non-existent-model",
            messages=[{"role": "user", "content": "Hello"}],
        )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].status.status_code.name == "ERROR"
    assert "ResourceNotFoundError" in str(
        spans[0].attributes.get("error.type", "") if spans[0].attributes else ""
    )


def test_sync_completion_error_auth(span_exporter: InMemorySpanExporter) -> None:
    mock_client = Mock(spec=ChatCompletionsClient)

    error = ClientAuthenticationError("Invalid API key")
    original_complete = Mock(side_effect=error)
    mock_client.complete = original_complete

    instrument_azure(mock_client)

    with pytest.raises(ClientAuthenticationError):
        mock_client.complete(
            model="Ministral-3B-hgtva",
            messages=[{"role": "user", "content": "Hello"}],
        )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].status.status_code.name == "ERROR"
    assert "ClientAuthenticationError" in str(
        spans[0].attributes.get("error.type", "") if spans[0].attributes else ""
    )


@pytest.mark.asyncio
async def test_async_completion_error(span_exporter: InMemorySpanExporter) -> None:
    mock_client = Mock(spec=AsyncChatCompletionsClient)

    error = ServiceRequestError("Connection error")
    original_complete = AsyncMock(side_effect=error)
    mock_client.complete = original_complete

    instrument_azure(mock_client)

    with pytest.raises(ServiceRequestError):
        await mock_client.complete(
            model="Ministral-3B-hgtva",
            messages=[{"role": "user", "content": "Hello"}],
        )

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].status.status_code.name == "ERROR"
    assert "ServiceRequestError" in str(
        spans[0].attributes.get("error.type", "") if spans[0].attributes else ""
    )


def test_instrumentation_idempotency() -> None:
    mock_client = Mock(spec=ChatCompletionsClient)
    original_complete = Mock()
    mock_client.complete = original_complete

    instrument_azure(mock_client)
    first_wrapper = mock_client.complete

    instrument_azure(mock_client)
    second_wrapper = mock_client.complete

    assert first_wrapper is second_wrapper
    assert hasattr(mock_client, "_lilypad_instrumented")
    assert mock_client._lilypad_instrumented is True


def test_instrumentation_preserves_signature() -> None:
    endpoint = "https://test.models.ai.azure.com"
    credential = AzureKeyCredential("test-key")

    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=credential,
        api_version="2024-05-01-preview",
    )

    original_sig = inspect.signature(client.complete)

    instrument_azure(client)

    wrapped_sig = inspect.signature(client.complete)

    assert original_sig == wrapped_sig


def test_multiple_clients_independent() -> None:
    endpoint = "https://test.models.ai.azure.com"
    credential = AzureKeyCredential("test-key")

    client1 = ChatCompletionsClient(
        endpoint=endpoint,
        credential=credential,
        api_version="2024-05-01-preview",
    )
    client2 = ChatCompletionsClient(
        endpoint=endpoint,
        credential=credential,
        api_version="2024-05-01-preview",
    )

    instrument_azure(client1)

    assert hasattr(client1, "_lilypad_instrumented")
    assert not hasattr(client2, "_lilypad_instrumented")

    assert isinstance(client1.complete, FunctionWrapper)
    assert not isinstance(client2.complete, FunctionWrapper)


@pytest.mark.asyncio
async def test_async_nature_preserved() -> None:
    endpoint = "https://test.models.ai.azure.com"
    credential = AzureKeyCredential("test-key")

    client = AsyncChatCompletionsClient(
        endpoint=endpoint,
        credential=credential,
        api_version="2024-05-01-preview",
    )

    assert inspect.iscoroutinefunction(client.complete)

    instrument_azure(client)

    assert inspect.iscoroutinefunction(client.complete)


def test_wrapping_failure_handling() -> None:
    from azure.ai.inference.aio import (
        ChatCompletionsClient as AsyncChatCompletionsClient,
    )

    mock_client = Mock(spec=AsyncChatCompletionsClient)

    @property
    def complete_property(self):
        return Mock()

    type(mock_client).complete = complete_property

    with patch("lilypad._internal.otel.azure.instrument.logger") as mock_logger:
        instrument_azure(mock_client)

        mock_logger.warning.assert_called()
        assert "Failed to wrap" in mock_logger.warning.call_args[0][0]


def test_package_version_not_found() -> None:
    mock_client = Mock(spec=ChatCompletionsClient)
    mock_client.complete = Mock()

    with (
        patch(
            "lilypad._internal.otel.azure.instrument.version",
            side_effect=PackageNotFoundError,
        ),
        patch("lilypad._internal.otel.azure.instrument.logger") as mock_logger,
    ):
        instrument_azure(mock_client)

        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        assert "Could not determine lilypad-sdk version" in debug_calls

        assert hasattr(mock_client, "_lilypad_instrumented")


@pytest.mark.vcr()
def test_sync_completion_with_empty_content(
    client: ChatCompletionsClient, span_exporter: InMemorySpanExporter
) -> None:
    response = client.complete(
        model="Ministral-3B-hgtva",
        messages=[UserMessage(content="")],
        max_tokens=50,
    )

    assert isinstance(response, ChatCompletions)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1

    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "chat Ministral-3B-hgtva",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.system": "az.ai.inference",
                "gen_ai.request.model": "Ministral-3B-hgtva",
                "gen_ai.request.max_tokens": 50,
                "gen_ai.response.model": "ministral-3b-2410",
                "gen_ai.response.finish_reasons": ("CompletionsFinishReason.STOPPED",),
                "gen_ai.response.id": "9e189bdbcaa3473f896b5a05c555152f",
                "gen_ai.usage.input_tokens": 3,
                "gen_ai.usage.output_tokens": 22,
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [
                {
                    "name": "gen_ai.user.message",
                    "attributes": {
                        "gen_ai.system": "az.ai.inference",
                        "content": "",
                    },
                },
                {
                    "name": "gen_ai.choice",
                    "attributes": {
                        "gen_ai.system": "az.ai.inference",
                        "message": '{"role": "assistant", "content": "Hello! How can I assist you today? Let\'s chat about anything you\'d like. \\ud83d\\ude0a"}',
                        "index": 0,
                        "finish_reason": "CompletionsFinishReason.STOPPED",
                    },
                },
            ],
        }
    )


@pytest.mark.vcr()
def test_sync_completion_with_tools(
    client: ChatCompletionsClient, span_exporter: InMemorySpanExporter
) -> None:
    from azure.ai.inference.models import (
        ChatCompletionsToolDefinition,
        FunctionDefinition,
    )

    tools = [
        ChatCompletionsToolDefinition(
            function=FunctionDefinition(
                name="get_weather",
                description="Get the weather for a location",
                parameters={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and country, e.g. San Francisco, USA",
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "The temperature unit",
                        },
                    },
                    "required": ["location"],
                },
            )
        )
    ]

    response = client.complete(
        model="Ministral-3B-hgtva",
        messages=[UserMessage(content="What's the weather in Tokyo?")],
        tools=tools,
        max_tokens=150,
    )

    assert isinstance(response, ChatCompletions)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    span_data = extract_span_data(spans[0])

    if response.choices[0].message.tool_calls:
        choice_event = span_data["events"][-1]
        assert "tool_calls" in json.loads(choice_event["attributes"]["message"])


@pytest.mark.vcr()
def test_sync_streaming_with_tools(
    client: ChatCompletionsClient, span_exporter: InMemorySpanExporter
) -> None:
    from azure.ai.inference.models import (
        ChatCompletionsToolDefinition,
        FunctionDefinition,
    )

    tools = [
        ChatCompletionsToolDefinition(
            function=FunctionDefinition(
                name="calculate",
                description="Perform a calculation",
                parameters={
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "The mathematical expression to calculate",
                        }
                    },
                    "required": ["expression"],
                },
            )
        )
    ]

    stream = client.complete(
        model="Ministral-3B-hgtva",
        messages=[UserMessage(content="Calculate 2 + 2")],
        tools=tools,
        max_tokens=150,
        stream=True,
    )

    chunks = []
    for chunk in stream:
        chunks.append(chunk)
        assert isinstance(chunk, StreamingChatCompletionsUpdate)

    assert len(chunks) > 0

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1

    span_data = extract_span_data(spans[0])
    assert span_data["name"] == "chat Ministral-3B-hgtva"
    assert span_data["attributes"]["gen_ai.operation.name"] == "chat"
    assert span_data["attributes"]["gen_ai.system"] == "az.ai.inference"


@pytest.mark.vcr()
def test_sync_completion_with_tool_response(
    client: ChatCompletionsClient, span_exporter: InMemorySpanExporter
) -> None:
    from azure.ai.inference.models import (
        ChatCompletionsToolDefinition,
        FunctionDefinition,
        ToolMessage,
    )

    tools = [
        ChatCompletionsToolDefinition(
            function=FunctionDefinition(
                name="get_weather",
                description="Get weather information",
                parameters={
                    "type": "object",
                    "properties": {"location": {"type": "string"}},
                    "required": ["location"],
                },
            )
        )
    ]

    messages: list[ChatRequestMessage] = [
        UserMessage(content="What's the weather in Paris?")
    ]

    response1 = client.complete(
        model="Ministral-3B-hgtva",
        messages=messages,
        tools=tools,
        max_tokens=150,
    )

    if response1.choices[0].message.tool_calls:
        tool_call = response1.choices[0].message.tool_calls[0]

        messages.append(response1.choices[0].message)  # type: ignore[arg-type]

        tool_msg = ToolMessage(
            content="The weather in Paris is 22°C and sunny", tool_call_id=tool_call.id
        )
        messages.append(tool_msg)

        response2 = client.complete(
            model="Ministral-3B-hgtva",
            messages=messages,
            max_tokens=150,
        )

        assert isinstance(response2, ChatCompletions)

    spans = span_exporter.get_finished_spans()

    assert len(spans) >= 1

    for span in spans:
        span_data = extract_span_data(span)
        for event in span_data["events"]:
            if event["name"] == "gen_ai.tool.message":
                assert "id" in event["attributes"]
                assert "content" in event["attributes"]


@pytest.mark.vcr()
def test_sync_completion_with_dict_tool_calls(
    client: ChatCompletionsClient, span_exporter: InMemorySpanExporter
) -> None:
    from azure.ai.inference.models import (
        ChatCompletionsToolDefinition,
        FunctionDefinition,
    )

    tools = [
        ChatCompletionsToolDefinition(
            function=FunctionDefinition(
                name="get_weather",
                description="Get weather information",
                parameters={
                    "type": "object",
                    "properties": {"location": {"type": "string"}},
                    "required": ["location"],
                },
            )
        )
    ]

    messages = [{"role": "user", "content": "What's the weather in London?"}]

    response = client.complete(
        model="Ministral-3B-hgtva",
        messages=messages,
        tools=tools,
        max_tokens=150,
    )

    assert isinstance(response, ChatCompletions)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1

    if response.choices[0].message.tool_calls:
        assistant_msg = {
            "role": "assistant",
            "content": response.choices[0].message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in response.choices[0].message.tool_calls
            ],
        }

        messages2 = [
            {"role": "user", "content": "What's the weather?"},
            assistant_msg,
            {
                "role": "tool",
                "content": "20°C and sunny",
                "tool_call_id": response.choices[0].message.tool_calls[0].id,
            },
        ]

        response2 = client.complete(
            model="Ministral-3B-hgtva",
            messages=messages2,
            max_tokens=50,
        )

        assert isinstance(response2, ChatCompletions)


@pytest.mark.vcr()
def test_sync_streaming_with_metadata_only_chunks(
    client: ChatCompletionsClient, span_exporter: InMemorySpanExporter
) -> None:
    stream = client.complete(
        model="Ministral-3B-hgtva",
        messages=[UserMessage(content="Say hello")],
        max_tokens=10,
        stream=True,
    )

    chunks = []
    for chunk in stream:
        chunks.append(chunk)

    assert len(chunks) > 0

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1


@pytest.mark.vcr()
def test_sync_completion_with_list_content(
    client: ChatCompletionsClient, span_exporter: InMemorySpanExporter
) -> None:
    messages = [
        {"role": "user", "content": "Hello, please respond with a greeting"},
        {"role": "assistant", "content": "Hello! How can I help you today?"},
        {"role": "user", "content": "Thanks!"},
    ]

    response = client.complete(
        model="Ministral-3B-hgtva",
        messages=messages,
        max_tokens=50,
    )

    assert isinstance(response, ChatCompletions)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1

    span_data = extract_span_data(spans[0])
    assert len(span_data["events"]) >= 3
    event_names = [event["name"] for event in span_data["events"]]
    assert "gen_ai.user.message" in event_names
    assert "gen_ai.assistant.message" in event_names
    assert "gen_ai.choice" in event_names


@pytest.mark.vcr()
@pytest.mark.asyncio
async def test_async_streaming_fixed(
    async_client: AsyncChatCompletionsClient, span_exporter: InMemorySpanExporter
) -> None:
    try:
        stream = await async_client.complete(
            model="Ministral-3B-hgtva",
            messages=[UserMessage(content="Count to 2")],
            max_tokens=20,
            stream=True,
        )

        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
            assert isinstance(chunk, StreamingChatCompletionsUpdate)

        assert len(chunks) > 0

        spans = span_exporter.get_finished_spans()
        assert len(spans) == 1

        assert extract_span_data(spans[0]) == snapshot(
            {
                "name": "chat Ministral-3B-hgtva",
                "attributes": {
                    "gen_ai.operation.name": "chat",
                    "gen_ai.system": "az.ai.inference",
                    "gen_ai.request.model": "Ministral-3B-hgtva",
                    "gen_ai.request.max_tokens": 20,
                    "gen_ai.response.model": "ministral-3b-2410",
                    "gen_ai.response.finish_reasons": (
                        "CompletionsFinishReason.STOPPED",
                    ),
                    "gen_ai.response.id": "517c399f02a74982b46d79c15d9e92cb",
                    "gen_ai.usage.input_tokens": 7,
                    "gen_ai.usage.output_tokens": 11,
                },
                "status": {"status_code": "UNSET", "description": None},
                "events": [
                    {
                        "name": "gen_ai.user.message",
                        "attributes": {
                            "gen_ai.system": "az.ai.inference",
                            "content": "Count to 2",
                        },
                    },
                    {
                        "name": "gen_ai.choice",
                        "attributes": {
                            "gen_ai.system": "az.ai.inference",
                            "index": 0,
                            "finish_reason": "CompletionsFinishReason.STOPPED",
                            "message": '{"role": "assistant", "content": "Sure, here it is:\\n\\n1, 2"}',
                        },
                    },
                ],
            }
        )
    finally:
        await async_client.close()


def test_instrumentation_wrapping_failure_detailed() -> None:
    mock_client = Mock(spec=ChatCompletionsClient)

    type(mock_client).complete = property(lambda self: Mock())

    with patch("lilypad._internal.otel.azure.instrument.logger") as mock_logger:
        instrument_azure(mock_client)

        mock_logger.warning.assert_called()
        warning_msg = mock_logger.warning.call_args[0][0]
        assert "Failed to wrap" in warning_msg


@pytest.mark.vcr()
def test_sync_streaming_chunk_without_choices(
    client: ChatCompletionsClient, span_exporter: InMemorySpanExporter
) -> None:
    stream = client.complete(
        model="Ministral-3B-hgtva",
        messages=[UserMessage(content="Hi")],
        max_tokens=5,
        stream=True,
    )

    chunks = []
    for chunk in stream:
        chunks.append(chunk)

    assert len(chunks) > 0
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1


@pytest.mark.vcr()
def test_sync_completion_with_complex_content(
    client: ChatCompletionsClient, span_exporter: InMemorySpanExporter
) -> None:
    messages = [
        {"role": "user", "content": {"text": "Hello", "metadata": {"key": "value"}}}
    ]

    from contextlib import suppress

    with suppress(Exception):
        client.complete(
            model="Ministral-3B-hgtva",
            messages=messages,
            max_tokens=50,
        )

    spans = span_exporter.get_finished_spans()

    if spans:
        span_data = extract_span_data(spans[0])

        if span_data.get("events"):
            event = span_data["events"][0]
            if "content" in event.get("attributes", {}):
                assert isinstance(event["attributes"]["content"], str)


@pytest.mark.asyncio
async def test_async_non_streaming_completion(
    async_client: AsyncChatCompletionsClient, span_exporter: InMemorySpanExporter
) -> None:
    try:
        response = await async_client.complete(
            model="Ministral-3B-hgtva",
            messages=[UserMessage(content="Say hi")],
            max_tokens=10,
            stream=False,
        )

        assert isinstance(response, ChatCompletions)
        spans = span_exporter.get_finished_spans()
        assert len(spans) == 1
    finally:
        await async_client.close()
