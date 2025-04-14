"""Tests for the require_license module in lilypad/ee/server/require_license.py."""

import inspect
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException, status

from ee.validate import LicenseError, LicenseInfo, Tier
from lilypad.ee.server.require_license import RequireLicense, require_license


class DummyProject:
    """Dummy project with an organization UUID attribute."""

    def __init__(self, organization_uuid: UUID | None):
        self.organization_uuid = organization_uuid


class DummyProjectService:
    """Dummy project service that returns a preset project."""

    def __init__(self, project: DummyProject | None):
        self._project = project

    def find_record_by_uuid(self, project_uuid: UUID) -> DummyProject | None:
        """Return the preset project."""
        return self._project


@pytest.mark.asyncio
async def test_project_not_found():
    """Test that HTTPException 404 is raised when the project is not found."""
    project_uuid = uuid4()
    project_service = DummyProjectService(None)
    organization_service = MagicMock()
    dependency = RequireLicense(tier=Tier.ENTERPRISE)
    request = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        await dependency(request, project_uuid, project_service, organization_service)  # pyright: ignore [reportArgumentType]
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "Project not found"


@pytest.mark.asyncio
async def test_project_without_organization():
    """Test that HTTPException 400 is raised when the project lacks an organization_uuid."""
    project_uuid = uuid4()
    project = DummyProject(organization_uuid=None)
    project_service = DummyProjectService(project)
    organization_service = MagicMock()
    dependency = RequireLicense(tier=Tier.ENTERPRISE)
    request = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        await dependency(request, project_uuid, project_service, organization_service)  # pyright: ignore [reportArgumentType]
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Project does not belong to an organization"


@pytest.mark.asyncio
async def test_invalid_license_none():
    """Test that HTTPException 403 is raised when license validation returns None."""
    project_uuid = uuid4()
    org_uuid = uuid4()
    project = DummyProject(organization_uuid=org_uuid)
    project_service = DummyProjectService(project)
    organization_service = MagicMock()
    request = MagicMock()

    # Patch LicenseValidator so that validate_license returns None
    with patch(
        "lilypad.ee.server.require_license.LicenseValidator"
    ) as mock_validator_class:
        mock_validator = MagicMock()
        mock_validator.validate_license.return_value = None
        mock_validator_class.return_value = mock_validator

        dependency = RequireLicense(tier=Tier.ENTERPRISE)
        with pytest.raises(HTTPException) as exc_info:
            await dependency(
                request,
                project_uuid,
                project_service,
                organization_service,  # pyright: ignore [reportArgumentType]
            )
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert (
            exc_info.value.detail
            == "Invalid License. Contact support@mirascope.com to get one."
        )


@pytest.mark.asyncio
async def test_license_mismatch():
    """Test that HTTPException 403 is raised when the license's organization_uuid mismatches the project's."""
    project_uuid = uuid4()
    org_uuid = uuid4()
    project = DummyProject(organization_uuid=org_uuid)
    project_service = DummyProjectService(project)
    organization_service = MagicMock()
    request = MagicMock()

    # Return a LicenseInfo with an organization_uuid that does not match the project's
    with patch(
        "lilypad.ee.server.require_license.LicenseValidator"
    ) as mock_validator_class:
        mock_validator = MagicMock()
        wrong_org_uuid = uuid4()
        license_info = LicenseInfo(
            organization_uuid=wrong_org_uuid,
            tier=Tier.ENTERPRISE,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            customer="dummy",
            license_id="dummy",
        )
        mock_validator.validate_license.return_value = license_info
        mock_validator_class.return_value = mock_validator

        dependency = RequireLicense(tier=Tier.ENTERPRISE)
        with pytest.raises(HTTPException) as exc_info:
            await dependency(
                request,
                project_uuid,
                project_service,
                organization_service,  # pyright: ignore [reportArgumentType]
            )
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "License key does not match organization"


@pytest.mark.asyncio
async def test_wrong_license_tier():
    """Test that HTTPException 403 is raised when the license tier is insufficient."""
    project_uuid = uuid4()
    org_uuid = uuid4()
    project = DummyProject(organization_uuid=org_uuid)
    project_service = DummyProjectService(project)
    organization_service = MagicMock()
    request = MagicMock()

    # Return a LicenseInfo with a correct organization_uuid but a FREE tier while ENTERPRISE is required
    with patch(
        "lilypad.ee.server.require_license.LicenseValidator"
    ) as mock_validator_class:
        mock_validator = MagicMock()
        license_info = LicenseInfo(
            organization_uuid=org_uuid,
            tier=Tier.FREE,  # Insufficient tier
            expires_at=datetime.now(tz=timezone.utc) + timedelta(days=1),
            customer="dummy",
            license_id="dummy",
        )
        mock_validator.validate_license.return_value = license_info
        mock_validator_class.return_value = mock_validator

        dependency = RequireLicense(tier=Tier.ENTERPRISE)
        with pytest.raises(HTTPException) as exc_info:
            await dependency(
                request,
                project_uuid,
                project_service,
                organization_service,  # pyright: ignore [reportArgumentType]
            )
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert (
            exc_info.value.detail
            == "License tier (FREE) does not meet the required tier (ENTERPRISE). Contact support@mirascope.com to upgrade."
        )


