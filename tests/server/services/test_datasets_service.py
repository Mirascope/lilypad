"""Tests for the DatasetsService class"""

from uuid import uuid4

import pytest
from sqlmodel import Session

from lilypad.server.models.generations import GenerationTable
from lilypad.server.models.projects import ProjectTable
from lilypad.server.services.datasets import DatasetsService
from lilypad.server.services.generations import GenerationService


@pytest.fixture
def datasets_service(session: Session, test_project: ProjectTable):
    """Creates a DatasetsService instance with a GenerationService dependency."""
    gen_service = GenerationService(session=session)
    ds_service = DatasetsService(session=session, generation_service=gen_service)
    return ds_service


def test_find_oxen_metadata_by_uuid(
    session: Session, test_project: ProjectTable, datasets_service: DatasetsService
):
    """Tests fetching Oxen metadata by generation_uuid."""
    # Create a Generation record with Oxen fields
    generation = GenerationTable(
        project_uuid=test_project.uuid,
        organization_uuid=test_project.organization_uuid,
        name="test_gen_for_service",
        signature="def serv(): pass",
        code="def serv(): pass",
        hash="hash_xyz",
        oxen_repo_url="https://hub.oxen.ai/my/repo",
        oxen_branch="dev",
        oxen_path="data/path.csv",
    )
    session.add(generation)
    session.commit()
    session.refresh(generation)

    # Execute service method
    meta = datasets_service.find_oxen_metadata(
        project_uuid=test_project.uuid,
        generation_uuid=str(generation.uuid),
        generation_name=None,
    )
    assert meta is not None
    assert meta["repo_url"] == "https://hub.oxen.ai/my/repo"
    assert meta["branch"] == "dev"
    assert meta["path"] == "data/path.csv"


def test_find_oxen_metadata_by_name(
    session: Session, test_project: ProjectTable, datasets_service: DatasetsService
):
    """Tests fetching Oxen metadata by generation_name."""
    generation = GenerationTable(
        project_uuid=test_project.uuid,
        organization_uuid=test_project.organization_uuid,
        name="oxen_test_name",
        oxen_repo_url="https://hub.oxen.ai/my/another_repo",
        oxen_branch="main",
        oxen_path="dataset/train.csv",
    )
    session.add(generation)
    session.commit()
    session.refresh(generation)

    meta = datasets_service.find_oxen_metadata(
        project_uuid=test_project.uuid, generation_name="oxen_test_name"
    )
    assert meta is not None
    assert meta["repo_url"] == "https://hub.oxen.ai/my/another_repo"
    assert meta["branch"] == "main"
    assert meta["path"] == "dataset/train.csv"


def test_find_oxen_metadata_none(
    session: Session, test_project: ProjectTable, datasets_service: DatasetsService
):
    """If no Generation matches or Oxen fields are missing, the service should return None."""
    not_found = datasets_service.find_oxen_metadata(
        project_uuid=test_project.uuid, generation_uuid=str(uuid4())
    )
    assert not_found is None

    none_name = datasets_service.find_oxen_metadata(
        project_uuid=test_project.uuid, generation_name="not_exist_name"
    )
    assert none_name is None
