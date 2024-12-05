"""Tests for prompt service"""

from sqlmodel import Session

from lilypad.server.models import (
    OpenAICallParams,
    ProjectTable,
    PromptCreate,
    PromptTable,
    Provider,
    ResponseFormat,
    UserPublic,
)
from lilypad.server.services import PromptService


def test_create_prompt(
    db_session: Session, test_project: ProjectTable, test_user: UserPublic
):
    """Test creating a prompt"""
    service = PromptService(db_session, test_user)
    prompt_create = PromptCreate(
        project_uuid=test_project.uuid,
        hash="test_hash",
        template="test template",
        provider=Provider.OPENAI,
        model="gpt-4",
        call_params=OpenAICallParams(
            max_tokens=100,
            temperature=0.7,
            top_p=1,
            response_format=ResponseFormat(type="text"),
        ),
    )

    prompt = service.create_record(prompt_create)
    assert prompt.template == "test template"
    assert prompt.provider == Provider.OPENAI
    assert prompt.model == "gpt-4"
    assert prompt.call_params["max_tokens"] == 100  # pyright: ignore [reportOptionalSubscript]


def test_find_prompt_by_call_params(
    db_session: Session, test_project: ProjectTable, test_user: UserPublic
):
    """Test finding prompt by call params"""
    service = PromptService(db_session, test_user)

    # Create OpenAICallParams first and convert to dict
    call_params = OpenAICallParams(
        max_tokens=100,
        temperature=0.7,
        top_p=1,
        response_format=ResponseFormat(type="text"),
    ).model_dump()

    prompt = PromptTable(
        organization_uuid=test_project.organization_uuid,
        project_uuid=test_project.uuid,
        hash="test_hash",
        template="test template",
        provider=Provider.OPENAI,
        model="gpt-4",
        call_params=call_params,
    )
    db_session.add(prompt)
    db_session.commit()

    prompt_create = PromptCreate(
        project_uuid=test_project.uuid,
        hash="test_hash",
        template="test template",
        provider=Provider.OPENAI,
        model="gpt-4",
        call_params=OpenAICallParams(
            max_tokens=100,
            temperature=0.7,
            top_p=1,
            response_format=ResponseFormat(type="text"),
        ),
    )

    found_prompt = service.find_prompt_by_call_params(prompt_create)
    assert found_prompt is not None
    assert found_prompt.hash == "test_hash"
    assert found_prompt.call_params == call_params


def test_find_prompt_by_call_params_not_found(
    db_session: Session, test_project: ProjectTable, test_user: UserPublic
):
    """Test finding non-existent prompt by call params"""
    service = PromptService(db_session, test_user)
    prompt_create = PromptCreate(
        project_uuid=test_project.uuid,
        hash="nonexistent_hash",
        template="test template",
        provider=Provider.OPENAI,
        model="gpt-4",
        call_params=OpenAICallParams(
            max_tokens=100,
            temperature=0.7,
            top_p=1,
            response_format=ResponseFormat(type="text"),
        ),
    )

    found_prompt = service.find_prompt_by_call_params(prompt_create)
    assert found_prompt is None
