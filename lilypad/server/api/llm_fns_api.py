"""LLM Functions API."""

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from lilypad.models import (
    AnthropicCallArgsCreate,
    CallArgsCreate,
    CallArgsPublic,
    LLMFunctionCreate,
    LLMFunctionPublic,
    OpenAICallArgsCreate,
    VersionCreate,
    VersionPublic,
)
from lilypad.server.db.session import get_session
from lilypad.server.models import (
    FnParamsTable,
    LLMFunctionTable,
    Provider,
    VersionTable,
)
from lilypad.server.services import LLMFunctionService, VersionService
from lilypad.server.utils import calculate_fn_params_hash

llm_fn_router = APIRouter()


@llm_fn_router.post(
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


@llm_fn_router.get(
    "/projects/{project_id}/llm-fns/{id:int}", response_model=LLMFunctionPublic
)
async def get_llm_function_by_id(
    id: int,
    llm_fn_service: Annotated[LLMFunctionService, Depends(LLMFunctionService)],
) -> LLMFunctionTable | None:
    """Get llm function by id."""
    return llm_fn_service.find_record_by_id(id)


@llm_fn_router.get(
    "/projects/{project_id}/llm-fns/{version_hash:str}",
    response_model=LLMFunctionPublic,
)
async def get_llm_function_by_hash(
    version_hash: str,
    llm_fn_service: Annotated[LLMFunctionService, Depends(LLMFunctionService)],
) -> LLMFunctionTable:
    """Get llm function by hash."""
    return llm_fn_service.find_record_by_hash(version_hash)


@llm_fn_router.get(
    "/projects/{project_id}/llm-fns/{function_name}/versions",
    response_model=Sequence[VersionPublic],
)
def get_versions_by_function_name(
    project_id: int,
    function_name: str,
    version_service: Annotated[VersionService, Depends(VersionService)],
) -> Sequence[VersionTable]:
    """Get version by function name."""
    return version_service.find_versions_by_function_name(project_id, function_name)


@llm_fn_router.post(
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


@llm_fn_router.get(
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
