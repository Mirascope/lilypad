"""The `/organizations` API router."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError

from ee import LicenseValidator
from ee.validate import LicenseError

from ....ee.server.models.user_organizations import UserRole
from ....ee.server.require_license import is_lilypad_cloud
from ....ee.server.schemas.user_organizations import UserOrganizationCreate
from ....ee.server.services.user_organizations import UserOrganizationService
from ....server._utils.auth import create_jwt_token
from ..._utils import get_current_user
from ...models import (
    OrganizationTable,
)
from ...schemas.organizations import (
    OrganizationCreate,
    OrganizationPublic,
    OrganizationUpdate,
)
from ...schemas.users import (
    UserPublic,
)
from ...services import OrganizationService, UserService
from ...services.billing import BillingService

organization_router = APIRouter()


@organization_router.post(
    "/organizations",
    response_model=OrganizationPublic,
)
async def create_organization(
    organization_service: Annotated[OrganizationService, Depends(OrganizationService)],
    user_organization_service: Annotated[
        UserOrganizationService, Depends(UserOrganizationService)
    ],
    organization_create: OrganizationCreate,
    user: Annotated[UserPublic, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(UserService)],
    billing_service: Annotated[BillingService, Depends(BillingService)],
    is_lilypad_cloud: Annotated[bool, Depends(is_lilypad_cloud)],
) -> OrganizationTable:
    """Create an organization."""
    try:
        organization = organization_service.create_record(organization_create)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Name already exists",
        )
    if is_lilypad_cloud and billing_service and user.email:
        billing_service.create_customer(organization, user.email)  # pragma: no cover
    user_service.update_user_active_organization_uuid(organization.uuid)
    user_organization = UserOrganizationCreate(
        user_uuid=user.uuid,
        role=UserRole.OWNER,
    )
    user_organization_service.create_record(
        user_organization, organization_uuid=organization.uuid
    )
    return organization


@organization_router.delete("/organizations", response_model=UserPublic)
async def delete_organization(
    request: Request,
    organization_service: Annotated[OrganizationService, Depends(OrganizationService)],
    user_organization_service: Annotated[
        UserOrganizationService, Depends(UserOrganizationService)
    ],
    user_service: Annotated[UserService, Depends(UserService)],
    user: Annotated[UserPublic, Depends(get_current_user)],
    billing_service: Annotated[BillingService, Depends(BillingService)],
) -> UserPublic:
    """Delete an organization."""
    if not user.active_organization_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have an active organization",
        )
    user_org = user_organization_service.get_active_user_organization()
    if not user_org.role == UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owner can remove organization",
        )

    is_cloud = request is not None and is_lilypad_cloud(request)
    if is_cloud:
        # Order matters, we need to grab billing info before deleting the organization
        billing_service.delete_customer_and_billing(
            user.active_organization_uuid
        )  # pragma: no cover
    deleted = organization_service.delete_record_by_uuid(user.active_organization_uuid)
    if not deleted:
        raise HTTPException(  # pragma: no cover
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization not found",
        )
    user_organizations = user_organization_service.find_user_organizations()
    updated_user = user_service.update_user_active_organization_uuid(
        user_organizations[0].organization_uuid if user_organizations else None
    )
    user_public = UserPublic.model_validate(updated_user)
    user_public.access_token = create_jwt_token(user_public)
    return user_public


@organization_router.patch(
    "/organizations",
    response_model=OrganizationPublic,
)
async def update_organization(
    request: Request,
    organization_service: Annotated[OrganizationService, Depends(OrganizationService)],
    user_organization_service: Annotated[
        UserOrganizationService, Depends(UserOrganizationService)
    ],
    organization_update: OrganizationUpdate,
    user: Annotated[UserPublic, Depends(get_current_user)],
    billing_service: Annotated[BillingService, Depends(BillingService)],
) -> OrganizationTable:
    """Update an organization."""
    # Check if user is in organization
    if not user.active_organization_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have an active organization",
        )
    user_org = user_organization_service.get_active_user_organization()
    if not user_org.role == UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owner can update organization",
        )

    # If updating license, validate it
    organization = organization_update.model_dump(exclude_unset=True)
    if (
        "license" in organization
        and (new_license := organization["license"]) is not None
    ):
        try:
            validator = LicenseValidator()
            validator.verify_license(new_license, user.active_organization_uuid)
        except LicenseError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid license key: {str(e)}",
            )
    updated_org = organization_service.update_record_by_uuid(
        user.active_organization_uuid, organization
    )
    is_cloud = request is not None and is_lilypad_cloud(request)
    if is_cloud and updated_org.billing.stripe_customer_id:
        billing_service.update_customer(  # pragma: no cover
            updated_org.billing.stripe_customer_id, updated_org.name
        )
    return updated_org
