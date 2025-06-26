"""License validation module for Lilypad Enterprise Edition"""

import functools
import inspect
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status

from ee import LicenseInfo, LicenseValidator, Tier
from ee.validate import LicenseError

from ...ee.server import ALT_HOST_NAME, HOST_NAME
from ...server._utils import get_current_user
from ...server.exceptions import LilypadForbiddenError
from ...server.schemas.users import UserPublic
from ...server.services import OrganizationService, ProjectService
from ...server.services.billing import BillingService
from ...server.settings import get_settings

_EndPointFunc = TypeVar("_EndPointFunc", bound=Callable[..., Awaitable[Any]])


def require_license(
    tier: Tier, cloud_free: bool = False
) -> Callable[[_EndPointFunc], _EndPointFunc]:
    """Decorator that adds a dependency for license validation based on the given tier.

    This decorator dynamically adds a parameter to the endpoint's signature:
      license_info: Annotated[LicenseInfo | None, Depends(_RequireLicense(tier=tier))]
    This allows FastAPI to resolve the dependency and include the parameter in the OpenAPI documentation,
    while the endpoint function itself does not need to explicitly declare the dependency parameter.

    Args:
        tier: The required license tier for self-hosted instances or
              cloud instances if cloud_free is False.
        cloud_free: If True, allows access on Lilypad Cloud regardless of the tier.
                    Defaults to False.
    """

    def decorator(func: _EndPointFunc) -> _EndPointFunc:
        # Create a new parameter for dependency injection
        new_param = inspect.Parameter(
            name="license_info",
            kind=inspect.Parameter.KEYWORD_ONLY,
            default=Depends(RequireLicense(tier=tier, cloud_free=cloud_free)),
            annotation="LicenseInfo | None",
        )

        # Retrieve the original function signature
        sig = inspect.signature(func)
        parameters = list(sig.parameters.values())

        # Insert the new parameter before any variadic keyword parameter (i.e. **kwargs)
        if "license_info" not in sig.parameters:
            insert_index = len(parameters)
            for i, param in enumerate(parameters):
                if param.kind == inspect.Parameter.VAR_KEYWORD:
                    insert_index = i
                    break
            parameters.insert(insert_index, new_param)

        # Create a new signature with the updated list of parameters
        new_sig = sig.replace(parameters=parameters)

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Remove license_info from kwargs since it is not needed inside the endpoint's logic
            kwargs.pop("license_info", None)
            return await func(*args, **kwargs)

        # Override the __signature__ attribute so FastAPI uses the updated signature
        wrapper.__signature__ = new_sig  # type: ignore

        return cast(_EndPointFunc, wrapper)

    return decorator


class RequireLicense:
    """License dependency for FastAPI endpoints."""

    def __init__(
        self, tier: Tier | None = Tier.ENTERPRISE, cloud_free: bool = False
    ) -> None:
        """Initialize with required tier and cloud behavior."""
        self.tier = tier
        self.cloud_free = cloud_free

    async def __call__(
        self,
        request: Request,
        project_uuid: UUID,
        project_service: Annotated[ProjectService, Depends(ProjectService)],
        organization_service: Annotated[
            OrganizationService, Depends(OrganizationService)
        ],
    ) -> LicenseInfo | None:
        """Validate license based on tier and environment (cloud/self-hosted)."""
        project = project_service.find_record_by_uuid(project_uuid)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        if not project.organization_uuid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project does not belong to an organization",
            )
        organization_uuid = project.organization_uuid

        is_cloud = is_lilypad_cloud(request)

        if is_cloud and self.cloud_free:
            return None  # pragma: no cover

        try:
            # Validate license using the LicenseValidator
            validator = LicenseValidator()
            license_info = validator.validate_license(
                organization_uuid, organization_service
            )

            if self.tier == Tier.FREE:
                return None

            if not license_info:
                raise LilypadForbiddenError(
                    detail="Invalid License. Contact support@mirascope.com to get one.",
                )

            if license_info.organization_uuid != organization_uuid:
                raise LilypadForbiddenError(
                    detail="License key does not match organization",
                )

            if license_info.is_expired:
                raise LilypadForbiddenError(  # pragma: no cover
                    detail="License has expired",
                )

            if self.tier and license_info.tier < self.tier:
                raise LilypadForbiddenError(
                    detail=f"License tier ({license_info.tier.name}) does not meet the required tier ({self.tier.name}). "
                    "Contact support@mirascope.com to upgrade.",
                )

            return license_info

        except LicenseError as e:
            raise LilypadForbiddenError(
                detail=str(e),
            )


def get_organization_license(
    user: Annotated[UserPublic, Depends(get_current_user)],
    organization_service: Annotated[OrganizationService, Depends(OrganizationService)],
    request: Request = None,  # pyright: ignore[reportArgumentType]
    billing_service: Annotated[BillingService | None, Depends(BillingService)] = None,
) -> LicenseInfo:
    """Get the license information for the organization"""
    if not user.active_organization_uuid:
        return LicenseInfo(  # pragma: no cover
            customer="",
            license_id="",
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            tier=Tier.FREE,
            organization_uuid=None,
        )

    is_cloud = request is not None and is_lilypad_cloud(request)

    # For Lilypad Cloud, get tier from billing table
    if is_cloud and billing_service is not None:
        tier = billing_service.get_tier_from_billing(
            user.active_organization_uuid
        )  # pragma: no cover
        return LicenseInfo(  # pragma: no cover
            customer="",
            license_id="",
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            tier=tier,
            organization_uuid=user.active_organization_uuid,
        )

    # For self-hosted, use license validator
    validator = LicenseValidator()
    license_info = validator.validate_license(
        user.active_organization_uuid, organization_service
    )
    if not license_info:
        return LicenseInfo(  # pragma: no cover
            customer="",
            license_id="",
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            tier=Tier.FREE,
            organization_uuid=user.active_organization_uuid,
        )
    return license_info


def is_lilypad_cloud(
    request: Request | None = None,
) -> bool:
    """Check if this is a Lilypad Cloud deployment.

    Args:
        request: Optional request object. If provided, checks request hostname.
                If not provided, only checks settings.

    Returns:
        True if this is a Lilypad Cloud deployment, False otherwise.
    """
    if request and request.url.hostname:
        return request.url.hostname.endswith(
            HOST_NAME
        ) or request.url.hostname.endswith(ALT_HOST_NAME)

    settings = get_settings()
    remote_hostname = settings.remote_client_hostname

    return bool(
        remote_hostname
        and (
            remote_hostname in (HOST_NAME, ALT_HOST_NAME)
            or remote_hostname.endswith(f".{HOST_NAME}")
            or remote_hostname.endswith(f".{ALT_HOST_NAME}")
        )
    )


def is_lilypad_cloud_dependency(request: Request) -> bool:
    """FastAPI dependency wrapper for is_lilypad_cloud.

    This is used when is_lilypad_cloud needs to be used as a FastAPI dependency.
    """
    return is_lilypad_cloud(request)
