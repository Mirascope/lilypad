"""The `PromptService` class for prompts."""

from ..models import PromptCreate, PromptTable
from .base import BaseService


class PromptService(BaseService[PromptTable, PromptCreate]):
    """The service class for functions."""

    table: type[PromptTable] = PromptTable
    create_model: type[PromptCreate] = PromptCreate
