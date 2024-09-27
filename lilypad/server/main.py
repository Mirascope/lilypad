"""Main FastAPI application module for Lilypad."""

import json
from typing import Annotated, Any, Sequence

from fastapi import Depends, FastAPI, Form, Header, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from google.protobuf.json_format import MessageToJson
from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import (
    ExportMetricsServiceRequest,
)
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
    ExportTraceServiceRequest,
)
from pydantic import BaseModel, TypeAdapter
from sqlmodel import Session, select

from lilypad.server.db.session import get_session
from lilypad.server.models import (
    CallBase,
    CallTable,
    ProjectTable,
    PromptVersionBase,
    PromptVersionTable,
    Scope,
    SpanBase,
    SpanTable,
)

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation exceptions."""
    print(request, exc)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory="templates")
api = FastAPI()


class PromptVersionPublic(PromptVersionBase):
    """Prompt Version public model."""

    id: int


@api.get("/prompt-versions")
async def get_prompt_versions(
    session: Annotated[Session, Depends(get_session)],
) -> Sequence[str]:
    """Get prompt version unique function names by hash."""
    function_names = session.exec(
        select(PromptVersionTable.function_name).distinct()
    ).all()
    return function_names


@api.get(
    "/prompt-versions/function_names/{function_name}",
    response_model=Sequence[PromptVersionPublic],
)
async def get_prompt_versions_by_function_name(
    function_name: str,
    session: Annotated[Session, Depends(get_session)],
) -> Sequence[PromptVersionTable]:
    """Get prompt version id by hash."""
    prompt_versions = session.exec(
        select(PromptVersionTable).where(
            PromptVersionTable.function_name == function_name
        )
    ).all()
    # Stainless does not handle `int | None` return types properly
    return prompt_versions


@api.get("/prompt-versions/{version_hash}")
async def get_prompt_version_id_by_hash(
    version_hash: str,
    session: Annotated[Session, Depends(get_session)],
) -> int:
    """Get prompt version id by hash."""
    prompt_version = session.exec(
        select(PromptVersionTable).where(
            PromptVersionTable.version_hash == version_hash
        )
    ).first()
    # Stainless does not handle `int | None` return types properly
    return (
        PromptVersionPublic.model_validate(prompt_version).id if prompt_version else -1
    )


@api.post(
    "/prompt-versions",
    response_model=PromptVersionPublic,
)
async def create_prompt_version(
    prompt_version_create: PromptVersionBase,
    session: Annotated[Session, Depends(get_session)],
) -> PromptVersionTable:
    """Creates a prompt version."""
    prompt_version = PromptVersionTable.model_validate(prompt_version_create)
    session.add(prompt_version)
    session.commit()
    session.refresh(prompt_version)
    return prompt_version


class CallPublicWithPromptVersion(CallBase):
    """Call public model with prompt version."""

    id: int
    prompt_version: PromptVersionPublic


@api.get("/calls", response_model=Sequence[CallPublicWithPromptVersion])
async def get_calls(
    session: Annotated[Session, Depends(get_session)],
) -> Sequence[CallTable]:
    """Creates a logged call."""
    call_tables = session.exec(select(CallTable)).all()
    return call_tables


@api.post("/calls")
async def create_calls(
    session: Annotated[Session, Depends(get_session)], call_create: CallBase
) -> CallTable:
    """Creates a logged call."""
    call = CallTable.model_validate(call_create)
    session.add(call)
    session.commit()
    session.refresh(call)
    return call


@api.post("/v1/metrics")
async def metrics(request: Request) -> None:
    print("METRICS")
    json = await request.json()
    print(json)


@api.post("/v1/traces")
async def traces(
    request: Request, session: Annotated[Session, Depends(get_session)]
) -> None:
    traces_json: list[dict] = await request.json()
    for trace in traces_json:
        if trace["instrumentation_scope"]["name"] == "lilypad":
            scope = Scope.LILYPAD
        else:
            scope = Scope.LLM
        span_table = SpanTable(
            id=trace["span_id"],
            parent_span_id=trace.get("parent_span_id", None),
            data=json.dumps(trace),
            scope=scope,
            prompt_version_id=trace.get("attributes", {}).get(
                "lilypad.prompt_version_id", None
            ),
        )
        session.add(span_table)
    session.commit()


class SpanPublic(SpanBase):
    """Call public model with prompt version."""

    id: str
    display_name: str | None = None
    prompt_version: PromptVersionPublic | None
    child_spans: list["SpanPublic"]


@api.get("/traces", response_model=Sequence[SpanPublic])
async def get_traces(
    session: Annotated[Session, Depends(get_session)],
) -> Sequence[SpanPublic]:
    """Get all traces"""
    traces = session.exec(
        select(SpanTable).where(SpanTable.parent_span_id.is_(None))  # type: ignore
    ).all()
    traces_public = TypeAdapter(list[SpanPublic]).validate_python(traces)
    for trace in traces_public:
        trace.display_name = (
            trace.prompt_version.function_name if trace.prompt_version else None
        )
        child_traces_public = TypeAdapter(list[SpanPublic]).validate_python(
            trace.child_spans
        )
        for child_trace in child_traces_public:
            data = json.loads(child_trace.data)
            child_trace.display_name = f"{data['attributes']['gen_ai.system']} with '{data['attributes']['gen_ai.request.model']}'"
    print(traces_public)
    return traces_public


app.mount("/api", api)
