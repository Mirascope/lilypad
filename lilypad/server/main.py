"""Main FastAPI application module for Lilypad."""

from collections.abc import Callable, Sequence
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

from lilypad import configure
from lilypad._trace import trace
from lilypad._utils import load_config, traced_synced_llm_function_constructor
from lilypad.models import (
    AnthropicCallArgsCreate,
    CallArgsCreate,
    CallArgsPublic,
    FnParamsPublic,
    LLMFunctionCreate,
    LLMFunctionPublic,
    OpenAICallArgsCreate,
    ProjectCreate,
    ProjectPublic,
    SpanCreate,
    SpanPublic,
    VersionCreate,
    VersionPublic,
)
from lilypad.server.db.session import get_session
from lilypad.server.models import (
    FnParamsTable,
    LLMFunctionTable,
    ProjectTable,
    Provider,
    Scope,
    SpanTable,
    VersionTable,
)
from lilypad.server.utils import calculate_fn_params_hash

from .services import LLMFunctionService, ProjectService, SpanService, VersionService


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


@api.get("/projects", response_model=Sequence[ProjectTable])
async def get_projects(
    project_service: Annotated[ProjectService, Depends(ProjectService)],
) -> Sequence[ProjectTable]:
    """Get all projects."""
    return project_service.find_all_records()


@api.get("/projects/{project_id}", response_model=ProjectTable)
async def get_project(
    project_id: int,
    project_service: Annotated[ProjectService, Depends(ProjectService)],
) -> ProjectTable:
    """Get a project."""
    return project_service.find_record_by_id(project_id)


@api.post("/projects/", response_model=ProjectPublic)
async def create_project(
    project_create: ProjectCreate,
    project_service: Annotated[ProjectService, Depends(ProjectService)],
) -> ProjectTable:
    """Create a project"""
    return project_service.create_record(project_create)


@api.delete("/projects/{project_id}")
async def delete_project(
    project_id: int,
    project_service: Annotated[ProjectService, Depends(ProjectService)],
) -> None:
    """Create a project"""
    return project_service.delete_record_by_id(project_id)


@api.post(
    "/projects/{project_id}/llm-fns/",
    response_model=LLMFunctionPublic,
)
async def create_llm_functions(
    project_id: int,
    llm_function_create: LLMFunctionCreate,
    llm_fn_service: Annotated[LLMFunctionService, Depends(LLMFunctionService)],
) -> LLMFunctionTable:
    """Get prompt version id by hash."""
    return llm_fn_service.create_record(llm_function_create, project_id=project_id)


@api.get("/projects/{project_id}/llm-fns/{id:int}", response_model=LLMFunctionPublic)
async def get_llm_function_by_id(
    id: int,
    llm_fn_service: Annotated[LLMFunctionService, Depends(LLMFunctionService)],
) -> LLMFunctionTable | None:
    """Get llm function by id."""
    return llm_fn_service.find_record_by_id(id)


@api.get(
    "/projects/{project_id}/llm-fns/{version_hash:str}",
    response_model=LLMFunctionPublic,
)
async def get_llm_function_by_hash(
    version_hash: str,
    llm_fn_service: Annotated[LLMFunctionService, Depends(LLMFunctionService)],
) -> LLMFunctionTable:
    """Get llm function by hash."""
    return llm_fn_service.find_record_by_hash(version_hash)


def create_dynamic_function(
    name: str, args_dict: dict[str, str], return_annotation: type
) -> Callable[..., Any]:
    """Create a dynamic function with the given name, arguments, and return type."""
    arg_list = [f"{arg_name}: {arg_type}" for arg_name, arg_type in args_dict.items()]
    arg_string = ", ".join(arg_list)

    func_def = f"def {name}({arg_string}) -> {return_annotation.__name__}: ..."

    namespace: dict[str, Any] = {}
    exec(func_def, namespace)

    return namespace[name]


