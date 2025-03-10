"""Test cases for server models."""

from collections.abc import Generator
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Engine
from sqlmodel import Field, Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from lilypad.server.models import (
    BaseSQLModel,
    GenerationTable,
    ProjectTable,
    Scope,
    SpanTable,
    SpanType,
)
from lilypad.server.schemas import (
    GenerationCreate,
    GenerationPublic,
    ProjectCreate,
    ProjectPublic,
    Provider,
    SpanCreate,
    SpanPublic,
)

ORGANIZATION_UUID = UUID("12345678-1234-1234-1234-123456789abc")


@pytest.fixture
def engine() -> Engine:
    """Create an in-memory database engine for testing."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine) -> Generator[Session, None, None]:
    """Create a new database session for testing."""
    with Session(engine) as session:
        yield session
        session.rollback()


def test_base_sql_model() -> None:
    """Test BaseSQLModel initialization."""

    class TestModel(BaseSQLModel, table=True):
        __tablename__ = "testmodel"  # pyright: ignore [reportAssignmentType]
        id: int | None = Field(default=None, primary_key=True)
        name: str

    model = TestModel(name="test")
    assert model.name == "test"
    assert model.created_at is not None


def test_generation_models() -> None:
    """Test Generation model variants."""
    # Test GenerationCreate
    generation_data = {
        "name": "test_func",
        "signature": "def test(): pass",
        "code": "def test(): pass",
        "hash": "abc123",
        "dependencies": {},
        "arg_types": {"arg1": "str"},
        "project_uuid": uuid4(),
    }
    func_create = GenerationCreate(**generation_data)
    assert func_create.name == "test_func"
    assert func_create.hash == "abc123"

    # Test FunctionPublic
    uuid = uuid4()
    func_public = GenerationPublic(
        uuid=uuid, **{k: v for k, v in generation_data.items() if k != "project_uuid"}
    )
    assert func_public.uuid == uuid
    assert func_public.name == "test_func"


def test_project_models(session) -> None:
    """Test Project model variants and relationships."""
    # Test ProjectCreate
    proj_create = ProjectCreate(name="test_project")
    assert proj_create.name == "test_project"

    # Test ProjectTable with relationships
    proj_table = ProjectTable(name="test_project", organization_uuid=ORGANIZATION_UUID)
    session.add(proj_table)
    session.commit()
    session.refresh(proj_table)

    assert proj_table.uuid is not None
    assert proj_table.name == "test_project"
    assert proj_table.generations == []

    # Test ProjectPublic
    uuid = uuid4()
    proj_public = ProjectPublic(
        uuid=uuid,
        name="test_project",
        generations=[],
        created_at=proj_table.created_at,
    )
    assert proj_public.uuid == uuid
    assert proj_public.name == "test_project"


def test_span_models() -> None:
    """Test Span model variants."""
    # Test SpanCreate
    span_create = SpanCreate(
        span_id="span123",
        project_uuid=uuid4(),
        generation_uuid=uuid4(),
        scope=Scope.LILYPAD,
        data={"key": "value"},
    )
    assert span_create.span_id == "span123"
    assert span_create.scope == Scope.LILYPAD

    # Test SpanPublic display name conversion for LILYPAD scope
    lilypad_span = SpanTable(
        organization_uuid=ORGANIZATION_UUID,
        span_id="span123",
        project_uuid=uuid4(),
        generation_uuid=uuid4(),
        scope=Scope.LILYPAD,
        data={
            "name": "test_span",
            "attributes": {
                "lilypad.type": "generation",
                "lilypad.generation.name": "test_function",
            },
        },
    )
    lilypad_span_public = SpanPublic.model_validate(lilypad_span)

    assert lilypad_span_public.display_name == "test_span"

    # Test LLM scope display name
    llm_span = SpanTable(
        organization_uuid=ORGANIZATION_UUID,
        span_id="span456",
        project_uuid=uuid4(),
        generation_uuid=uuid4(),
        type=SpanType.GENERATION,
        scope=Scope.LLM,
        data={
            "name": "llm_span",
            "attributes": {
                "gen_ai.system": "test_system",
                "gen_ai.request.model": "test_model",
            },
        },
    )
    llm_span_public = SpanPublic.model_validate(llm_span)
    assert llm_span_public.display_name == "test_system with 'test_model'"


def test_relationships(session) -> None:
    """Test model relationships and cascading deletes."""
    # Create test project
    project = ProjectTable(
        name="test_project",
        organization_uuid=ORGANIZATION_UUID,
    )
    session.add(project)
    session.commit()

    # Create generation linked to project
    generation = GenerationTable(
        organization_uuid=ORGANIZATION_UUID,
        name="test_func",
        signature="def test(): pass",
        code="def test(): pass",
        hash="abc123",
        project_uuid=project.uuid,  # pyright: ignore [reportArgumentType]
    )
    session.add(generation)
    session.commit()

    # Test relationships
    assert generation in project.generations

    # Test cascade delete
    session.delete(project)
    session.commit()

    # Verify all related records are deleted
    assert session.get(GenerationTable, generation.uuid) is None


def test_provider_enum() -> None:
    """Test Provider enum values."""
    assert Provider.OPENAI.value == "openai"
    assert Provider.ANTHROPIC.value == "anthropic"
    assert Provider.OPENROUTER.value == "openrouter"
    assert Provider.GEMINI.value == "gemini"


def test_scope_enum() -> None:
    """Test Scope enum values."""
    assert Scope.LILYPAD.value == "lilypad"
    assert Scope.LLM.value == "llm"
