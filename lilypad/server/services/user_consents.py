"""The `UserConsentService` class for user_consents."""

from ..models.user_consents import UserConsentTable
from ..schemas.user_consents import UserConsentCreate
from .base import BaseService


class UserConsentService(BaseService[UserConsentTable, UserConsentCreate]):
    """The service class for organization_invotes."""

    table: type[UserConsentTable] = UserConsentTable
    create_model: type[UserConsentCreate] = UserConsentCreate
