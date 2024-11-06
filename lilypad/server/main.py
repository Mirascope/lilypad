"""Main FastAPI application module for Lilypad."""

import json
from collections.abc import Sequence
from typing import Annotated, Any, Literal

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlmodel import Session, select
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response
from starlette.types import Scope as StarletteScope

from lilypad._utils import load_config
from lilypad.models import (
    SpanCreate,
    SpanPublic,
)
from lilypad.server.db.session import get_session
from lilypad.server.models import (
    Provider,
    Scope,
    SpanTable,
)

from .api import llm_fn_router, project_router, version_router
from .services import SpanService


class SPAStaticFiles(StaticFiles):
    """Serve the index.html file for all routes."""

    async def get_response(self, path: str, scope: StarletteScope) -> Response:
        """Get the response for the given path."""
        try:
            return await super().get_response(path, scope)
        except (HTTPException, StarletteHTTPException) as ex:
            if ex.status_code == 404:
                return await super().get_response("index.html", scope)
            else:
                raise ex


app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation exceptions."""
    print(request, exc)  # noqa: T201
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


config = load_config()
port = config.get("port", 8000)

origins = [
    "http://localhost:5173",
    "http://localhost:8000/*",
    "http://127.0.0.1:8000",
    f"http://localhost/{port}",
    f"http://127.0.0.1/{port}",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
api = FastAPI()


@api.post("/v1/traces")
async def traces(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    span_service: Annotated[SpanService, Depends(SpanService)],
) -> list[SpanPublic]:
    """Create span traces."""
    traces_json: list[dict] = await request.json()
    span_tables: list[SpanTable] = []
    latest_parent_span_id = None
    latest_project_id = None
    for lilypad_trace in traces_json:
        if lilypad_trace["instrumentation_scope"]["name"] == "lilypad":
            scope = Scope.LILYPAD
            latest_parent_span_id = lilypad_trace["span_id"]
            latest_project_id = lilypad_trace["attributes"]["lilypad.project_id"]
        else:
            scope = Scope.LLM

        # Handle streaming traces
        if scope == Scope.LLM and not lilypad_trace.get("parent_span_id"):
            parent_span_id = latest_parent_span_id
            project_id = latest_project_id
        else:
            parent_span_id = lilypad_trace.get("parent_span_id", None)
            project_id = lilypad_trace.get("attributes", {}).get(
                "lilypad.project_id", None
            )
        span_create = SpanCreate(
            id=lilypad_trace["span_id"],
            version=lilypad_trace.get("attributes", {}).get("lilypad.version", None),
            parent_span_id=parent_span_id,
            data=lilypad_trace,
            scope=scope,
            version_id=lilypad_trace.get("attributes", {}).get(
                "lilypad.version_id", None
            ),
            project_id=project_id,
        )
        span_service.create_record(span_create)
    parent_traces: list[SpanPublic] = []
    for span_table in span_tables:
        session.refresh(span_table)
        if not span_table.parent_span_id:
            parent_traces.append(set_display_name_and_convert(span_table))

    return parent_traces


def set_display_name_and_convert(
    span: SpanTable,
) -> SpanPublic:
    """Set the display name based on the scope."""
    # TODO: Handle error cases where spans dont have attributes
    if span.scope == Scope.LILYPAD:
        display_name = span.data["attributes"]["lilypad.function_name"]
    elif span.scope == Scope.LLM:
        data = span.data
        display_name = f"{data['attributes']['gen_ai.system']} with '{data['attributes']['gen_ai.request.model']}'"
    else:
        display_name = "Unknown"

    span_public = SpanPublic.model_validate(span)
    span_public.display_name = display_name

    span_public.child_spans = [
        set_display_name_and_convert(child_span) for child_span in span.child_spans
    ]

    return span_public


class TextPart(BaseModel):
    """Text part model."""

    type: Literal["text"]
    text: str


class ImagePart(BaseModel):
    """Image part model."""

    type: Literal["image"]
    media_type: str
    image: str


class AudioPart(BaseModel):
    """Image part model."""

    type: Literal["audio"]
    media_type: str
    audio: str


class ToolPart(BaseModel):
    """Tool part model."""

    type: Literal["tool_call"]
    name: str
    arguments: dict[str, Any]


class MessageParam(BaseModel):
    """Message param model."""

    content: Sequence[TextPart | ImagePart | AudioPart | ToolPart]
    role: str


class SpanMoreDetails(BaseModel):
    """Span more details model."""

    display_name: str
    model: str
    provider: str
    prompt_tokens: float | None = None
    completion_tokens: float | None = None
    duration_ms: float
    code: str | None = None
    function_arguments: dict[str, Any] | None = None
    output: str | None = None
    messages: list[MessageParam]
    data: dict[str, Any]


def group_span_keys(attributes: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Groups gen_ai related attributes into a structured format.

    Args:
        attributes (Dict[str, Any]): Dictionary containing gen_ai prefixed key-value pairs

    Returns:
        Dict[str, Dict[str, Any]]: Grouped and processed attributes

    Example:
        attributes = {
            "gen_ai.prompt.0.content": "Hello",
            "gen_ai.completion.0.content": "Hi there",
            "gen_ai.completion.0.tool_calls.0.name": "search"
        }
    """
    grouped_items = {}
    message_index = 0

    for key, value in attributes.items():
        # Only process gen_ai related keys
        if not key.startswith("gen_ai."):
            continue

        # Remove the "gen_ai" prefix for easier processing
        key_without_prefix = key[len("gen_ai.") :]
        key_parts = key_without_prefix.split(".")
        # Get the base category (prompt or completion) and its index
        if len(key_parts) < 3:  # We need at least category, index, and field
            continue
        item_category = key_parts[0]
        item_index = key_parts[1]

        if item_category not in ["prompt", "completion"]:
            continue

        # Create the group key
        group_key = f"{item_category}.{item_index}"

        # Initialize group if it doesn't exist
        if group_key not in grouped_items:
            grouped_items[group_key] = {"index": message_index}
            message_index += 1

        # Handle tool_calls specially
        if len(key_parts) > 2 and key_parts[2] == "tool_calls":
            tool_call_index = int(key_parts[3])
            tool_call_field = key_parts[4]

            # Initialize tool_calls list if it doesn't exist
            if "tool_calls" not in grouped_items[group_key]:
                grouped_items[group_key]["tool_calls"] = []

            # Extend tool_calls list if needed
            while len(grouped_items[group_key]["tool_calls"]) <= tool_call_index:
                grouped_items[group_key]["tool_calls"].append({})

            # Parse JSON arguments if present
            if tool_call_field == "arguments" and isinstance(value, str):
                try:
                    grouped_items[group_key]["tool_calls"][tool_call_index][
                        tool_call_field
                    ] = json.loads(value)
                except json.JSONDecodeError:
                    grouped_items[group_key]["tool_calls"][tool_call_index][
                        tool_call_field
                    ] = value
            else:
                grouped_items[group_key]["tool_calls"][tool_call_index][
                    tool_call_field
                ] = value
        else:
            # Handle regular fields
            grouped_items[group_key][key_parts[2]] = value

    return grouped_items


