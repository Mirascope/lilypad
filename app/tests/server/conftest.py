"""Test configuration and fixtures."""

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import pytest
from sqlmodel import Session, SQLModel, create_engine

from lilypad.ee.server.models import UserRole
from lilypad.ee.server.schemas.user_organizations import UserOrganizationPublic
from lilypad.server.schemas.organizations import (
    OrganizationPublic,
)
from lilypad.server.schemas.users import (
    UserPublic,
)

# In-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

ORGANIZATION_UUID = UUID("12345678-1234-1234-1234-123456789abc")


def get_session():
    """Get database session."""
    with Session(engine) as session:
        yield session


@pytest.fixture(autouse=True)
def setup_test_db():
    """Set up test database."""
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def db_session():
    """Get database session."""
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user() -> UserPublic:
    """Create a test user and organization."""
    user_uuid = uuid4()
    organization = OrganizationPublic(uuid=ORGANIZATION_UUID, name="Test Organization")
    user_org = UserOrganizationPublic(
        uuid=uuid4(),
        user_uuid=user_uuid,
        organization_uuid=ORGANIZATION_UUID,
        role=UserRole.ADMIN,
        organization=organization,
    )
    user_public = UserPublic(
        uuid=user_uuid,
        email="test@test.com",
        first_name="Test User",
        active_organization_uuid=ORGANIZATION_UUID,
        user_organizations=[user_org],
    )

    return user_public


@pytest.fixture
def get_test_current_user(test_user: UserPublic):
    """Override the get_current_user dependency for FastAPI.

    Returns:
        UserPublic: Test user
    """

    def override_get_current_user():
        return test_user

    return override_get_current_user


# ===== Stripe Mock Fixtures =====

@pytest.fixture
def mock_stripe_customer():
    """Mock Stripe customer data."""
    return {
        "id": "cus_test123",
        "email": "test@example.com",
        "metadata": {"organization_uuid": str(ORGANIZATION_UUID)},
        "created": 1234567890,
    }


@pytest.fixture
def mock_stripe_subscription():
    """Mock Stripe subscription data."""
    return {
        "id": "sub_test123",
        "customer": "cus_test123",
        "status": "active",
        "current_period_start": 1234567890,
        "current_period_end": 1234567890,
        "items": {
            "data": [
                {
                    "id": "si_test123",
                    "price": {"id": "price_test123", "product": "prod_test123"},
                }
            ]
        },
    }


@pytest.fixture
def mock_stripe_invoice():
    """Mock Stripe invoice data."""
    return {
        "id": "inv_test123",
        "customer": "cus_test123",
        "subscription": "sub_test123",
        "amount_paid": 2000,
        "currency": "usd",
        "status": "paid",
    }


@pytest.fixture
def mock_stripe_service():
    """Mock Stripe service with common methods."""
    with patch("stripe.Customer") as mock_customer, \
         patch("stripe.Subscription") as mock_subscription, \
         patch("stripe.Invoice") as mock_invoice:
        
        mock_customer.create = Mock(return_value={"id": "cus_test123"})
        mock_customer.retrieve = Mock(return_value={"id": "cus_test123"})
        mock_subscription.create = Mock(return_value={"id": "sub_test123"})
        mock_invoice.list = Mock(return_value={"data": []})
        
        yield {
            "customer": mock_customer,
            "subscription": mock_subscription,
            "invoice": mock_invoice,
        }


# ===== Kafka Mock Fixtures =====

@pytest.fixture
def mock_kafka_producer():
    """Mock Kafka producer."""
    producer = AsyncMock()
    producer.send = AsyncMock(return_value=None)
    producer.flush = AsyncMock(return_value=None)
    return producer


@pytest.fixture
def mock_kafka_consumer():
    """Mock Kafka consumer."""
    consumer = AsyncMock()
    consumer.subscribe = AsyncMock(return_value=None)
    consumer.poll = AsyncMock(return_value={})
    consumer.commit = AsyncMock(return_value=None)
    return consumer


# ===== OpenSearch Mock Fixtures =====

@pytest.fixture
def mock_opensearch_client():
    """Mock OpenSearch client."""
    client = AsyncMock()
    client.index = AsyncMock(return_value={"_id": "test_id"})
    client.search = AsyncMock(return_value={
        "hits": {
            "total": {"value": 0},
            "hits": []
        }
    })
    client.delete = AsyncMock(return_value={"result": "deleted"})
    return client


# ===== Common Test Data Fixtures =====

@pytest.fixture
def sample_span_data():
    """Sample span data for testing."""
    return {
        "name": "test_span",
        "start_time": datetime.now(timezone.utc).isoformat(),
        "end_time": datetime.now(timezone.utc).isoformat(),
        "attributes": {"key": "value"},
        "span_type": "DEFAULT",
    }


@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "name": "Test Project",
        "description": "Test project description",
        "metadata": {"test": True},
    }


@pytest.fixture
def sample_api_key_data():
    """Sample API key data for testing."""
    return {
        "name": "Test API Key",
        "scopes": ["read", "write"],
        "expires_at": None,
    }


@pytest.fixture
def sample_comment_data():
    """Sample comment data for testing."""
    return {
        "content": "Test comment content",
        "metadata": {"author": "test"},
    }


# ===== Auth Mock Fixtures =====

@pytest.fixture
def mock_oauth_provider():
    """Mock OAuth provider responses."""
    return {
        "google": {
            "userinfo": {
                "email": "test@gmail.com",
                "given_name": "Test",
                "family_name": "User",
                "picture": "https://example.com/pic.jpg",
            },
            "token": {
                "access_token": "google_access_token",
                "token_type": "Bearer",
            }
        },
        "github": {
            "user": {
                "email": "test@github.com",
                "login": "testuser",
                "name": "Test User",
                "avatar_url": "https://github.com/avatar.jpg",
            },
            "token": {
                "access_token": "github_access_token",
                "token_type": "bearer",
            }
        }
    }


@pytest.fixture
def auth_headers(test_user: UserPublic):
    """Auth headers for API requests."""
    return {"Authorization": f"Bearer test_token_{test_user.uuid}"}


# ===== Response Mock Fixtures =====

@pytest.fixture
def success_response():
    """Generic success response."""
    def _response(data: Any = None):
        return {
            "success": True,
            "data": data or {},
            "message": "Operation successful"
        }
    return _response


@pytest.fixture
def error_response():
    """Generic error response."""
    def _response(message: str = "Error occurred", code: int = 400):
        return {
            "success": False,
            "error": message,
            "code": code
        }
    return _response


# ===== Database Record Fixtures =====

@pytest.fixture
def create_test_records(db_session: Session):
    """Factory fixture for creating test records."""
    created_records = []
    
    def _create_record(table_class, **kwargs):
        record = table_class(**kwargs)
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)
        created_records.append(record)
        return record
    
    yield _create_record
    
    # Cleanup
    for record in reversed(created_records):
        db_session.delete(record)
    db_session.commit()


# ===== Async Mock Fixtures =====

@pytest.fixture
def async_mock():
    """Create an async mock."""
    return AsyncMock()


@pytest.fixture
def mock_async_session():
    """Mock async database session."""
    session = AsyncMock()
    session.exec = AsyncMock()
    session.add = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session
