"""Tests for the FunctionService class."""

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from lilypad.server.models import FunctionTable, ProjectTable, UserPublic
from lilypad.server.services import FunctionService


def test_find_records_by_name(
    db_session: Session, test_project: ProjectTable, test_user: UserPublic
):
    """Test finding functions by name."""
    service = FunctionService(db_session, test_user)

    functions = [
        FunctionTable(
            organization_uuid=test_project.organization_uuid,
            name="test_func",
            project_id=test_project.id,
            hash=f"hash_{i}",
            code=f"code_{i}",
        )
        for i in range(3)
    ]

    db_session.add_all(functions)
    db_session.commit()

    found_functions = service.find_records_by_name(test_project.id, "test_func")  # pyright: ignore [reportArgumentType]
    assert len(found_functions) == 3
    assert all(func.name == "test_func" for func in found_functions)


def test_find_unique_function_names_by_project_id(
    db_session: Session, test_project: ProjectTable, test_user: UserPublic
):
    """Test finding unique function names by project ID."""
    service = FunctionService(db_session, test_user)

    functions = [
        FunctionTable(
            organization_uuid=test_project.organization_uuid,
            name="func_1",
            project_id=test_project.id,
            hash="hash_1",
            code="code_1",
        ),
        FunctionTable(
            organization_uuid=test_project.organization_uuid,
            name="func_1",  # Duplicate name
            project_id=test_project.id,
            hash="hash_2",
            code="code_2",
        ),
        FunctionTable(
            organization_uuid=test_project.organization_uuid,
            name="func_2",
            project_id=test_project.id,
            hash="hash_3",
            code="code_3",
        ),
    ]

    db_session.add_all(functions)
    db_session.commit()

    unique_names = service.find_unique_function_names_by_project_id(test_project.id)  # pyright: ignore [reportArgumentType]
    assert len(unique_names) == 2
    assert set(unique_names) == {"func_1", "func_2"}


def test_find_record_by_hash(
    db_session: Session, test_project: ProjectTable, test_user: UserPublic
):
    """Test finding function by hash."""
    service = FunctionService(db_session, test_user)

    function = FunctionTable(
        organization_uuid=test_project.organization_uuid,
        name="test_func",
        project_id=test_project.id,
        hash="test_hash",
        code="test_code",
    )

    db_session.add(function)
    db_session.commit()

    found_function = service.find_record_by_hash("test_hash")
    assert found_function.hash == "test_hash"
    assert found_function.name == "test_func"


def test_find_record_by_hash_not_found(db_session: Session, test_user: UserPublic):
    """Test finding non-existent function by hash."""
    service = FunctionService(db_session, test_user)

    with pytest.raises(HTTPException):
        service.find_record_by_hash("nonexistent_hash")
