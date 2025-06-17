"""Tests for environments and deployments API."""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session

from lilypad.server.models import (
    DeploymentTable,
    EnvironmentTable,
    FunctionTable,
    ProjectTable,
)


class TestEnvironmentsAPI:
    """Test environments API endpoints."""

    def test_get_environments_empty(
        self, client: TestClient, test_environment: EnvironmentTable
    ):
        """Test getting environments with default test environment."""
        response = client.get("/environments")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # There's already a test_environment fixture that creates one
        assert len(data) == 1
        assert data[0]["name"] == test_environment.name

    def test_get_environments_with_data(
        self, client: TestClient, session: Session, test_project: ProjectTable
    ):
        """Test getting environments with multiple environments."""
        # Add additional environment
        env2 = EnvironmentTable(
            name="production",
            organization_uuid=test_project.organization_uuid,
        )
        session.add(env2)
        session.commit()

        response = client.get("/environments")
        assert response.status_code == 200
        data = response.json()
        # Should have test_environment from fixture + production
        assert len(data) >= 1
        names = [env["name"] for env in data]
        assert "production" in names

    def test_create_environment(self, client: TestClient):
        """Test creating a new environment."""
        environment_data = {
            "name": "staging",
            "description": "Staging environment",
        }
        response = client.post("/environments", json=environment_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "staging"
        assert data["description"] == "Staging environment"
        assert "uuid" in data
        assert "created_at" in data
        # Note: EnvironmentTable doesn't have updated_at field

    def test_get_environment_by_uuid(
        self, client: TestClient, test_environment: EnvironmentTable
    ):
        """Test getting environment by UUID."""
        response = client.get(f"/environments/{test_environment.uuid}")
        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == str(test_environment.uuid)
        assert data["name"] == test_environment.name

    def test_get_environment_not_found(self, client: TestClient):
        """Test getting environment with invalid UUID."""
        fake_uuid = uuid4()
        response = client.get(f"/environments/{fake_uuid}")
        assert response.status_code == 404

    def test_delete_environment(
        self, client: TestClient, session: Session, test_project: ProjectTable
    ):
        """Test deleting an environment."""
        # Create environment to delete
        env_to_delete = EnvironmentTable(
            name="to_delete",
            organization_uuid=test_project.organization_uuid,
        )
        session.add(env_to_delete)
        session.commit()
        session.refresh(env_to_delete)

        response = client.delete(f"/environments/{env_to_delete.uuid}")
        assert response.status_code == 200
        assert response.json() is True

        # Verify it's deleted
        response = client.get(f"/environments/{env_to_delete.uuid}")
        assert response.status_code == 404

    def test_delete_environment_not_found(self, client: TestClient):
        """Test deleting non-existent environment."""
        fake_uuid = uuid4()
        response = client.delete(f"/environments/{fake_uuid}")
        assert response.status_code == 404


class TestDeploymentsAPI:
    """Test deployment API endpoints."""

    def test_deploy_function(
        self,
        client: TestClient,
        test_project: ProjectTable,
        test_environment: EnvironmentTable,
        test_function: FunctionTable,
    ):
        """Test deploying a function to an environment."""
        response = client.post(
            f"/projects/{test_project.uuid}/environments/{test_environment.uuid}/deploy",
            params={
                "function_uuid": str(test_function.uuid),
                "notes": "Initial deployment",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["environment_uuid"] == str(test_environment.uuid)
        assert data["function_uuid"] == str(test_function.uuid)
        assert data["is_active"] is True
        assert data["notes"] == "Initial deployment"
        assert data["version_num"] == 1

    def test_deploy_function_without_notes(
        self,
        client: TestClient,
        test_project: ProjectTable,
        test_environment: EnvironmentTable,
        test_function: FunctionTable,
    ):
        """Test deploying a function without notes."""
        response = client.post(
            f"/projects/{test_project.uuid}/environments/{test_environment.uuid}/deploy",
            params={"function_uuid": str(test_function.uuid)},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] is None

    def test_get_active_deployment(
        self,
        client: TestClient,
        session: Session,
        test_project: ProjectTable,
        test_environment: EnvironmentTable,
        test_function: FunctionTable,
    ):
        """Test getting active deployment for an environment."""
        # Create a deployment
        deployment = DeploymentTable(
            environment_uuid=test_environment.uuid,  # type: ignore[arg-type]
            function_uuid=test_function.uuid,  # type: ignore[arg-type]
            project_uuid=test_project.uuid,
            organization_uuid=test_project.organization_uuid,
            is_active=True,
            version_num=1,
            notes="Test deployment",
        )
        session.add(deployment)
        session.commit()

        response = client.get(
            f"/projects/{test_project.uuid}/environments/{test_environment.uuid}/deployment"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["environment_uuid"] == str(test_environment.uuid)
        assert data["function_uuid"] == str(test_function.uuid)
        assert data["is_active"] is True

    def test_get_active_deployment_not_found(
        self,
        client: TestClient,
        test_project: ProjectTable,
        test_environment: EnvironmentTable,
    ):
        """Test getting active deployment when none exists."""
        response = client.get(
            f"/projects/{test_project.uuid}/environments/{test_environment.uuid}/deployment"
        )
        assert response.status_code == 404
        assert "No active deployment found" in response.json()["detail"]

    def test_get_environment_function(
        self,
        client: TestClient,
        session: Session,
        test_project: ProjectTable,
        test_environment: EnvironmentTable,
        test_function: FunctionTable,
    ):
        """Test getting the active function for an environment."""
        # Create a deployment
        deployment = DeploymentTable(
            environment_uuid=test_environment.uuid,  # type: ignore[arg-type]
            function_uuid=test_function.uuid,  # type: ignore[arg-type]
            project_uuid=test_project.uuid,
            organization_uuid=test_project.organization_uuid,
            is_active=True,
            version_num=1,
        )
        session.add(deployment)
        session.commit()

        response = client.get(
            f"/projects/{test_project.uuid}/environments/{test_environment.uuid}/function"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == str(test_function.uuid)
        assert data["name"] == test_function.name
        assert data["signature"] == test_function.signature

    def test_get_environment_function_not_found(
        self,
        client: TestClient,
        test_project: ProjectTable,
        test_environment: EnvironmentTable,
    ):
        """Test getting function when no deployment exists."""
        response = client.get(
            f"/projects/{test_project.uuid}/environments/{test_environment.uuid}/function"
        )
        assert response.status_code == 404

    def test_get_deployment_history(
        self,
        client: TestClient,
        test_project: ProjectTable,
        test_environment: EnvironmentTable,
        test_function: FunctionTable,
    ):
        """Test getting deployment history for an environment."""
        # Deploy a function first
        deploy_response = client.post(
            f"/projects/{test_project.uuid}/environments/{test_environment.uuid}/deploy",
            params={
                "function_uuid": str(test_function.uuid),
                "notes": "Test deployment",
            },
        )
        assert deploy_response.status_code == 200

        # Get deployment history
        response = client.get(
            f"/projects/{test_project.uuid}/environments/{test_environment.uuid}/history"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["is_active"] is True
        assert data[0]["notes"] == "Test deployment"

    def test_get_deployment_history_empty(
        self,
        client: TestClient,
        test_project: ProjectTable,
        test_environment: EnvironmentTable,
    ):
        """Test getting deployment history when none exist."""
        # Capture UUIDs before using them
        project_uuid = str(test_project.uuid)
        env_uuid = str(test_environment.uuid)

        response = client.get(
            f"/projects/{project_uuid}/environments/{env_uuid}/history"
        )
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_deploy_multiple_times(
        self,
        client: TestClient,
        session: Session,
        test_project: ProjectTable,
        test_environment: EnvironmentTable,
        test_function: FunctionTable,
    ):
        """Test deploying multiple times deactivates previous deployments."""
        # Create another function to test multiple deployments
        func2 = FunctionTable(
            name="function2",
            signature="func2()",
            code="def func2(): pass",
            hash="test_hash2",
            arg_types={},
            project_uuid=test_project.uuid,
            organization_uuid=test_project.organization_uuid,
            version_num=1,
        )
        session.add(func2)
        session.commit()
        session.refresh(func2)

        # Capture UUIDs at the start to avoid detached instance errors
        project_uuid = str(test_project.uuid)
        env_uuid = str(test_environment.uuid)
        func1_uuid = str(test_function.uuid)
        func2_uuid = str(func2.uuid)

        # First deployment
        response1 = client.post(
            f"/projects/{project_uuid}/environments/{env_uuid}/deploy",
            params={"function_uuid": func1_uuid, "notes": "First deployment"},
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["notes"] == "First deployment"
        assert data1["is_active"] is True

        # Second deployment with different function
        response2 = client.post(
            f"/projects/{project_uuid}/environments/{env_uuid}/deploy",
            params={"function_uuid": func2_uuid, "notes": "Second deployment"},
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["notes"] == "Second deployment"
        assert data2["is_active"] is True
