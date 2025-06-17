"""Tests for the TagService class."""

from uuid import UUID

import pytest
from sqlmodel import Session, select

from lilypad.server.models.tags import TagTable
from lilypad.server.schemas.users import UserPublic
from lilypad.server.services.tags import TagService


@pytest.fixture
def tag_service(db_session: Session, test_user: UserPublic) -> TagService:
    """Create a TagService instance."""
    return TagService(session=db_session, user=test_user)


def test_find_or_create_tag_existing(
    tag_service: TagService, db_session: Session, test_project
):
    """Test finding an existing tag."""
    # Create a tag
    tag_name = "Existing Tag"
    tag = TagTable(
        name=tag_name,
        project_uuid=test_project.uuid,
        organization_uuid=UUID("12345678-1234-1234-1234-123456789abc"),
    )
    db_session.add(tag)
    db_session.commit()

    # Find the tag
    found_tag = tag_service.find_or_create_tag(tag_name, test_project.uuid)

    # Verify it's the same tag
    assert found_tag.uuid == tag.uuid
    assert found_tag.name == tag_name
    assert found_tag.project_uuid == test_project.uuid

    # Verify no new tag was created
    tags = db_session.exec(
        select(TagTable).where(
            TagTable.project_uuid == test_project.uuid,
            TagTable.name == tag_name,
        )
    ).all()
    assert len(tags) == 1


def test_find_or_create_tag_new(
    tag_service: TagService, db_session: Session, test_project
):
    """Test creating a new tag."""
    # Find or create a tag that doesn't exist
    tag_name = "New Tag"
    new_tag = tag_service.find_or_create_tag(tag_name, test_project.uuid)

    # Verify the tag was created
    assert new_tag.uuid is not None
    assert new_tag.name == tag_name
    assert new_tag.project_uuid == test_project.uuid
    assert new_tag.organization_uuid == UUID("12345678-1234-1234-1234-123456789abc")

    # Verify it exists in the database
    db_tag = db_session.exec(
        select(TagTable).where(
            TagTable.project_uuid == test_project.uuid,
            TagTable.name == tag_name,
        )
    ).first()
    assert db_tag is not None
    assert db_tag.uuid == new_tag.uuid


def test_find_or_create_tag_case_sensitive(
    tag_service: TagService, db_session: Session, test_project
):
    """Test that tag names are case-sensitive."""
    # Create a tag
    tag_name = "Case Sensitive"
    tag = TagTable(
        name=tag_name,
        project_uuid=test_project.uuid,
        organization_uuid=UUID("12345678-1234-1234-1234-123456789abc"),
    )
    db_session.add(tag)
    db_session.commit()

    # Find or create a tag with different case
    different_case = "CASE SENSITIVE"
    new_tag = tag_service.find_or_create_tag(different_case, test_project.uuid)

    # Verify a new tag was created
    assert new_tag.uuid != tag.uuid
    assert new_tag.name == different_case
    assert new_tag.project_uuid == test_project.uuid

    # Verify both tags exist in the database
    tags = db_session.exec(
        select(TagTable).where(
            TagTable.project_uuid == test_project.uuid,
        )
    ).all()
    assert len(tags) == 2
    tag_names = {t.name for t in tags}
    assert tag_name in tag_names
    assert different_case in tag_names


def test_find_or_create_tag_different_projects(
    tag_service: TagService, db_session: Session, test_project
):
    """Test that tags with the same name can exist in different projects."""
    # Create another project
    from lilypad.server.models import ProjectTable

    other_project = ProjectTable(
        name="Other Project",
        organization_uuid=UUID("12345678-1234-1234-1234-123456789abc"),
    )
    db_session.add(other_project)
    db_session.commit()

    # Create a tag in the first project
    tag_name = "Project Tag"
    tag1 = tag_service.find_or_create_tag(tag_name, test_project.uuid)

    # Ensure other_project.uuid is not None (type guard)
    assert other_project.uuid is not None

    # Create a tag with the same name in the second project
    tag2 = tag_service.find_or_create_tag(tag_name, other_project.uuid)

    # Verify they are different tags
    assert tag1.uuid != tag2.uuid
    assert tag1.name == tag2.name
    assert tag1.project_uuid != tag2.project_uuid

    # Verify both tags exist in the database
    tags = db_session.exec(
        select(TagTable).where(
            TagTable.name == tag_name,
        )
    ).all()
    assert len(tags) == 2
    project_uuids = {t.project_uuid for t in tags}
    assert test_project.uuid in project_uuids
    assert other_project.uuid in project_uuids