def convert_gemini_messages(
    messages: dict[str, Any],
) -> list[MessageParam]:
    """Convert Gemini messages."""
    structured_messages: list[MessageParam] = []
    for key, value in messages.items():
        if key.startswith("prompt"):
            content = []
            for part in json.loads(value["user"]):
                if isinstance(part, str):
                    content.append(TextPart(type="text", text=part))
                elif isinstance(part, dict):
                    if part.get("mime_type", "").startswith("image"):
                        content.append(
                            ImagePart(
                                type="image",
                                media_type=part["mime_type"],
                                image=part["data"],
                            )
                        )
                    elif part.get("mime_type", "").startswith("audio"):
                        content.append(
                            AudioPart(
                                type="audio",
                                media_type=part["mime_type"],
                                audio=part["data"],
                            )
                        )
            structured_messages.append(
                MessageParam(
                    content=content,
                    role="user",
                )
            )
        elif key.startswith("completion"):
            structured_messages.append(
                MessageParam(
                    content=[TextPart(type="text", text=value["content"])],
                    role="assistant",
                )
            )
    return structured_messages


def convert_anthropic_messages(
    messages: dict[str, Any],
) -> list[MessageParam]:
    """Convert Anthropic messages."""
    structured_messages: list[MessageParam] = []
    for key, value in messages.items():
        if key.startswith("prompt"):
            content = []
            try:
                for part in json.loads(value["content"]):
                    if isinstance(part, str):
                        content.append(TextPart(type="text", text=part))
                    elif isinstance(part, dict):
                        if part.get("type", "") == "image":
                            content.append(
                                ImagePart(
                                    type="image",
                                    media_type=part["source"]["media_type"],
                                    image=part["source"]["data"],
                                )
                            )
                        else:
                            content.append(TextPart(type="text", text=part["text"]))
            except json.JSONDecodeError:
                content.append(TextPart(type="text", text=value["content"]))

            structured_messages.append(
                MessageParam(
                    content=content,
                    role="user",
                )
            )
        elif key.startswith("completion"):
            content = []
            part = value.get("content", None)
            if isinstance(part, str):
                content.append(TextPart(type="text", text=part))
            elif isinstance(part, dict):
                content.append(TextPart(type="text", text=part["text"]))
            if tool_calls := value.get("tool_calls", []):
                for tool_call in tool_calls:
                    content.append(
                        ToolPart(
                            type="tool_call",
                            name=tool_call["name"],
                            arguments=tool_call.get("arguments", {}),
                        )
                    )
            if len(content) > 0:
                structured_messages.append(
                    MessageParam(
                        content=content,
                        role="assistant",
                    )
                )
    return structured_messages


