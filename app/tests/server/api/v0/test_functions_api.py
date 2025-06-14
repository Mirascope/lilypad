"""Tests for the functions API."""

import hashlib
import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from lilypad.server.models import FunctionTable, ProjectTable
from lilypad.server.models.environments import EnvironmentTable
from lilypad.server.models.deployments import DeploymentTable


def test_get_function_by_version(
    client: TestClient, test_project: ProjectTable, test_function: FunctionTable
):
    """Test getting function by version."""
    response = client.get(
        f"/projects/{test_project.uuid}/functions/name/{test_function.name}/version/{test_function.version_num}"
    )

    assert response.status_code == 200
    assert response.json()["name"] == test_function.name
    assert response.json()["version_num"] == test_function.version_num


def test_get_functions_by_name(
    client: TestClient, test_project: ProjectTable, test_function: FunctionTable
):
    """Test getting functions by name."""
    response = client.get(
        f"/projects/{test_project.uuid}/functions/name/{test_function.name}"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == test_function.name


def test_get_deployed_function_by_names_no_deployment(
    client: TestClient,
    test_project: ProjectTable,
    test_function: FunctionTable,
    test_environment: EnvironmentTable,
):
    """Test getting deployed function falls back to latest when not deployed."""
    from lilypad.server._utils.environment import get_current_environment
    from lilypad.server.api.v0.main import api

    # Override the environment dependency directly
    api.dependency_overrides[get_current_environment] = lambda: test_environment

    response = client.get(
        f"/projects/{test_project.uuid}/functions/name/{test_function.name}/environments"
    )

    # Should return the latest function as fallback
    assert response.status_code == 200
    assert response.json()["name"] == test_function.name


def test_get_deployed_function_by_names_not_found(
    client: TestClient,
    test_project: ProjectTable,
    test_environment: EnvironmentTable,
):
    """Test getting deployed function returns 404 when function doesn't exist."""
    from lilypad.server._utils.environment import get_current_environment
    from lilypad.server.api.v0.main import api

    # Override the environment dependency directly
    api.dependency_overrides[get_current_environment] = lambda: test_environment

    response = client.get(
        f"/projects/{test_project.uuid}/functions/name/nonexistent_function/environments"
    )

    assert response.status_code == 404


def test_create_versioned_function(
    client: TestClient, test_project: ProjectTable, session: Session
):
    """Test creating a versioned function."""
    function_create = {
        "name": "new_versioned_function",
        "prompt_template": "Test prompt template",
        "arg_types": {"arg1": "str"},
        "signature": "dummy",  # Will be overridden by endpoint
        "code": "dummy",  # Will be overridden by endpoint
        "hash": "dummy",  # Will be overridden by endpoint
    }

    response = client.post(
        f"/projects/{test_project.uuid}/versioned-functions",
        json=function_create,
    )

    if response.status_code != 200:
        pass
    assert response.status_code == 200
    assert response.json()["name"] == "new_versioned_function"
    assert response.json()["is_versioned"] is True
    assert response.json()["version_num"] == 1


def test_create_versioned_function_no_prompt_template(
    client: TestClient, test_project: ProjectTable
):
    """Test creating a versioned function without prompt template fails."""
    function_create = {
        "name": "test_function",
        "arg_types": {"arg1": "str"},
        "signature": "dummy",  # Will be overridden by endpoint
        "code": "dummy",  # Will be overridden by endpoint
        "hash": "dummy",  # Will be overridden by endpoint
    }

    response = client.post(
        f"/projects/{test_project.uuid}/versioned-functions",
        json=function_create,
    )

    assert response.status_code == 400
    assert "Prompt template is required" in response.json()["detail"]


def test_create_versioned_function_duplicate(
    client: TestClient, test_project: ProjectTable, session: Session
):
    """Test creating a duplicate versioned function returns existing."""
    # First create a function
    function_create = {
        "name": "duplicate_function",
        "prompt_template": "Test prompt template",
        "arg_types": {"arg1": "str"},
        "signature": "dummy",  # Will be overridden by endpoint
        "code": "dummy",  # Will be overridden by endpoint
        "hash": "dummy",  # Will be overridden by endpoint
    }

    response1 = client.post(
        f"/projects/{test_project.uuid}/versioned-functions",
        json=function_create,
    )
    assert response1.status_code == 200
    first_uuid = response1.json()["uuid"]

    # Try to create the same function again
    response2 = client.post(
        f"/projects/{test_project.uuid}/versioned-functions",
        json=function_create,
    )

    assert response2.status_code == 200
    # Should return the same function
    assert response2.json()["uuid"] == first_uuid


def test_get_unique_function_names(
    client: TestClient, test_project: ProjectTable, test_function: FunctionTable
):
    """Test getting unique function names."""
    response = client.get(f"/projects/{test_project.uuid}/functions/metadata/names")

    assert response.status_code == 200
    assert test_function.name in response.json()


def test_get_latest_version_unique_function_names(
    client: TestClient, test_project: ProjectTable, test_function: FunctionTable
):
    """Test getting latest version of unique function names."""
    response = client.get(
        f"/projects/{test_project.uuid}/functions/metadata/names/versions"
    )

    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert any(f["name"] == test_function.name for f in response.json())


def test_get_function_by_hash(
    client: TestClient,
    test_project: ProjectTable,
    test_function: FunctionTable,
    test_api_key,
):
    """Test getting function by hash."""
    response = client.get(
        f"/projects/{test_project.uuid}/functions/hash/{test_function.hash}",
        headers={"X-API-Key": "test_key"},  # Add API key header
    )

    assert response.status_code == 200
    assert response.json()["hash"] == test_function.hash


def test_get_functions(
    client: TestClient, test_project: ProjectTable, test_function: FunctionTable
):
    """Test getting all functions."""
    response = client.get(f"/projects/{test_project.uuid}/functions")

    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert any(f["name"] == test_function.name for f in response.json())


def test_get_function(
    client: TestClient, test_project: ProjectTable, test_function: FunctionTable
):
    """Test getting function by UUID."""
    response = client.get(
        f"/projects/{test_project.uuid}/functions/{test_function.uuid}"
    )

    assert response.status_code == 200
    assert response.json()["name"] == test_function.name


def test_create_new_function(
    client: TestClient, test_project: ProjectTable, session: Session, test_api_key
):
    """Test creating a new function."""
    function_create = {
        "name": "brand_new_function",
        "hash": hashlib.sha256(b"new_function_code").hexdigest(),
        "code": "def brand_new_function(): pass",
        "signature": "brand_new_function()",
    }

    response = client.post(
        f"/projects/{test_project.uuid}/functions",
        json=function_create,
        headers={"X-API-Key": "test_key"},  # Add API key header
    )

    assert response.status_code == 200
    assert response.json()["name"] == "brand_new_function"


def test_create_new_function_duplicate_hash(
    client: TestClient,
    test_project: ProjectTable,
    test_function: FunctionTable,
    test_api_key,
):
    """Test creating a function with existing hash returns the existing function."""
    function_create = {
        "name": "duplicate_hash_function",
        "hash": test_function.hash,  # Use existing hash
        "code": test_function.code,
        "signature": test_function.signature,
    }

    response = client.post(
        f"/projects/{test_project.uuid}/functions",
        json=function_create,
        headers={"X-API-Key": "test_key"},  # Add API key header
    )

    assert response.status_code == 200
    # Should return the existing function
    assert response.json()["uuid"] == str(test_function.uuid)


def test_update_function(
    client: TestClient,
    test_project: ProjectTable,
    test_function: FunctionTable,
    test_api_key,
):
    """Test updating a function."""
    function_update = {}  # Empty update since FunctionUpdate model is empty

    response = client.patch(
        f"/projects/{test_project.uuid}/functions/{test_function.uuid}",
        json=function_update,
        headers={"X-API-Key": "test_key"},  # Add API key header
    )

    assert response.status_code == 200
    # Just verify the function is returned unchanged
    assert response.json()["name"] == test_function.name


def test_archive_functions_by_name(
    client: TestClient,
    test_project: ProjectTable,
    test_function: FunctionTable,
    session: Session,
):
    """Test archiving functions by name."""
    response = client.delete(
        f"/projects/{test_project.uuid}/functions/names/{test_function.name}"
    )

    assert response.status_code == 200
    assert response.json() is True

    # Verify function is archived
    session.refresh(test_function)
    assert test_function.archived is not None


def test_archive_function(
    client: TestClient,
    test_project: ProjectTable,
    test_function: FunctionTable,
    session: Session,
):
    """Test archiving function by UUID."""
    response = client.delete(
        f"/projects/{test_project.uuid}/functions/{test_function.uuid}"
    )

    assert response.status_code == 200
    assert response.json() is True

    # Verify function is archived
    session.refresh(test_function)
    assert test_function.archived is not None


def test_get_function_nonexistent(client: TestClient, test_project: ProjectTable):
    """Test getting nonexistent function returns 404."""
    response = client.get(f"/projects/{test_project.uuid}/functions/{uuid.uuid4()}")

    assert response.status_code == 404


def test_update_nonexistent_function(client: TestClient, test_project: ProjectTable):
    """Test updating nonexistent function returns 404."""
    function_update = {
        "prompt_template": "Updated prompt",
    }

    response = client.patch(
        f"/projects/{test_project.uuid}/functions/{uuid.uuid4()}",
        json=function_update,
        headers={"X-API-Key": "test_key"},
    )

    assert response.status_code == 404


def test_get_function_by_invalid_hash(
    client: TestClient, test_project: ProjectTable, test_api_key
):
    """Test getting function by invalid hash returns 404."""
    response = client.get(
        f"/projects/{test_project.uuid}/functions/hash/invalid_hash_123",
        headers={"X-API-Key": "test_key"},
    )

    assert response.status_code == 404


def test_get_deployed_function_inactive_deployment(
    client: TestClient, 
    test_project: ProjectTable, 
    test_function: FunctionTable,
    test_environment: EnvironmentTable,
    session: Session
):
    """Test getting deployed function when deployment exists but is inactive."""
    from lilypad.server._utils.environment import get_current_environment
    from lilypad.server.api.v0.main import api
    
    # Create an inactive deployment
    deployment = DeploymentTable(
        project_uuid=test_project.uuid,
        environment_uuid=test_environment.uuid,
        function_uuid=test_function.uuid,
        organization_uuid=test_project.organization_uuid,  # Add required field
        is_active=False  # Make it inactive
    )
    session.add(deployment)
    session.commit()
    session.refresh(deployment)
    
    # Override the environment dependency
    api.dependency_overrides[get_current_environment] = lambda: test_environment
    
    try:
        response = client.get(
            f"/projects/{test_project.uuid}/functions/name/{test_function.name}/environments"
        )
        
        # Should return 400 for inactive deployment
        assert response.status_code == 400
        assert "deployed but not active" in response.json()["detail"]
    finally:
        # Clean up override
        api.dependency_overrides.pop(get_current_environment, None)


def test_archive_functions_by_name_with_exception(
    client: TestClient,
    test_project: ProjectTable,
    test_function: FunctionTable,
    monkeypatch
):
    """Test archiving functions by name when exception occurs."""
    from lilypad.server.services import FunctionService
    
    # Mock the function service to raise an exception
    def mock_archive_record_by_name(*args, **kwargs):
        raise Exception("Test exception")
    
    monkeypatch.setattr(FunctionService, "archive_record_by_name", mock_archive_record_by_name)
    
    response = client.delete(
        f"/projects/{test_project.uuid}/functions/names/{test_function.name}"
    )
    
    assert response.status_code == 200
    assert response.json() is False  # Should return False when exception occurs


def test_archive_function_with_exception(
    client: TestClient,
    test_project: ProjectTable,
    test_function: FunctionTable,
    monkeypatch
):
    """Test archiving function by UUID when exception occurs."""
    from lilypad.server.services import FunctionService
    
    # Mock the function service to raise an exception
    def mock_archive_record_by_uuid(*args, **kwargs):
        raise Exception("Test exception")
    
    monkeypatch.setattr(FunctionService, "archive_record_by_uuid", mock_archive_record_by_uuid)
    
    response = client.delete(
        f"/projects/{test_project.uuid}/functions/{test_function.uuid}"
    )
    
    assert response.status_code == 200
    assert response.json() is False  # Should return False when exception occurs


def test_get_deployed_function_active_deployment(
    client: TestClient, 
    test_project: ProjectTable, 
    test_function: FunctionTable,
    test_environment: EnvironmentTable,
    session: Session
):
    """Test getting deployed function when deployment exists and is active."""
    from lilypad.server._utils.environment import get_current_environment
    from lilypad.server.api.v0.main import api
    
    # Create an active deployment
    deployment = DeploymentTable(
        project_uuid=test_project.uuid,
        environment_uuid=test_environment.uuid,
        function_uuid=test_function.uuid,
        organization_uuid=test_project.organization_uuid,
        is_active=True  # Make it active
    )
    session.add(deployment)
    session.commit()
    session.refresh(deployment)
    
    # Override the environment dependency
    api.dependency_overrides[get_current_environment] = lambda: test_environment
    
    try:
        response = client.get(
            f"/projects/{test_project.uuid}/functions/name/{test_function.name}/environments"
        )
        
        # Should return the deployed function
        assert response.status_code == 200
        assert response.json()["name"] == test_function.name
        assert response.json()["uuid"] == str(test_function.uuid)
    finally:
        # Clean up override
        api.dependency_overrides.pop(get_current_environment, None)


def test_archive_functions_by_name_with_opensearch_enabled(
    client: TestClient,
    test_project: ProjectTable,
    test_function: FunctionTable,
    monkeypatch
):
    """Test archiving functions by name with OpenSearch enabled (covers success path in exception handler)."""
    from lilypad.server.services.opensearch import OpenSearchService
    
    # Mock OpenSearch service to be enabled
    class MockOpenSearchService:
        is_enabled = True
        
        def delete_traces_by_function_uuid(self, project_uuid, function_uuid):
            pass  # Mock successful deletion
    
    mock_opensearch = MockOpenSearchService()
    
    # Mock the get_opensearch_service dependency
    def mock_get_opensearch_service():
        return mock_opensearch
    
    monkeypatch.setattr("lilypad.server.services.opensearch.get_opensearch_service", mock_get_opensearch_service)
    
    response = client.delete(
        f"/projects/{test_project.uuid}/functions/names/{test_function.name}"
    )
    
    assert response.status_code == 200
    assert response.json() is True


def test_archive_function_with_opensearch_enabled(
    client: TestClient,
    test_project: ProjectTable,
    test_function: FunctionTable,
    monkeypatch
):
    """Test archiving function by UUID with OpenSearch enabled (covers success path in exception handler)."""
    from lilypad.server.services.opensearch import OpenSearchService
    
    # Mock OpenSearch service to be enabled
    class MockOpenSearchService:
        is_enabled = True
        
        def delete_traces_by_function_uuid(self, project_uuid, function_uuid):
            pass  # Mock successful deletion
    
    mock_opensearch = MockOpenSearchService()
    
    # Mock the get_opensearch_service dependency
    def mock_get_opensearch_service():
        return mock_opensearch
    
    monkeypatch.setattr("lilypad.server.services.opensearch.get_opensearch_service", mock_get_opensearch_service)
    
    response = client.delete(
        f"/projects/{test_project.uuid}/functions/{test_function.uuid}"
    )
    
    assert response.status_code == 200
    assert response.json() is True
