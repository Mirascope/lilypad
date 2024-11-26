"""Tests for prompt service"""

import pytest
from sqlmodel import Session

from lilypad.server.models import (
    OpenAICallParams,
    ProjectTable,
    PromptCreate,
    PromptTable,
    Provider,
    ResponseFormat,
)
from lilypad.server.services import PromptService


@pytest.fixture
def test_project(db_session: Session) -> ProjectTable:
    """Create test project"""
    project = ProjectTable(name="Test Project")
    db_session.add(project)
    db_session.commit()
    return project


def test_create_prompt(db_session: Session, test_project: ProjectTable):
    """Test creating a prompt"""
    service = PromptService(db_session)
    prompt_create = PromptCreate(
        project_id=test_project.id,
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


def test_find_prompt_by_call_params(db_session: Session, test_project: ProjectTable):
    """Test finding prompt by call params"""
    service = PromptService(db_session)

    # Create OpenAICallParams first and convert to dict
    call_params = OpenAICallParams(
        max_tokens=100,
        temperature=0.7,
        top_p=1,
        response_format=ResponseFormat(type="text"),
    ).model_dump()

    prompt = PromptTable(
        project_id=test_project.id,
        hash="test_hash",
        template="test template",
        provider=Provider.OPENAI,
        model="gpt-4",
        call_params=call_params,
    )
    db_session.add(prompt)
    db_session.commit()

    prompt_create = PromptCreate(
        project_id=test_project.id,
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
    db_session: Session, test_project: ProjectTable
):
    """Test finding non-existent prompt by call params"""
    service = PromptService(db_session)
    prompt_create = PromptCreate(
        project_id=test_project.id,
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
