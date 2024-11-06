"""Version API."""

from collections.abc import Callable, Sequence
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from mirascope.integrations import middleware_factory
from pydantic import BaseModel

from lilypad import configure
from lilypad._trace import trace
from lilypad._utils import (
    get_custom_context_manager,
    handle_call_response,
    handle_call_response_async,
    handle_response_model,
    handle_response_model_async,
    handle_stream,
    handle_stream_async,
    handle_structured_stream,
    handle_structured_stream_async,
    traced_synced_llm_function_constructor,
)
from lilypad.models import (
    FnParamsPublic,
    VersionCreate,
    VersionPublic,
)
from lilypad.server.models import VersionTable
from lilypad.server.services import LLMFunctionService, VersionService

version_router = APIRouter()


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
@version_router.post("/projects/{project_id}/versions/{version_id}/vibe")
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
    arg_types = version.llm_fn.arg_types or {}
    prompt_template = version.fn_params.prompt_template if version.fn_params else ""
    decorator = middleware_factory(
        custom_context_manager=get_custom_context_manager(
            version, arg_types, arg_values, False, prompt_template
        ),
        handle_call_response=handle_call_response,
        handle_call_response_async=handle_call_response_async,
        handle_stream=handle_stream,
        handle_stream_async=handle_stream_async,
        handle_response_model=handle_response_model,
        handle_response_model_async=handle_response_model_async,
        handle_structured_stream=handle_structured_stream,
        handle_structured_stream_async=handle_structured_stream_async,
    )
    fn_params = FnParamsPublic.model_validate(version.fn_params)

    return traced_synced_llm_function_constructor(fn_params, decorator)(fn)(
        **arg_values
    )  # pyright: ignore [reportReturnType]


@version_router.get(
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


@version_router.post(
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


@version_router.get(
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Non-synced version not found"
        )
    return version


@version_router.get(
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


@version_router.patch(
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
