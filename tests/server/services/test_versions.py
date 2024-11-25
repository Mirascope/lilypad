"""Tests for version service"""

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from lilypad.server.models import (
    FunctionTable,
    ProjectTable,
    PromptTable,
    Provider,
    VersionTable,
)
from lilypad.server.services import VersionService


@pytest.fixture
def test_project(db_session: Session) -> ProjectTable:
    """Create test project"""
    project = ProjectTable(name="Test Project")
    db_session.add(project)
    db_session.commit()
    return project


@pytest.fixture
def test_function(db_session: Session, test_project: ProjectTable) -> FunctionTable:
    """Create test function"""
    function = FunctionTable(
        name="test_func", project_id=test_project.id, hash="test_hash", code="test_code"
    )
    db_session.add(function)
    db_session.commit()
    return function


@pytest.fixture
def test_prompt(db_session: Session, test_project: ProjectTable) -> PromptTable:
    """Create test prompt"""
    prompt = PromptTable(
        project_id=test_project.id,
        hash="test_prompt_hash",
        template="test template",
        provider=Provider.OPENAI,
        model="gpt-4",
        call_params={
            "max_tokens": 100,
            "temperature": 0.7,
            "top_p": 1,
            "response_format": {"type": "text"},
        },
    )
    db_session.add(prompt)
    db_session.commit()
    return prompt


def test_find_versions_by_function_name(
    db_session: Session, test_project: ProjectTable, test_function: FunctionTable
):
    """Test finding versions by function name"""
    service = VersionService(db_session)

    versions = [
        VersionTable(
            version_num=i,
            project_id=test_project.id,
            function_id=test_function.id,
            function_name=test_function.name,
            function_hash=test_function.hash,
            is_active=i == 1,
        )
        for i in range(3)
    ]
    db_session.add_all(versions)
    db_session.commit()

    found_versions = service.find_versions_by_function_name(
        test_project.id,
        test_function.name,  # pyright: ignore [reportArgumentType]
    )
    assert len(found_versions) == 3
    assert all(v.function_name == test_function.name for v in found_versions)


def test_find_prompt_version_by_id(
    db_session: Session,
    test_project: ProjectTable,
    test_function: FunctionTable,
    test_prompt: PromptTable,
):
    """Test finding prompt version by ID"""
    service = VersionService(db_session)
    version = VersionTable(
        version_num=1,
        project_id=test_project.id,
        function_id=test_function.id,
        prompt_id=test_prompt.id,
        function_name=test_function.name,
        function_hash=test_function.hash,
        prompt_hash=test_prompt.hash,
        is_active=True,
    )
    db_session.add(version)
    db_session.commit()

    found_version = service.find_prompt_version_by_id(
        test_project.id,
        test_function.id,
        test_prompt.id,  # pyright: ignore [reportArgumentType]
    )
    assert found_version is not None
    assert found_version.prompt_id == test_prompt.id


def test_find_function_version_by_hash(
    db_session: Session, test_project: ProjectTable, test_function: FunctionTable
):
    """Test finding function version by hash"""
    service = VersionService(db_session)
    version = VersionTable(
        version_num=1,
        project_id=test_project.id,
        function_id=test_function.id,
        function_name=test_function.name,
        function_hash=test_function.hash,
        is_active=True,
    )
    db_session.add(version)
    db_session.commit()

    found_version = service.find_function_version_by_hash(
        test_project.id,
        test_function.hash,  # pyright: ignore [reportArgumentType]
    )
    assert found_version is not None
    assert found_version.function_hash == test_function.hash


def test_find_prompt_active_version(
    db_session: Session, test_project: ProjectTable, test_function: FunctionTable
):
    """Test finding active version for a prompt"""
    service = VersionService(db_session)
    version = VersionTable(
        version_num=1,
        project_id=test_project.id,
        function_id=test_function.id,
        function_name=test_function.name,
        function_hash=test_function.hash,
        is_active=True,
    )
    db_session.add(version)
    db_session.commit()

    active_version = service.find_prompt_active_version(
        test_project.id,
        test_function.hash,  # pyright: ignore [reportArgumentType]
    )
    assert active_version.is_active is True
    assert active_version.function_hash == test_function.hash


def test_find_prompt_active_version_not_found(
    db_session: Session, test_project: ProjectTable
):
    """Test finding non-existent active version"""
    service = VersionService(db_session)
    with pytest.raises(HTTPException):
        service.find_prompt_active_version(test_project.id, "nonexistent_hash")  # pyright: ignore [reportArgumentType]


def test_change_active_version(
    db_session: Session, test_project: ProjectTable, test_function: FunctionTable
):
    """Test changing active version between two versions of the same function"""
    service = VersionService(db_session)

    # Create first version - initially active
    version1 = VersionTable(
        version_num=0,
        project_id=test_project.id,
        function_id=test_function.id,
        function_name="test_func",
        function_hash="test_hash",
        is_active=True,
    )

    # Create second version - initially inactive
    version2 = VersionTable(
        version_num=1,
        project_id=test_project.id,
        function_id=test_function.id,
        function_name="test_func",
        function_hash="test_hash",
        is_active=False,
    )

    db_session.add(version1)
    db_session.add(version2)
    db_session.commit()

    # Change active version to version2
    new_active = service.change_active_version(test_project.id, version2)  # pyright: ignore [reportArgumentType]

    # Get fresh data from database
    updated_version1 = db_session.get(VersionTable, version1.id)
    updated_version2 = db_session.get(VersionTable, version2.id)

    # Verify state changes
    assert new_active.is_active is True
    assert (
        updated_version1.is_active is False  # pyright: ignore [reportOptionalMemberAccess]
    )  # Previous active version should be inactive
    assert updated_version2.is_active is True  # pyright: ignore [reportOptionalMemberAccess]


def test_change_active_version_no_previous_active(
    db_session: Session, test_project: ProjectTable, test_function: FunctionTable
):
    """Test activating a version when no active version exists"""
    service = VersionService(db_session)

    # Create a version with is_active=False
    version = VersionTable(
        version_num=1,
        project_id=test_project.id,
        function_id=test_function.id,
        function_name="test_func",
        function_hash="test_hash",
        is_active=False,
    )

    db_session.add(version)
    db_session.commit()

    # Activate the version
    new_active = service.change_active_version(test_project.id, version)  # pyright: ignore [reportArgumentType]

    # Verify it became active
    updated_version = db_session.get(VersionTable, version.id)

    assert new_active.is_active is True
    assert updated_version.is_active is True  # pyright: ignore [reportOptionalMemberAccess]


def test_get_function_version_count(
    db_session: Session, test_project: ProjectTable, test_function: FunctionTable
):
    """Test getting function version count"""
    service = VersionService(db_session)
    versions = [
        VersionTable(
            version_num=i,
            project_id=test_project.id,
            function_id=test_function.id,
            function_name=test_function.name,
            function_hash=test_function.hash,
            is_active=i == 0,
        )
        for i in range(3)
    ]
    db_session.add_all(versions)
    db_session.commit()

    count = service.get_function_version_count(test_project.id, test_function.name)  # pyright: ignore [reportArgumentType]
    assert count == 3
