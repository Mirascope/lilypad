"""The `APIKeyService` class for api_keys."""

from typing import Any

from ..models import APIKeyTable
from ..schemas import APIKeyCreate
from .base_organization import BaseOrganizationService


class APIKeyService(BaseOrganizationService[APIKeyTable, APIKeyCreate]):
    """The service class for api_keys."""

    table: type[APIKeyTable] = APIKeyTable
    create_model: type[APIKeyCreate] = APIKeyCreate

    def create_record(self, data: APIKeyCreate, **kwargs: Any) -> APIKeyTable:
        """Create a new api key"""
        return super().create_record(
            data,
            user_uuid=self.user.uuid,
            **kwargs,
        )
