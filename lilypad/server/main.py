"""Main FastAPI application module for Lilypad."""

import json
from typing import Annotated, Any, Sequence

from fastapi import Depends, FastAPI, Form, Header, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, TypeAdapter
from sqlmodel import Session, SQLModel, select
from starlette.exceptions import HTTPException as StarletteHTTPException

from lilypad.server.db.session import get_session
from lilypad.server.models import (
    LLMFunctionBase,
    Provider,
    Scope,
    SpanBase,
    SpanTable,
    llm_functions,
)
from lilypad.server.models.llm_functions import LLMFunctionTable
from lilypad.server.models.provider_call_params import ProviderCallParamsTable


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except (HTTPException, StarletteHTTPException) as ex:
            if ex.status_code == 404:
                return await super().get_response("index.html", scope)
            else:
                raise ex


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
templates = Jinja2Templates(directory="templates")
api = FastAPI()


@api.get("/llm-functions/names")
async def get_llm_function_names(
    session: Annotated[Session, Depends(get_session)],
) -> Sequence[str]:
    """Get llm function names by hash."""
    function_names = session.exec(
        select(LLMFunctionTable.function_name).distinct()
    ).all()
    return function_names


@api.get(
    "/llm-functions",
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


class LLMFunctionBasePublic(LLMFunctionBase):
    """LLM function base public model"""

    id: int
    provider_call_params: list[ProviderCallParamsTable] | None


@api.post(
    "/llm-functions/",
    response_model=LLMFunctionBasePublic,
)
async def create_llm_functions(
    llm_function_create: LLMFunctionCreate,
    session: Annotated[Session, Depends(get_session)],
) -> LLMFunctionTable:
    """Get prompt version id by hash."""
    llm_function = LLMFunctionTable.model_validate(llm_function_create)
    session.add(llm_function)
    session.commit()
    session.refresh(llm_function)
    return llm_function


@api.get("/llm-functions/{id:int}", response_model=LLMFunctionBasePublic)
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


@api.get("/llm-functions/{version_hash:str}", response_model=LLMFunctionBasePublic)
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
    call_params: dict[str, Any] | None


@api.post(
    "/llm-functions/{llm_function_id}/provider-call-params",
    response_model=ProviderCallParamsTable,
)
async def create_provider_call_params(
    llm_function_id: int,
    call_args_create: CallArgsCreate,
    session: Annotated[Session, Depends(get_session)],
) -> ProviderCallParamsTable:
    """Creates a provider call params."""
    provider_call_params_create = {
        **call_args_create.model_dump(exclude={"call_params"}),
        "call_params": json.dumps(call_args_create.call_params),
        "llm_function_id": llm_function_id,
    }
    provider_call_params = ProviderCallParamsTable.model_validate(
        provider_call_params_create
    )
    session.add(provider_call_params)
    session.commit()
    session.refresh(provider_call_params)
    return provider_call_params


class CallArgsPublic(BaseModel):
    """Call args model."""

    model: str
    provider: Provider
    prompt_template: str
    call_params: dict[str, Any] | None


@api.get(
    "/llm-functions/{id:int}/provider-call-params",
    response_model=CallArgsPublic,
)
async def get_call_args_from_llm_function_by_id(
    id: int,
    session: Annotated[Session, Depends(get_session)],
) -> CallArgsPublic:
    """Get prompt version id by hash."""
    llm_function = session.exec(
        select(LLMFunctionTable).where(LLMFunctionTable.id == id)
    ).first()
    if not llm_function or not llm_function.provider_call_params:
        return CallArgsPublic(
            model="gpt-4o",
            provider=Provider.OPENAI,
            prompt_template="",
            call_params={},
        )
    latest_provider_call_params = llm_function.provider_call_params[-1]
    return CallArgsPublic(
        model=latest_provider_call_params.model,
        provider=latest_provider_call_params.provider,
        prompt_template=latest_provider_call_params.prompt_template,
        call_params=json.loads(latest_provider_call_params.call_params)
        if latest_provider_call_params.call_params
        else {},
    )


@api.get(
    "/llm-functions/{version_hash:str}/provider-call-params",
    response_model=CallArgsPublic,
)
async def get_call_args_from_llm_function_by_hash(
    version_hash: str,
    session: Annotated[Session, Depends(get_session)],
) -> CallArgsPublic:
    """Get prompt version id by hash."""
    llm_function = session.exec(
        select(LLMFunctionTable).where(LLMFunctionTable.version_hash == version_hash)
    ).first()
    if not llm_function or not llm_function.provider_call_params:
        raise HTTPException(status_code=404, detail="LLM function not found")
    latest_provider_call_params = llm_function.provider_call_params[-1]
    return CallArgsPublic(
        model=latest_provider_call_params.model,
        provider=latest_provider_call_params.provider,
        prompt_template=latest_provider_call_params.prompt_template,
        call_params=json.loads(latest_provider_call_params.call_params)
        if latest_provider_call_params.call_params
        else {},
    )


# @api.get("/prompt-versions/{version_hash}/latest", response_model=CallArgs)
# async def get_call_args_from_prompt_version(
#     version_hash: str,
#     session: Annotated[Session, Depends(get_session)],
# ) -> CallArgs:
#     """Get prompt version id by hash."""
#     prompt_version = session.exec(
#         select(PromptVersionTable).where(
#             PromptVersionTable.version_hash == version_hash
#         )
#     ).first()
#     if not prompt_version:
#         raise HTTPException(status_code=404, detail="Prompt version not found")
#     return CallArgs(
#         model="openai",
#         json_mode=False,
#         provider=Provider.OPENAI,
#         prompt_template=prompt_version.prompt_template,
#         call_params={},
#     )


class PromptVersionUpdate(SQLModel):
    """Patch prompt version model"""

    prompt_template: str | None = None
    input_arguments: str | None = None


# @api.patch(
#     "/prompt-versions/{prompt_version_id}",
#     response_model=PromptVersionPublic,
# )
# async def patch_prompt_version(
#     prompt_version_id: int,
#     prompt_version_create: PromptVersionUpdate,
#     session: Annotated[Session, Depends(get_session)],
# ) -> PromptVersionTable:
#     """Creates a prompt version."""
#     prompt_version = session.exec(
#         select(PromptVersionTable).where(PromptVersionTable.id == prompt_version_id)
#     ).first()
#     if not prompt_version:
#         raise HTTPException(status_code=404, detail="Prompt version not found")
#     new_prompt_version_data = prompt_version_create.model_dump(exclude_unset=True)
#     for key, value in new_prompt_version_data.items():
#         setattr(prompt_version, key, value)
#     session.add(prompt_version)
#     session.commit()
#     session.refresh(prompt_version)
#     return prompt_version


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
            llm_function_id=trace.get("attributes", {}).get(
                "lilypad.llm_function_id", None
            ),
        )
        session.add(span_table)
    session.commit()


class SpanPublic(SpanBase):
    """Call public model with prompt version."""

    id: str
    display_name: str | None = None
    llm_function: LLMFunctionTable | None = None
    child_spans: list["SpanPublic"]


def set_display_name_and_convert(
    span: SpanTable,
) -> SpanPublic:
    # Compute the display_name based on your custom logic
    if span.scope == Scope.LILYPAD:
        display_name = span.llm_function.function_name if span.llm_function else None
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


app.mount("/api", api)
app.mount("/lilypad", SPAStaticFiles(directory="dist", html=True), name="lilypad")
