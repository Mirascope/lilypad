"""The `SpanService` class for spans."""

from ..models import SpanCreate, SpanTable
from .base import BaseService


class SpanService(BaseService[SpanTable, SpanCreate]):
    """The service class for spans."""

    table: type[SpanTable] = SpanTable
    create_model: type[SpanCreate] = SpanCreate