def convert_span_to_more_details(span: SpanTable) -> SpanMoreDetails:
    """Convert span to more details."""
    data = span.data
    messages = []
    if span.scope == Scope.LLM:
        raw_messages = group_span_keys(data["attributes"])
        display_name = data["name"]
        code = None
        function_arguments = None
        output = None
        provider = data["attributes"]["gen_ai.system"].lower()
        if provider == Provider.GEMINI:
            messages = convert_gemini_messages(raw_messages)
        elif provider == Provider.OPENROUTER or provider == Provider.OPENAI:
            # TODO: Handle OpenAI messages
            messages = []
        elif provider == Provider.ANTHROPIC:
            messages = convert_anthropic_messages(raw_messages)
    else:
        code = span.version_table.llm_fn.code
        function_arguments = json.loads(data["attributes"]["lilypad.arg_values"])
        output = data["attributes"]["lilypad.output"]
        display_name = data["attributes"]["lilypad.function_name"]
        messages = data["attributes"]["lilypad.messages"]
    attributes: dict = data["attributes"]
    return SpanMoreDetails(
        display_name=display_name,
        model=attributes.get("gen_ai.request.model", "unknown"),
        provider=attributes.get("gen_ai.system", "unknown"),
        prompt_tokens=attributes.get("gen_ai.usage.prompt_tokens"),
        completion_tokens=attributes.get("gen_ai.usage.completion_tokens"),
        duration_ms=data["end_time"] - data["start_time"],
        code=code,
        function_arguments=function_arguments,
        output=output,
        messages=messages,
        data=data,
    )


@api.get("/spans/{span_id}", response_model=SpanMoreDetails)
async def get_span(
    span_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> SpanMoreDetails:
    """Get span by id."""
    span = session.exec(select(SpanTable).where(SpanTable.id == span_id)).first()
    if not span:
        raise HTTPException(status_code=404, detail="Span not found")
    return convert_span_to_more_details(span)


@api.get("/projects/{project_id}/spans/{span_id}", response_model=SpanPublic)
async def get_span_by_project_id(
    span_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> SpanPublic:
    """Get span by id."""
    span = session.exec(select(SpanTable).where(SpanTable.id == span_id)).first()
    if not span:
        raise HTTPException(status_code=404, detail="Span not found")
    return set_display_name_and_convert(span)


@api.get("/projects/{project_id}/traces", response_model=Sequence[SpanPublic])
async def get_traces(
    project_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> Sequence[SpanPublic]:
    """Get all traces"""
    traces = session.exec(
        select(SpanTable).where(
            SpanTable.project_id == project_id,
            SpanTable.parent_span_id.is_(None),  # type: ignore
        )
    ).all()
    traces_public: list[SpanPublic] = []
    for lilypad_trace in traces:
        traces_public.append(set_display_name_and_convert(lilypad_trace))
    return traces_public


@api.get("/health")
async def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}


api.include_router(project_router)
api.include_router(version_router)
api.include_router(llm_fn_router)
app.mount("/api", api)
app.mount("/", SPAStaticFiles(directory="static", html=True), name="app")
app.mount(
    "/assets", SPAStaticFiles(directory="static/assets", html=True), name="app_assets"
)
