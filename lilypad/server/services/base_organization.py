"""The `BaseOrganizationService` class from which all organization services inherit."""

from collections.abc import Sequence
from typing import Any, TypeVar
from uuid import UUID

from pydantic import BaseModel

from ..models import BaseOrganizationSQLModel
from .base import BaseService

_TableT = TypeVar("_TableT", bound=BaseOrganizationSQLModel)
_CreateT = TypeVar("_CreateT", bound=BaseModel)


class BaseOrganizationService(BaseService[_TableT, _CreateT]):
    """Base class for all services that are under an organization."""

    def find_record_by_uuid(self, uuid: UUID, **filters: Any) -> _TableT:
        """Find record by uuid with organization filter"""
        organization_uuid = filters.pop(
            "organization_uuid", self.user.active_organization_uuid
        )
        return super().find_record_by_uuid(
            uuid, organization_uuid=organization_uuid, **filters
        )

    def find_all_records(self, **filters: Any) -> Sequence[_TableT]:
        """Find all records with organization filter"""
        organization_uuid = filters.pop(
            "organization_uuid", self.user.active_organization_uuid
        )
        return super().find_all_records(organization_uuid=organization_uuid, **filters)

    def create_record(self, data: _CreateT, **kwargs: Any) -> _TableT:
        """Create a new record with organization"""
        organization_uuid = kwargs.pop(
            "organization_uuid", self.user.active_organization_uuid
        )
        return super().create_record(
            data, organization_uuid=organization_uuid, **kwargs
        )
