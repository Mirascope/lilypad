"""Initialize Lilypad OpenTelemetry instrumentation."""

from __future__ import annotations

import logging
import importlib.util
from typing import Any
from secrets import token_bytes
from contextlib import contextmanager
from collections.abc import Sequence, Generator

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

try:
    from rich.logging import RichHandler as LogHandler
except ImportError:
    from logging import StreamHandler as LogHandler

DEFAULT_LOG_LEVEL: int = logging.INFO


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
        self._logged_trace_ids = set()  # Track which traces we've already logged

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Convert spans to a list of JSON serializable dictionaries and send them."""
        if not spans:
            return SpanExportResult.SUCCESS

        span_data = [self._span_to_dict(span) for span in spans]

        try:
            response = self.client.projects.traces.create(
                project_uuid=self.settings.project_id, request_options={"additional_body_parameters": span_data}
            )  # pyright: ignore[reportArgumentType]
        except LilypadException as exc:
            self.log.debug("Server responded with error: %s", exc)
            return SpanExportResult.FAILURE
        except Exception as exc:
            self.log.error("Unexpected error sending spans: %s", exc)
            return SpanExportResult.FAILURE

        self.log.debug(f"Spans {response.trace_status}: {response.span_count} spans")
        if response.trace_status == "queued" and response.span_count > 0:
            # When using Kafka queue, we don't get database UUIDs back immediately
            # So we can only provide the generic traces URL
            unique_trace_ids = list(set(response.trace_ids))

            # Only log trace URLs that haven't been logged before
            new_trace_ids = [tid for tid in unique_trace_ids if tid not in self._logged_trace_ids]

            if new_trace_ids:
                # Mark these trace IDs as logged
                self._logged_trace_ids.update(new_trace_ids)

                if len(new_trace_ids) == 1:
                    self.log.info(
                        f"View trace at: {self.settings.remote_client_url}/projects/{self.settings.project_id}/traces/{new_trace_ids[0]}"
                    )
                else:
                    self.log.info(
                        f"View {len(new_trace_ids)} new traces at: {self.settings.remote_client_url}/projects/{self.settings.project_id}/traces"
                    )
                    for trace_id in new_trace_ids:
                        self.log.debug(
                            f"  - {self.settings.remote_client_url}/projects/{self.settings.project_id}/traces/{trace_id}"
                        )
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        """Shutdown the exporter."""
        pass  # Nothing to clean up

    def force_flush(self, timeout_millis: int = 30_000) -> bool:
        """Force flush any pending spans."""
        return True  # Always return True since we send immediately

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
