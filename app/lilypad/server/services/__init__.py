"""Services for the `lilypad` server.

IMPORTANT: Circular Dependency Management
-----------------------------------------
This module exports commonly used services. When adding new service exports,
be aware of potential circular dependencies:

1. BillingService is imported by several services (spans, data_retention, etc.)
2. BillingService itself imports StripeKafkaService
3. To avoid circular imports in the future:
   - Keep service dependencies minimal
   - Use static methods for shared functionality
   - Consider using TYPE_CHECKING imports for type hints only
   - If circular dependencies arise, remove the problematic import from __all__
     and require direct imports (e.g., from .billing import BillingService)
"""

from .api_keys import APIKeyService
from .billing import BillingService
from .comments import CommentService
from .deployments import DeploymentService
from .environments import EnvironmentService
from .functions import FunctionService
from .kafka_base import BaseKafkaService
from .kafka_producer import close_kafka_producer, get_kafka_producer
from .opensearch import OpenSearchService, SearchQuery, get_opensearch_service
from .organization_invites import OrganizationInviteService
from .organizations import OrganizationService
from .projects import ProjectService
from .span_kafka_service import SpanKafkaService, get_span_kafka_service
from .spans import SpanService
from .stripe_kafka_service import StripeKafkaService, get_stripe_kafka_service
from .tags import TagService
from .user_consents import UserConsentService
from .users import UserService

__all__ = [
    "APIKeyService",
    "BillingService",
    "CommentService",
    "DeploymentService",
    "EnvironmentService",
    "FunctionService",
    "BaseKafkaService",
    "SpanKafkaService",
    "get_span_kafka_service",
    "StripeKafkaService",
    "get_stripe_kafka_service",
    "get_kafka_producer",
    "close_kafka_producer",
    "OpenSearchService",
    "SearchQuery",
    "get_opensearch_service",
    "OrganizationInviteService",
    "OrganizationService",
    "ProjectService",
    "SpanService",
    "TagService",
    "UserConsentService",
    "UserService",
]
