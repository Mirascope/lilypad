"""SpanService class"""

from lilypad.models import SpanCreate
from lilypad.server.models import SpanTable

from . import BaseService


class SpanService(BaseService[SpanTable, SpanCreate]):
    """SpanService class"""

    table: type[SpanTable] = SpanTable
    create_model: type[SpanCreate] = SpanCreate