# TODO: Getting RuntimeError: asyncio.run() cannot be called from a running event loop
# when running Anthropic calls, but not OpenAI
@api.post("/projects/{project_id}/versions/{version_id}/vibe")
def vibe_check(
    project_id: int,
    version_id: int,
    arg_values: dict[str, Any],
    version_service: Annotated[VersionService, Depends(VersionService)],
) -> str:
    """Check if the vibes are good."""
    version_table = version_service.find_record_by_id(version_id)
    version = VersionPublic.model_validate(version_table)
    args_dict = version.llm_fn.arg_types or {}
    configure()
    # TODO: Check synced or not synced

    # For non-synced, non mirascope functions
    trace_decorator = trace(
        project_id=project_id,
        version_id=version.id,
        arg_types=args_dict,
        arg_values=arg_values,
        lexical_closure=version.llm_fn.code,
        prompt_template=version.fn_params.prompt_template if version.fn_params else "",
        version=version.version,
    )

    fn = create_dynamic_function(
        name=version.llm_fn.function_name,
        args_dict=args_dict,
        return_annotation=str,
    )

    if not version.fn_params:
        return trace_decorator(fn)(**arg_values)  # pyright: ignore [reportReturnType]

    fn_params = FnParamsPublic.model_validate(version.fn_params)

    return traced_synced_llm_function_constructor(fn_params, trace_decorator)(fn)(
        **arg_values
    )  # pyright: ignore [reportReturnType]


@api.get(
    "/projects/{project_id}/versions/{version_id:int}", response_model=VersionPublic
)
def get_version_by_id(
    version_id: int,
    version_service: Annotated[VersionService, Depends(VersionService)],
) -> VersionTable:
    """Get version by ID."""
    return version_service.find_record_by_id(version_id)


class NonSyncedVersionCreate(BaseModel):
    """Non-synced LLM function version create model."""

    llm_function_id: int


@api.post(
    "/projects/{project_id}/versions/{version_hash}",
    response_model=VersionPublic,
)
async def create_non_synced_version(
    project_id: int,
    version_hash: str,
    non_synced_version_create: NonSyncedVersionCreate,
    llm_fn_service: Annotated[LLMFunctionService, Depends(LLMFunctionService)],
    version_service: Annotated[VersionService, Depends(VersionService)],
) -> VersionTable:
    """Creates a new version for a non-synced LLM function."""
    existing_version = version_service.find_non_synced_version_by_hash(
        project_id, version_hash
    )
    if existing_version:
        return existing_version

    llm_fn = llm_fn_service.find_record_by_id(non_synced_version_create.llm_function_id)
    number_of_versions = version_service.get_latest_version_count(
        project_id, llm_fn.function_name
    )
    new_version = VersionCreate(
        project_id=project_id,
        version=number_of_versions + 1,
        function_name=llm_fn.function_name,
        fn_params_id=None,
        llm_function_id=non_synced_version_create.llm_function_id,
        fn_params_hash=None,
        llm_function_hash=llm_fn.version_hash,
    )
    return version_service.create_record(new_version)


@api.get(
    "/projects/{project_id}/versions/{version_hash}",
    response_model=VersionPublic,
)
async def get_non_synced_version(
    project_id: int,
    version_hash: str,
    version_service: Annotated[VersionService, Depends(VersionService)],
) -> VersionTable:
    """Get non-synced version of the function."""
    version = version_service.find_non_synced_version_by_hash(project_id, version_hash)
    if not version:
        raise HTTPException(status_code=404, detail="Non-synced version not found")
    return version


@api.get(
    "/projects/{project_id}/versions/{function_hash}/active",
    response_model=VersionPublic,
)
async def get_active_version(
    project_id: int,
    function_hash: str,
    version_service: Annotated[VersionService, Depends(VersionService)],
) -> VersionTable:
    """Get active version for synced function."""
    return version_service.find_synced_active_version(project_id, function_hash)


@api.patch(
    "/projects/{project_id}/versions/{version_id}/active",
    response_model=VersionPublic,
)
async def set_active_version(
    project_id: int,
    version_id: int,
    version_service: Annotated[VersionService, Depends(VersionService)],
) -> VersionTable:
    """Set active version for synced function."""
    new_active_version = version_service.find_record_by_id(version_id)
    return version_service.change_active_version(project_id, new_active_version)


