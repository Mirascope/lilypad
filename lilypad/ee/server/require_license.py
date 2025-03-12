"""License validation module for Lilypad Enterprise Edition"""

import functools
import inspect
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status

from ee import LicenseInfo, LicenseValidator, Tier

from ...ee.server import HOST_NAME
from ...exceptions import LicenseError
from ...server._utils import get_current_user
from ...server.exceptions import LilypadForbiddenError
from ...server.schemas import UserPublic
from ...server.services import OrganizationService, ProjectService

_EndPointFunc = TypeVar("_EndPointFunc", bound=Callable[..., Awaitable[Any]])


def require_license(tier: Tier) -> Callable[[_EndPointFunc], _EndPointFunc]:
    """Decorator that adds a dependency for license validation based on the given tier.

    This decorator dynamically adds a parameter to the endpoint's signature:
      license_info: Annotated[LicenseInfo | None, Depends(_RequireLicense(tier=tier))]
    This allows FastAPI to resolve the dependency and include the parameter in the OpenAPI documentation,
    while the endpoint function itself does not need to explicitly declare the dependency parameter.
    """

    def decorator(func: _EndPointFunc) -> _EndPointFunc:
        # Create a new parameter for dependency injection
        new_param = inspect.Parameter(
            name="license_info",
            kind=inspect.Parameter.KEYWORD_ONLY,
            default=Depends(RequireLicense(tier=tier)),
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

    def __init__(self, tier: Tier | None = Tier.ENTERPRISE) -> None:
        """Initialize with required tier."""
        self.tier = tier

    async def __call__(
        self,
        project_uuid: UUID,
        project_service: Annotated[ProjectService, Depends(ProjectService)],
        organization_service: Annotated[
            OrganizationService, Depends(OrganizationService)
        ],
    ) -> LicenseInfo | None:
        """Validate license and return license info if valid."""
        # Get project record by UUID
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
                raise LilypadForbiddenError(
                    detail="License has expired",
                )

            if self.tier and license_info.tier < self.tier:
                raise LilypadForbiddenError(
                    detail="Invalid License. Contact support@mirascope.com to get one.",
                )

            return license_info

        except LicenseError as e:
            raise LilypadForbiddenError(
                detail=str(e),
            )


async def get_organization_license(
    user: Annotated[UserPublic, Depends(get_current_user)],
    organization_service: Annotated[OrganizationService, Depends(OrganizationService)],
) -> LicenseInfo:
    """Get the license information for the organization"""
    if not user.active_organization_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have an active organization.",
        )
    validator = LicenseValidator()
    license_info = validator.validate_license(
        user.active_organization_uuid, organization_service
    )
    if not license_info:
        return LicenseInfo(
            customer="",
            license_id="",
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            tier=Tier.FREE,
            organization_uuid=user.active_organization_uuid,
        )
    return license_info


async def is_lilypad_cloud(
    request: Request,
) -> bool:
    """Check if the request is to Lilypad Cloud"""
    return request.url.hostname is not None and request.url.hostname.endswith(HOST_NAME)