@pytest.mark.asyncio
async def test_valid_license():
    """Test that a valid LicenseInfo is returned when license validation passes."""
    project_uuid = uuid4()
    org_uuid = uuid4()
    project = DummyProject(organization_uuid=org_uuid)
    project_service = DummyProjectService(project)
    organization_service = MagicMock()
    request = MagicMock()

    # Return a valid LicenseInfo with matching organization_uuid and ENTERPRISE tier
    with patch(
        "lilypad.ee.server.require_license.LicenseValidator"
    ) as mock_validator_class:
        mock_validator = MagicMock()
        license_info = LicenseInfo(
            organization_uuid=org_uuid,
            tier=Tier.ENTERPRISE,
            expires_at=datetime.now(tz=timezone.utc) + timedelta(days=1),
            customer="dummy",
            license_id="dummy",
        )
        mock_validator.validate_license.return_value = license_info
        mock_validator_class.return_value = mock_validator

        dependency = RequireLicense(tier=Tier.ENTERPRISE)
        result = await dependency(
            request,
            project_uuid,
            project_service,
            organization_service,  # pyright: ignore [reportArgumentType]
        )
        assert result == license_info


@pytest.mark.asyncio
async def test_free_tier_returns_none():
    """Test that when the required tier is FREE, the dependency returns None regardless of license info."""
    project_uuid = uuid4()
    org_uuid = uuid4()
    project = DummyProject(organization_uuid=org_uuid)
    project_service = DummyProjectService(project)
    organization_service = MagicMock()
    request = MagicMock()

    # Even if a valid LicenseInfo is returned, FREE tier should cause the dependency to return None.
    with patch(
        "lilypad.ee.server.require_license.LicenseValidator"
    ) as mock_validator_class:
        mock_validator = MagicMock()
        license_info = LicenseInfo(
            organization_uuid=org_uuid,
            tier=Tier.ENTERPRISE,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            customer="dummy",
            license_id="dummy",
        )
        mock_validator.validate_license.return_value = license_info
        mock_validator_class.return_value = mock_validator

        dependency = RequireLicense(tier=Tier.FREE)
        result = await dependency(
            request,
            project_uuid,
            project_service,
            organization_service,  # pyright: ignore [reportArgumentType]
        )
        assert result is None


@pytest.mark.asyncio
async def test_license_validator_exception():
    """Test that an HTTPException with 403 is raised when LicenseValidator raises LicenseError."""
    project_uuid = uuid4()
    org_uuid = uuid4()
    project = DummyProject(organization_uuid=org_uuid)
    project_service = DummyProjectService(project)
    organization_service = MagicMock()
    request = MagicMock()

    with patch(
        "lilypad.ee.server.require_license.LicenseValidator"
    ) as mock_validator_class:
        mock_validator = MagicMock()
        mock_validator.validate_license.side_effect = LicenseError("Validation failed")
        mock_validator_class.return_value = mock_validator

        dependency = RequireLicense(tier=Tier.ENTERPRISE)
        with pytest.raises(HTTPException) as exc_info:
            await dependency(
                request,
                project_uuid,
                project_service,
                organization_service,  # pyright: ignore [reportArgumentType]
            )
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Validation failed" in exc_info.value.detail


def test_require_license_decorator_signature():
    """Test that the require_license decorator adds the license_info parameter with type annotation."""

    @require_license(Tier.ENTERPRISE)
    async def dummy_endpoint(x: int) -> int:
        return x

    # Retrieve the signature of the decorated function
    sig = inspect.signature(dummy_endpoint)
    # Verify that 'license_info' is included in the parameters
    assert "license_info" in sig.parameters
    param = sig.parameters["license_info"]
    # Check that the parameter is keyword-only
    assert param.kind == inspect.Parameter.KEYWORD_ONLY
    # Verify that the annotation is "LicenseInfo | None"
    assert param.annotation == "LicenseInfo | None"


@pytest.mark.asyncio
async def test_require_license_decorator_wrapper():
    """Test that the require_license decorator removes license_info from kwargs when calling the endpoint."""
    captured_kwargs = {}

    async def dummy(x: int, **kwargs):
        captured_kwargs.update(kwargs)
        return x

    decorated = require_license(Tier.ENTERPRISE)(dummy)
    # Call the decorated function with a license_info value; it should be popped by the decorator.
    result = await decorated(10, license_info="dummy_value")
    assert result == 10
    assert "license_info" not in captured_kwargs