@api.post(
    "/projects/{project_id}/llm-fns/{llm_function_id}/fn-params",
    response_model=VersionPublic,
)
async def create_version_and_fn_params(
    project_id: int,
    llm_function_id: int,
    call_args_create: CallArgsCreate,
    llm_fn_service: Annotated[LLMFunctionService, Depends(LLMFunctionService)],
    version_service: Annotated[VersionService, Depends(VersionService)],
    session: Annotated[Session, Depends(get_session)],
) -> VersionTable:
    """Create a new version.

    Returns the version if llm function hash and fn params hash already exist.
    Create a new version if the function parameters do not exist.
    Sets active if it is the first prompt template.
    """
    fn_hash = calculate_fn_params_hash(call_args_create)
    fn_params = FnParamsTable.model_validate(
        {
            **call_args_create.model_dump(exclude={"call_params"}),
            "call_params": call_args_create.call_params.model_dump()
            if call_args_create.call_params
            else {},
            "llm_function_id": llm_function_id,
            "hash": fn_hash,
        }
    )

    llm_fn = llm_fn_service.find_record_by_id(llm_function_id)
    # Check if the function parameters already exist
    existing_version = version_service.find_synced_verion_by_hashes(
        llm_fn.version_hash, fn_hash
    )
    if existing_version:
        return existing_version

    # Create a new version
    session.add(fn_params)
    session.flush()
    session.refresh(fn_params)

    # Version to show to the user
    number_of_versions = version_service.get_latest_version_count(
        project_id, llm_fn.function_name
    )
    is_active = version_service.is_first_prompt_template(
        project_id, llm_fn.version_hash
    )
    new_version = VersionCreate(
        project_id=project_id,
        version=number_of_versions + 1,
        function_name=llm_fn.function_name,
        is_active=is_active,
        fn_params_id=fn_params.id,
        llm_function_id=llm_function_id,
        fn_params_hash=fn_params.hash,
        llm_function_hash=fn_params.llm_fn.version_hash,
    )
    return version_service.create_record(new_version)


@api.get(
    "/projects/{project_id}/llm-fns/{id:int}/fn-params",
    response_model=CallArgsPublic,
)
async def get_call_args_from_llm_function_by_id(
    id: int, llm_fn_service: Annotated[LLMFunctionService, Depends(LLMFunctionService)]
) -> CallArgsPublic:
    """Get prompt version id by hash.

    For the ID route, we return the latest version of the function parameters.
    """
    try:
        llm_function = llm_fn_service.find_record_by_id(id)
    except HTTPException:
        return CallArgsPublic(
            id=None,
            model="gpt-4o",
            provider=Provider.OPENAI,
        )
    if not llm_function.fn_params:
        all_llm_functions = llm_fn_service.find_records_by_name(
            llm_function.project_id, llm_function.function_name
        )
        if len(all_llm_functions) == 1:
            return CallArgsPublic(
                id=None,
                model="gpt-4o",
                provider=Provider.OPENAI,
            )
        else:
            second_llm_function = all_llm_functions[-2]
            if not second_llm_function or not second_llm_function.fn_params:
                return CallArgsPublic(
                    id=None,
                    model="gpt-4o",
                    provider=Provider.OPENAI,
                )
            else:
                latest_fn_params = second_llm_function.fn_params[-1]
    else:
        latest_fn_params = llm_function.fn_params[-1]

    if latest_fn_params.provider == Provider.OPENAI:
        call_params = OpenAICallArgsCreate.model_validate(latest_fn_params.call_params)
    elif latest_fn_params.provider == Provider.ANTHROPIC:
        call_params = AnthropicCallArgsCreate.model_validate(
            latest_fn_params.call_params
        )
    else:
        call_params = None

    return CallArgsPublic(
        id=latest_fn_params.id,
        model=latest_fn_params.model,
        provider=latest_fn_params.provider,
        hash=latest_fn_params.hash,
        prompt_template=latest_fn_params.prompt_template,
        call_params=call_params,
    )


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


@api.get("/projects/{project_id}/spans/{span_id}", response_model=SpanPublic)
async def get_span(
    project_id: int,
    span_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> SpanPublic:
    """Get span by id."""
    span = session.exec(
        select(SpanTable).where(
            SpanTable.project_id == project_id,
            SpanTable.id == span_id,
            SpanTable.parent_span_id.is_(None),  # type: ignore
        )
    ).first()
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


app.mount("/api", api)
app.mount("/", SPAStaticFiles(directory="static", html=True), name="app")
app.mount(
    "/assets", SPAStaticFiles(directory="static/assets", html=True), name="app_assets"
)
