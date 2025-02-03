"""Response Model for the database."""

from uuid import UUID

from lilypad.server.models.response_models import _ResponseModelBase


class ResponseModelPublic(_ResponseModelBase):
    """Public model for response models."""

    uuid: UUID


class ResponseModelCreate(_ResponseModelBase):
    """Create model for response models."""
