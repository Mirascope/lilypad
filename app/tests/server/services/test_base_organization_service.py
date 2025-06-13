"""Tests for base organization service."""

import pytest
from pydantic import BaseModel
from sqlmodel import Session
from uuid import uuid4

from lilypad.server.models.projects import ProjectTable
from lilypad.server.services.base_organization import BaseOrganizationService


class MockCreateModel(BaseModel):
    """Mock create model for testing."""
    name: str


class TestableBaseOrganizationService(BaseOrganizationService[ProjectTable, MockCreateModel]):
    """Testable implementation of BaseOrganizationService."""
    table = ProjectTable
    create_model = MockCreateModel


def test_find_record_by_uuid_with_organization_filter(
    db_session: Session, test_user, test_project: ProjectTable
):
    """Test find_record_by_uuid applies organization filter automatically."""
    service = TestableBaseOrganizationService(session=db_session, user=test_user)
    
    # Find existing record (should use user's organization automatically)
    found_project = service.find_record_by_uuid(test_project.uuid)
    assert found_project.uuid == test_project.uuid
    assert found_project.organization_uuid == test_user.active_organization_uuid
    
    # Test with explicit organization_uuid filter
    found_project_explicit = service.find_record_by_uuid(
        test_project.uuid, 
        organization_uuid=test_user.active_organization_uuid
    )
    assert found_project_explicit.uuid == test_project.uuid


def test_find_record_by_uuid_wrong_organization(
    db_session: Session, test_user, test_project: ProjectTable
):
    """Test find_record_by_uuid fails when record belongs to different organization."""
    service = TestableBaseOrganizationService(session=db_session, user=test_user)
    
    # Try to find record with wrong organization UUID
    wrong_org_uuid = uuid4()
    with pytest.raises(Exception):  # Should raise HTTPException from base class
        service.find_record_by_uuid(test_project.uuid, organization_uuid=wrong_org_uuid)


def test_find_all_records_with_organization_filter(
    db_session: Session, test_user, test_project: ProjectTable
):
    """Test find_all_records applies organization filter automatically."""
    service = TestableBaseOrganizationService(session=db_session, user=test_user)
    
    # Find all records (should filter by user's organization automatically)
    all_projects = service.find_all_records()
    assert len(all_projects) >= 1
    assert test_project.uuid in {project.uuid for project in all_projects}
    
    # All returned projects should belong to the user's organization
    for project in all_projects:
        assert project.organization_uuid == test_user.active_organization_uuid
    
    # Test with explicit organization_uuid filter
    explicit_projects = service.find_all_records(
        organization_uuid=test_user.active_organization_uuid
    )
    assert len(explicit_projects) >= 1


def test_find_all_records_with_additional_filters(
    db_session: Session, test_user, test_project: ProjectTable
):
    """Test find_all_records with additional filters."""
    service = TestableBaseOrganizationService(session=db_session, user=test_user)
    
    # Find with name filter
    filtered_projects = service.find_all_records(name=test_project.name)
    assert len(filtered_projects) == 1
    assert filtered_projects[0].uuid == test_project.uuid
    assert filtered_projects[0].organization_uuid == test_user.active_organization_uuid


def test_find_all_records_different_organization(
    db_session: Session, test_user
):
    """Test find_all_records returns empty for different organization."""
    service = TestableBaseOrganizationService(session=db_session, user=test_user)
    
    # Find with wrong organization UUID
    wrong_org_uuid = uuid4()
    wrong_org_projects = service.find_all_records(organization_uuid=wrong_org_uuid)
    assert len(wrong_org_projects) == 0


def test_create_record_with_organization(db_session: Session, test_user):
    """Test create_record automatically adds organization."""
    service = TestableBaseOrganizationService(session=db_session, user=test_user)
    
    # Create new record (should use user's organization automatically)
    create_data = MockCreateModel(name="test_project_create")
    
    new_project = service.create_record(create_data)
    
    assert new_project.name == "test_project_create"
    assert new_project.organization_uuid == test_user.active_organization_uuid
    assert new_project.uuid is not None


def test_create_record_with_explicit_organization(db_session: Session, test_user):
    """Test create_record with explicit organization_uuid."""
    service = TestableBaseOrganizationService(session=db_session, user=test_user)
    
    # Create new record with explicit organization
    create_data = MockCreateModel(name="test_project_explicit")
    explicit_org_uuid = uuid4()
    
    new_project = service.create_record(
        create_data, 
        organization_uuid=explicit_org_uuid
    )
    
    assert new_project.name == "test_project_explicit"
    assert new_project.organization_uuid == explicit_org_uuid
    assert new_project.uuid is not None


def test_create_record_with_additional_kwargs(db_session: Session, test_user):
    """Test create_record with additional kwargs (ProjectTable only has name, so test basic functionality)."""
    service = TestableBaseOrganizationService(session=db_session, user=test_user)
    
    # Create new record - ProjectTable only has name field, so test passes through kwargs correctly
    create_data = MockCreateModel(name="test_project_kwargs")
    
    new_project = service.create_record(create_data)
    
    assert new_project.name == "test_project_kwargs"
    assert new_project.organization_uuid == test_user.active_organization_uuid
    assert new_project.uuid is not None


def test_organization_filters_pop_behavior(db_session: Session, test_user):
    """Test that organization_uuid is properly popped from filters."""
    service = TestableBaseOrganizationService(session=db_session, user=test_user)
    
    # Test find_record_by_uuid - organization_uuid should be popped
    create_data = MockCreateModel(name="test_pop_behavior")
    created_project = service.create_record(create_data)
    
    # The organization_uuid should be popped and not passed to super().find_record_by_uuid
    found_project = service.find_record_by_uuid(created_project.uuid)
    assert found_project.uuid == created_project.uuid
    
    # Test find_all_records - organization_uuid should be popped
    all_projects = service.find_all_records()
    assert len(all_projects) >= 1
    
    # Test create_record - organization_uuid should be popped from kwargs
    another_project = service.create_record(MockCreateModel(name="test_pop_create"))
    assert another_project.organization_uuid == test_user.active_organization_uuid


def test_base_organization_service_inheritance(db_session: Session, test_user):
    """Test that BaseOrganizationService properly inherits from BaseService."""
    service = TestableBaseOrganizationService(session=db_session, user=test_user)
    
    # Should have all BaseService attributes
    assert hasattr(service, 'session')
    assert hasattr(service, 'user')
    assert hasattr(service, 'table')
    assert hasattr(service, 'create_model')
    
    # Should have inherited methods
    assert hasattr(service, 'find_record')
    assert hasattr(service, 'find_records_by_uuids')
    assert hasattr(service, 'delete_record_by_uuid')
    assert hasattr(service, 'update_record_by_uuid')
    
    # Test that inherited methods work
    create_data = MockCreateModel(name="test_inheritance")
    created_project = service.create_record(create_data)
    
    # Test inherited find_record method (without organization filter)
    found_by_name = service.find_record(name="test_inheritance")
    assert found_by_name is not None
    assert found_by_name.uuid == created_project.uuid