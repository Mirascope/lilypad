"""Tests for the datasets_api.py router"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from uuid import uuid4

from lilypad.server.models.generations import GenerationTable
from lilypad.server.models.projects import ProjectTable

@pytest.fixture
def test_generation_for_datasets(session: Session, test_project: ProjectTable) -> GenerationTable:
    """
    Creates a Generation record with Oxen fields for testing.
    """
    generation = GenerationTable(
        project_uuid=test_project.uuid,
        organization_uuid=test_project.organization_uuid,
        name="oxen_test_generation",
        signature="def test_oxen(): pass",
        code="def test_oxen(): pass",
        hash="oxen_hash_123",
        oxen_repo_url="https://hub.oxen.ai/oxen/SomeRepo",
        oxen_branch="main",
        oxen_path="data/dataset.csv",
    )
    session.add(generation)
    session.commit()
    session.refresh(generation)
    return generation


def test_get_dataset_metadata_no_params(
    client: TestClient,
    test_generation_for_datasets: GenerationTable
):
    """
    If neither generation_uuid nor generation_name is provided, it should return 400.
    """
    project_uuid = test_generation_for_datasets.project_uuid
    response = client.get(f"/projects/{project_uuid}/datasets")  # No query parameters
    assert response.status_code == 400
    assert "Must provide either 'generation_uuid' or 'generation_name'" in response.text


def test_get_dataset_metadata_by_uuid(
    client: TestClient,
    test_generation_for_datasets: GenerationTable
):
    """
    If generation_uuid is provided, the API should return Oxen metadata for that generation.
    """
    project_uuid = test_generation_for_datasets.project_uuid
    gen_uuid = test_generation_for_datasets.uuid

    resp = client.get(
        f"/projects/{project_uuid}/datasets",
        params={"generation_uuid": str(gen_uuid)}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["repo_url"] == "https://hub.oxen.ai/oxen/SomeRepo"
    assert data["branch"] == "main"
    assert data["path"] == "data/dataset.csv"


def test_get_dataset_metadata_by_name(
    client: TestClient,
    session: Session,
    test_generation_for_datasets: GenerationTable
):
    """
    If generation_name is provided, the API should return metadata if the matching generation exists.
    """
    project_uuid = test_generation_for_datasets.project_uuid
    gen_name = test_generation_for_datasets.name

    resp = client.get(
        f"/projects/{project_uuid}/datasets",
        params={"generation_name": gen_name}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["repo_url"] == "https://hub.oxen.ai/oxen/SomeRepo"
    assert data["branch"] == "main"
    assert data["path"] == "data/dataset.csv"


def test_get_dataset_metadata_not_found(
    client: TestClient,
    test_generation_for_datasets: GenerationTable
):
    """
    If no matching generation is found for the given UUID or name, it should return 404.
    """
    project_uuid = test_generation_for_datasets.project_uuid

    resp = client.get(
        f"/projects/{project_uuid}/datasets",
        params={"generation_uuid": str(uuid4())}
    )
    assert resp.status_code == 404
    assert "No matching generation or Oxen metadata found" in response.text
