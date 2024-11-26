"""The `PromptService` class for prompts."""

from sqlmodel import select

from ..models import PromptCreate, PromptTable
from .base import BaseService


class PromptService(BaseService[PromptTable, PromptCreate]):
    """The service class for functions."""

    table: type[PromptTable] = PromptTable
    create_model: type[PromptCreate] = PromptCreate

    def find_prompt_by_call_params(
        self, prompt_create: PromptCreate
    ) -> PromptTable | None:
        """Find prompt by call params"""
        call_params = (
            prompt_create.call_params.model_dump()
            if prompt_create.call_params
            else None
        )
        return self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.hash == prompt_create.hash,
                self.table.call_params == call_params,
                self.table.model == prompt_create.model,
                self.table.provider == prompt_create.provider,
            )
        ).first()
