"""Tool for the database."""

from uuid import UUID

from lilypad.server.models.tools import _ToolBase


class ToolPublic(_ToolBase):
    """Public model for tools."""

    uuid: UUID


class ToolCreate(_ToolBase):
    """Create model for tools."""
