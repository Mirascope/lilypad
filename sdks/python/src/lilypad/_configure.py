"""Initialize Lilypad OpenTelemetry instrumentation."""

from __future__ import annotations

import time
import queue
import random
import logging
import threading
import importlib.util
from typing import Any
from secrets import token_bytes
from contextlib import contextmanager
from contextvars import copy_context
from collections.abc import Sequence, Generator

from pydantic import TypeAdapter
from opentelemetry import trace
from opentelemetry.trace import INVALID_SPAN_ID, INVALID_TRACE_ID
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import (
    SpanExporter,
    SpanExportResult,
    BatchSpanProcessor,
)
from opentelemetry.sdk.trace.id_generator import IdGenerator

from .exceptions import LilypadException
from ._utils.client import get_sync_client
from ._utils.settings import (
    get_settings,
    _set_settings,
    _current_settings,
)
from ._utils.otel_debug import wrap_batch_processor
from .generated.types.span_public import SpanPublic

try:
    from rich.logging import RichHandler as LogHandler
except ImportError:
    from logging import StreamHandler as LogHandler

DEFAULT_LOG_LEVEL: int = logging.INFO

# Ignore pydantic deprecation warnings by using `list[SpanPublic]` instead of `TraceCreateResponse`
TraceCreateResponseAdapter = TypeAdapter(list[SpanPublic])

_MAX_RETRIES = 5
_BACKOFF_SECS = 2.0
_WORKER_SLEEP = 0.2


class _RetryPayload:
    __slots__ = ("data", "attempts")

    def __init__(self, data: list[dict[str, Any]]) -> None:
        self.data = data
        self.attempts = 0


class CryptoIdGenerator(IdGenerator):
    """Generate span/trace IDs with cryptographically secure randomness."""

    def _random_int(self, n_bytes: int) -> int:
        return int.from_bytes(token_bytes(n_bytes), "big")

    def generate_span_id(self) -> int:
        span_id = self._random_int(8)  # 64bit
        while span_id == INVALID_SPAN_ID:
            span_id = self._random_int(8)
        return span_id

    def generate_trace_id(self) -> int:
        trace_id = self._random_int(16)  # 128bit
        while trace_id == INVALID_TRACE_ID:
            trace_id = self._random_int(16)
        return trace_id


