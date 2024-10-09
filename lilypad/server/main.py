"""Main FastAPI application module for Lilypad."""

import json
from collections.abc import Sequence
from typing import Annotated, Any

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

from lilypad.models import (
    CallArgsPublic,
    LLMFunctionBasePublic,
    ProjectCreate,
    ProjectPublic,
    SpanPublic,
)
from lilypad.server.db.session import get_session
from lilypad.server.models import (
    FnParamsTable,
    LLMFunctionTable,
    ProjectTable,
    Provider,
    Scope,
    SpanTable,
)


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
    print(request, exc)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


origins = [
    "http://localhost:5173",
    "http://localhost:8000/*",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
api = FastAPI()


@api.get("/projects", response_model=Sequence[ProjectTable])
async def get_projects(
    session: Annotated[Session, Depends(get_session)],
) -> Sequence[ProjectTable]:
    """Get all projects."""
    projects = session.exec(select(ProjectTable)).all()
    return projects


@api.get("/projects/{project_id}", response_model=ProjectTable)
async def get_project(
    project_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> ProjectTable:
    """Get all projects."""
    project = session.exec(
        select(ProjectTable).where(ProjectTable.id == project_id)
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@api.post("/projects/", response_model=ProjectPublic)
async def create_project(
    project_create: ProjectCreate,
    session: Annotated[Session, Depends(get_session)],
) -> ProjectTable:
    """Create a project"""
    project = ProjectTable.model_validate(project_create)
    session.add(project)
    session.commit()
    session.flush()
    return project


@api.get(
    "/projects/{project_id}/llm-fns",
    response_model=Sequence[LLMFunctionTable],
)
async def get_code_by_function_name(
    function_name: str,
    session: Annotated[Session, Depends(get_session)],
) -> Sequence[LLMFunctionTable]:
    """Get prompt version id by hash."""
    "HITHIT"
    llm_functions = session.exec(
        select(LLMFunctionTable).where(LLMFunctionTable.function_name == function_name)
    ).all()
    return llm_functions


class LLMFunctionCreate(BaseModel):
    """LLM function create model."""

    function_name: str
    code: str
    version_hash: str
    input_arguments: str | None = None


@api.post(
    "/projects/{project_id}/llm-fns/",
    response_model=LLMFunctionBasePublic,
)
async def create_llm_functions(
    project_id: int,
    llm_function_create: LLMFunctionCreate,
    session: Annotated[Session, Depends(get_session)],
) -> LLMFunctionTable:
    """Get prompt version id by hash."""
    llm_function = LLMFunctionTable.model_validate(
        {
            **llm_function_create.model_dump(),
            "project_id": project_id,
        }
    )
    session.add(llm_function)
    session.commit()
    session.refresh(llm_function)
    return llm_function


@api.get(
    "/projects/{project_id}/llm-fns/{id:int}", response_model=LLMFunctionBasePublic
)
async def get_llm_function_by_id(
    id: int,
    session: Annotated[Session, Depends(get_session)],
) -> LLMFunctionTable | None:
    """Get llm function by hash."""
    llm_function = session.exec(
        select(LLMFunctionTable).where(LLMFunctionTable.id == id)
    ).first()
    if not llm_function:
        raise HTTPException(status_code=404, detail="LLM function not found")
    return llm_function if llm_function else None


@api.get(
    "/projects/{project_id}/llm-fns/{version_hash:str}",
    response_model=LLMFunctionBasePublic,
)
async def get_llm_function_id_by_hash(
    version_hash: str,
    session: Annotated[Session, Depends(get_session)],
) -> LLMFunctionTable | None:
    """Get llm function by hash."""
    llm_function = session.exec(
        select(LLMFunctionTable).where(LLMFunctionTable.version_hash == version_hash)
    ).first()
    if not llm_function:
        raise HTTPException(status_code=404, detail="LLM function not found")
    return llm_function if llm_function else None


class CallArgsCreate(BaseModel):
    """Call args model."""

    model: str
    provider: Provider
    prompt_template: str
    editor_state: str
    call_params: dict[str, Any] | None


@api.post(
    "/projects/{project_id}/llm-fns/{llm_function_id}/fn-params",
    response_model=FnParamsTable,
)
async def create_fn_params(
    llm_function_id: int,
    call_args_create: CallArgsCreate,
    session: Annotated[Session, Depends(get_session)],
) -> FnParamsTable:
    """Create function call params."""
    fn_params_create = {
        **call_args_create.model_dump(exclude={"call_params"}),
        "call_params": json.dumps(call_args_create.call_params),
        "llm_function_id": llm_function_id,
    }
    fn_params = FnParamsTable.model_validate(fn_params_create)
    session.add(fn_params)
    session.commit()
    session.refresh(fn_params)
    return fn_params


@api.get(
    "/projects/{project_id}/llm-fns/{id:int}/fn-params",
    response_model=CallArgsPublic,
)
async def get_call_args_from_llm_function_by_id(
    id: int,
    session: Annotated[Session, Depends(get_session)],
) -> CallArgsPublic:
    """Get prompt version id by hash.

    For the ID route, we return the latest version of the function parameters.
    """
    # TODO: Clean up this function
    llm_function = session.exec(
        select(LLMFunctionTable).where(LLMFunctionTable.id == id)
    ).first()
    if not llm_function:
        return CallArgsPublic(
            id=None,
            model="gpt-4o",
            provider=Provider.OPENAI,
            prompt_template="",
            editor_state="",
            call_params={},
        )
    elif not llm_function.fn_params:
        all_llm_functions = session.exec(
            select(LLMFunctionTable).where(
                LLMFunctionTable.function_name == llm_function.function_name
            )
        ).all()
        if len(all_llm_functions) == 1:
            return CallArgsPublic(
                id=None,
                model="gpt-4o",
                provider=Provider.OPENAI,
                prompt_template="",
                editor_state="",
                call_params={},
            )
        else:
            second_llm_function = all_llm_functions[-2]
            if not second_llm_function or not second_llm_function.fn_params:
                return CallArgsPublic(
                    id=None,
                    model="gpt-4o",
                    provider=Provider.OPENAI,
                    prompt_template="",
                    editor_state="",
                    call_params={},
                )
            else:
                latest_fn_params = second_llm_function.fn_params[-1]
    else:
        latest_fn_params = llm_function.fn_params[-1]
    return CallArgsPublic(
        id=latest_fn_params.id,
        model=latest_fn_params.model,
        provider=latest_fn_params.provider,
        prompt_template=latest_fn_params.prompt_template,
        editor_state=latest_fn_params.editor_state,
        call_params=json.loads(latest_fn_params.call_params)
        if latest_fn_params.call_params
        else {},
    )


@api.get(
    "/projects/{project_id}/llm-fns/{version_hash:str}/fn-params",
    response_model=CallArgsPublic,
)
async def get_call_args_from_llm_function_by_hash(
    version_hash: str,
    session: Annotated[Session, Depends(get_session)],
) -> CallArgsPublic:
    """Get prompt version id by hash.

    For the hash route, DO NOT return the latest function params.
    """
    llm_function = session.exec(
        select(LLMFunctionTable).where(LLMFunctionTable.version_hash == version_hash)
    ).first()
    if not llm_function or not llm_function.fn_params:
        raise HTTPException(status_code=404, detail="LLM function not found")
    latest_fn_params = llm_function.fn_params[-1]
    return CallArgsPublic(
        id=latest_fn_params.id,
        model=latest_fn_params.model,
        provider=latest_fn_params.provider,
        prompt_template=latest_fn_params.prompt_template,
        editor_state=latest_fn_params.editor_state,
        call_params=json.loads(latest_fn_params.call_params)
        if latest_fn_params.call_params
        else {},
    )


@api.post("/v1/metrics")
async def metrics(request: Request) -> None:
    json = await request.json()


@api.post("/v1/traces")
async def traces(
    request: Request, session: Annotated[Session, Depends(get_session)]
) -> list[SpanPublic]:
    """Create span traces."""
    traces_json: list[dict] = await request.json()
    span_tables: list[SpanTable] = []
    for trace in traces_json:
        version = None
        if trace["instrumentation_scope"]["name"] == "lilypad":
            scope = Scope.LILYPAD
            if llm_function_id := trace.get("attributes", {}).get(
                "lilypad.llm_function_id", None
            ):
                span_llm_function = session.exec(
                    select(LLMFunctionTable).where(
                        LLMFunctionTable.id == llm_function_id
                    )
                ).first()
                if not span_llm_function:
                    raise HTTPException(
                        status_code=404, detail="LLM function not found"
                    )

                llm_functions = session.exec(
                    select(LLMFunctionTable).where(
                        LLMFunctionTable.function_name
                        == span_llm_function.function_name
                    )
                ).all()
                version = 1
                for llm_function in llm_functions:
                    for fn_params in llm_function.fn_params:
                        if span_llm_function.fn_params[-1].id == fn_params.id:
                            break
                        else:
                            version += 1

        else:
            scope = Scope.LLM
        # TODO: Optimize
        span_table = SpanTable(
            id=trace["span_id"],
            version=version or None,
            parent_span_id=trace.get("parent_span_id", None),
            data=json.dumps(trace),
            scope=scope,
            llm_function_id=trace.get("attributes", {}).get(
                "lilypad.llm_function_id", None
            ),
        )
        span_tables.append(span_table)
        session.add(span_table)
    session.commit()
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
    if span.scope == Scope.LILYPAD:
        display_name = span.llm_fn.function_name if span.llm_fn else None
    elif span.scope == Scope.LLM:
        data = json.loads(span.data)
        display_name = f"{data['attributes']['gen_ai.system']} with '{data['attributes']['gen_ai.request.model']}'"
    else:
        display_name = "Unknown"

    span_public = SpanPublic.model_validate(span)
    span_public.display_name = display_name

    span_public.child_spans = [
        set_display_name_and_convert(child_span) for child_span in span.child_spans
    ]

    return span_public


@api.get("/traces", response_model=Sequence[SpanPublic])
async def get_traces(
    session: Annotated[Session, Depends(get_session)],
) -> Sequence[SpanPublic]:
    """Get all traces"""
    traces = session.exec(
        select(SpanTable).where(SpanTable.parent_span_id.is_(None))  # type: ignore
    ).all()
    traces_public: list[SpanPublic] = []
    for trace in traces:
        traces_public.append(set_display_name_and_convert(trace))
    return traces_public


@api.get("/health")
async def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}


app.mount("/api", api)
app.mount("/", SPAStaticFiles(directory="static", html=True), name="app")
app.mount(
    "/assets", SPAStaticFiles(directory="static/assets", html=True), name="app_assets"
)
