"""Tests for functions service."""

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from lilypad.server.models.functions import FunctionTable
from lilypad.server.models.projects import ProjectTable
from lilypad.server.services.functions import FunctionService


@pytest.fixture
def test_function(db_session: Session, test_project: ProjectTable) -> FunctionTable:
    """Create a test function."""
    function = FunctionTable(
        project_uuid=test_project.uuid,
        organization_uuid=test_project.organization_uuid,
        name="test_function",
        version_num=1,
        hash="test_hash",
        signature="test_signature",
        code="def test_function(name: str): return f'Hello {name}'",
        prompt_template="Hello {name}",
        call_params={"temperature": 0.7},
        arg_types={"name": "str"},
        provider="openai",
        model="gpt-4",
    )
    db_session.add(function)
    db_session.commit()
    db_session.refresh(function)
    return function


def test_find_functions_by_version_not_found(
    db_session: Session, test_user, test_project: ProjectTable
):
    """Test find_functions_by_version when function is not found."""
    function_service = FunctionService(session=db_session, user=test_user)

    # Try to find a function that doesn't exist
    with pytest.raises(HTTPException) as exc_info:
        function_service.find_functions_by_version(
            test_project.uuid, "nonexistent_function", 1
        )

    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail


def test_find_functions_by_signature(
    db_session: Session,
    test_user,
    test_project: ProjectTable,
    test_function: FunctionTable,
):
    """Test find_functions_by_signature method."""
    function_service = FunctionService(session=db_session, user=test_user)

    # Find functions by signature
    functions = function_service.find_functions_by_signature(
        test_project.uuid, test_function.signature
    )

    assert len(functions) == 1
    assert functions[0].uuid == test_function.uuid
    assert functions[0].signature == test_function.signature


def test_find_functions_by_signature_empty(
    db_session: Session, test_user, test_project: ProjectTable
):
    """Test find_functions_by_signature when no functions match."""
    function_service = FunctionService(session=db_session, user=test_user)

    # Try to find functions with a signature that doesn't exist
    functions = function_service.find_functions_by_signature(
        test_project.uuid, "nonexistent_signature"
    )

    assert len(functions) == 0


def test_get_functions_by_name_desc_created_at(
    db_session: Session,
    test_user,
    test_project: ProjectTable,
    test_function: FunctionTable,
):
    """Test get_functions_by_name_desc_created_at method."""
    function_service = FunctionService(session=db_session, user=test_user)

    # Create another function with the same name but later version
    function2 = FunctionTable(
        project_uuid=test_project.uuid,
        organization_uuid=test_project.organization_uuid,
        name=test_function.name,
        version_num=2,
        hash="test_hash_2",
        signature="test_signature_2",
        code="def test_function_v2(name: str): return f'Hello {name} v2'",
        prompt_template="Hello {name} v2",
        call_params={"temperature": 0.8},
        arg_types={"name": "str"},
        provider="openai",
        model="gpt-4",
    )
    db_session.add(function2)
    db_session.commit()
    db_session.refresh(function2)

    # Get functions by name ordered by created_at descending
    functions = function_service.get_functions_by_name_desc_created_at(
        test_project.uuid, test_function.name
    )

    assert len(functions) == 2
    # Should be ordered by created_at descending, then version_num ascending
    # Since function2 was created later, it should come first
    assert functions[0].uuid == function2.uuid
    assert functions[1].uuid == test_function.uuid


def test_get_functions_by_name_desc_created_at_empty(
    db_session: Session, test_user, test_project: ProjectTable
):
    """Test get_functions_by_name_desc_created_at when no functions match."""
    function_service = FunctionService(session=db_session, user=test_user)

    # Try to find functions with a name that doesn't exist
    functions = function_service.get_functions_by_name_desc_created_at(
        test_project.uuid, "nonexistent_function"
    )

    assert len(functions) == 0