class _JSONSpanExporter(SpanExporter):
    """A custom span exporter that sends spans to a custom endpoint as JSON."""

    def __init__(self) -> None:
        """Initialize the exporter with the custom endpoint URL."""
        self.settings = get_settings()
        self.client = get_sync_client(api_key=self.settings.api_key)
        self.log = logging.getLogger(__name__)
        self._stop = threading.Event()
        self._q: queue.Queue[_RetryPayload] = queue.Queue(maxsize=10_000)
        ctx = copy_context()
        self._worker = threading.Thread(
            target=lambda: ctx.run(self._worker_loop),
            name="LilypadSpanRetry",
            daemon=True,
        )
        self._worker.start()

    def pretty_print_display_names(self, span: SpanPublic) -> None:
        """Extract and pretty print the display_name attribute from each span, handling nested spans."""
        self.log.info(
            f"View the trace at: "
            f"{self.settings.remote_client_url}/projects/{self.settings.project_id}/traces/{span.uuid_}"
        )
        self._print_span_node(span, indent=0)

    def _print_span_node(self, span: SpanPublic, indent: int) -> None:
        """Recursively print a SpanNode and its children with indentation."""
        indent_str = "    " * indent  # 4 spaces per indent level

        self.log.info(f"{indent_str}{span.display_name}")

        for child in span.child_spans:
            self._print_span_node(child, indent + 1)

    def _send_once(self, payload: list[dict[str, Any]]) -> list[SpanPublic] | None:
        """Send once; return list[SpanPublic] if the API accepted the batch."""
        try:
            raw_response = self.client.projects.traces.create(
                project_uuid=self.settings.project_id, request_options={"additional_body_parameters": payload}
            )  # pyright: ignore[reportArgumentType]
        except LilypadException as exc:
            self.log.debug("Server responded with error: %s", exc)
            return None

        if raw_response is None:
            self.log.warning("Server responded with None")
            return None

        response_spans = TraceCreateResponseAdapter.validate_python(raw_response)
        if len(response_spans) > 0:
            return response_spans
        else:
            return None

    def _worker_loop(self) -> None:
        while True:
            item = self._q.get()
            if item is None:
                self._q.task_done()
                break

            try:
                if response_spans := self._send_once(item.data):
                    for response_span in response_spans:
                        self.pretty_print_display_names(response_span)
                    return None
                item.attempts += 1
                if item.attempts <= _MAX_RETRIES and not self._stop.is_set():
                    delay = (_BACKOFF_SECS * 2 ** (item.attempts - 1)) * (0.8 + 0.4 * random.random())
                    time.sleep(delay)
                    self._q.put(item)
            finally:
                self._q.task_done()

    def shutdown(self) -> None:
        self._stop.set()
        self._q.put(None)  # pyright: ignore[reportArgumentType]
        self._worker.join(timeout=5)
        if self._worker.is_alive():
            self.log.warning("Worker did not exit in time – dropping remaining spans")

    def force_flush(self, timeout_millis: int = 30_000) -> bool:
        start = time.time()
        while not self._q.empty() and (time.time() - start) * 1000 < timeout_millis:
            time.sleep(0.05)
        return self._q.empty()

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Convert spans to a list of JSON serializable dictionaries"""
        if not spans:
            return SpanExportResult.SUCCESS

        span_data = [self._span_to_dict(span) for span in spans]

        if response_spans := self._send_once(span_data):
            for response_span in response_spans:
                self.pretty_print_display_names(response_span)
            return SpanExportResult.SUCCESS

        try:
            self._q.put_nowait(_RetryPayload(span_data))
            return SpanExportResult.SUCCESS
        except queue.Full:
            self.log.error("Retry queue full – dropping %d spans", len(span_data))
            return SpanExportResult.FAILURE

    def _span_to_dict(self, span: ReadableSpan) -> dict[str, Any]:
        """Convert the span data to a dictionary that can be serialized to JSON"""
        # span.instrumentation_scope to_json does not work
        instrumentation_scope = (
            {
                "name": span.instrumentation_scope.name,
                "version": span.instrumentation_scope.version,
                "schema_url": span.instrumentation_scope.schema_url,
                "attributes": dict(span.instrumentation_scope.attributes.items())
                if span.instrumentation_scope.attributes
                else None,
            }
            if span.instrumentation_scope
            else {
                "name": None,
                "version": None,
                "schema_url": None,
                "attributes": {},
            }
        )
        return {
            "trace_id": f"{span.context.trace_id:032x}" if span.context else None,
            "span_id": f"{span.context.span_id:016x}" if span.context else None,
            "parent_span_id": f"{span.parent.span_id:016x}" if span.parent else None,
            "instrumentation_scope": instrumentation_scope,
            "resource": span.resource.to_json(0),
            "name": span.name,
            "start_time": span.start_time,
            "end_time": span.end_time,
            "attributes": dict(span.attributes.items()) if span.attributes else {},
            "status": span.status.status_code.name,
            "session_id": span.attributes.get("lilypad.session_id") if span.attributes else None,
            "events": [
                {
                    "name": event.name,
                    "attributes": dict(event.attributes.items()) if event.attributes else {},
                    "timestamp": event.timestamp,
                }
                for event in span.events
            ],
            "links": [
                {
                    "context": {
                        "trace_id": f"{link.context.trace_id:032x}",
                        "span_id": f"{link.context.span_id:016x}",
                    },
                    "attributes": link.attributes,
                }
                for link in span.links
            ],
        }


def configure(
    *,
    api_key: str | None = None,
    project_id: str | None = None,
    base_url: str | None = None,
    log_level: int = DEFAULT_LOG_LEVEL,
    log_format: str | None = None,
    log_handlers: list[logging.Handler] | None = None,
    auto_llm: bool = False,
) -> None:
    """Initialize the OpenTelemetry instrumentation for Lilypad and configure log outputs.

    The user can configure log level, format, and output destination via the parameters.
    This allows adjusting log outputs for local runtimes or different environments.
    """

    current = get_settings()
    new = current.model_copy(deep=True)
    new.update(
        api_key=api_key,
        project_id=project_id,
        base_url=base_url,
    )

    _set_settings(new)

    logger = logging.getLogger("lilypad")
    logger.setLevel(log_level)
    logger.handlers.clear()
    handlers = log_handlers or [LogHandler()]
    for handler in handlers:
        handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(handler)

    # Proceed with tracer provider configuration.
    if trace.get_tracer_provider().__class__.__name__ == "TracerProvider":
        logger.error("TracerProvider already initialized.")  # noqa: T201
        return
    otlp_exporter = _JSONSpanExporter()
    provider = TracerProvider(id_generator=CryptoIdGenerator())
    processor = BatchSpanProcessor(otlp_exporter)  # pyright: ignore[reportArgumentType]
    if log_level == logging.DEBUG:
        wrap_batch_processor(processor)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    if not auto_llm:
        return

    if importlib.util.find_spec("openai") is not None:
        from ._opentelemetry import OpenAIInstrumentor

        OpenAIInstrumentor().instrument()
    if importlib.util.find_spec("anthropic") is not None:
        from ._opentelemetry import AnthropicInstrumentor

        AnthropicInstrumentor().instrument()
    if (
        importlib.util.find_spec("azure") is not None
        and importlib.util.find_spec("azure.ai") is not None
        and importlib.util.find_spec("azure.ai.inference") is not None
    ):
        from ._opentelemetry import AzureInstrumentor

        AzureInstrumentor().instrument()
    if importlib.util.find_spec("google") is not None and importlib.util.find_spec("google.genai") is not None:
        from ._opentelemetry import GoogleGenAIInstrumentor

        GoogleGenAIInstrumentor().instrument()
    if importlib.util.find_spec("botocore") is not None:
        from ._opentelemetry import BedrockInstrumentor

        BedrockInstrumentor().instrument()
    if importlib.util.find_spec("mistralai") is not None:
        from ._opentelemetry import MistralInstrumentor

        MistralInstrumentor().instrument()
    if importlib.util.find_spec("outlines") is not None:
        from ._opentelemetry import OutlinesInstrumentor

        OutlinesInstrumentor().instrument()


@contextmanager
def lilypad_config(**override: Any) -> Generator[None, None, None]:
    token = None
    try:
        base = get_settings()
        tmp = base.model_copy(deep=True)
        tmp.update(**override)
        token = _current_settings.set(tmp)
        yield
    finally:
        if token is not None:
            _current_settings.reset(token)
