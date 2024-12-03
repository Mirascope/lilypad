"""Test cases for server models."""

from collections.abc import Generator
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Engine
from sqlmodel import Field, Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from lilypad.server.models import (
    ActiveVersionPublic,
    BaseSQLModel,
    FunctionCreate,
    FunctionPublic,
    FunctionTable,
    ProjectCreate,
    ProjectPublic,
    ProjectTable,
    PromptCreate,
    PromptPublic,
    PromptTable,
    Provider,
    ResponseFormat,
    Scope,
    SpanCreate,
    SpanPublic,
    SpanTable,
    VersionCreate,
    VersionPublic,
    VersionTable,
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


def test_function_models() -> None:
    """Test Function model variants."""
    # Test FunctionCreate
    func_data = {
        "name": "test_func",
        "hash": "abc123",
        "code": "def test(): pass",
        "arg_types": {"arg1": "str"},
        "project_uuid": 1,
    }
    func_create = FunctionCreate(**func_data)
    assert func_create.name == "test_func"
    assert func_create.hash == "abc123"

    # Test FunctionPublic
    uuid = uuid4()
    func_public = FunctionPublic(
        uuid=uuid, **{k: v for k, v in func_data.items() if k != "project_uuid"}
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
    assert proj_table.functions == []
    assert proj_table.prompts == []
    assert proj_table.versions == []

    # Test ProjectPublic
    uuid = uuid4()
    proj_public = ProjectPublic(
        uuid=uuid, name="test_project", functions=[], prompts=[], versions=[]
    )
    assert proj_public.uuid == uuid
    assert proj_public.name == "test_project"


def test_prompt_models() -> None:
    """Test Prompt model variants."""
    prompt_data = {
        "hash": "def123",
        "template": "Test template",
        "provider": Provider.OPENAI,
        "model": "gpt-4",
    }

    # Test PromptCreate
    prompt_create = PromptCreate(**prompt_data)
    assert prompt_create.hash == "def123"
    assert prompt_create.provider == Provider.OPENAI

    # Test PromptPublic
    uuid = uuid4()
    prompt_public = PromptPublic(uuid=uuid, **prompt_data)
    assert prompt_public.uuid == uuid
    assert prompt_public.template == "Test template"

    # Test ResponseFormat
    resp_format = ResponseFormat(type="json_object")
    assert resp_format.type == "json_object"


def test_span_models() -> None:
    """Test Span model variants."""
    # Test SpanCreate
    span_create = SpanCreate(
        span_id="span123",
        project_uuid=uuid4(),
        version_uuid=uuid4(),
        version_num=1,
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
        version_uuid=uuid4(),
        version_num=1,
        scope=Scope.LILYPAD,
        data={
            "name": "test_span",
            "attributes": {
                "lilypad.function_name": "test_function",
                "lilypad.version_num": 1,
            },
        },
    )
    lilypad_span_public = SpanPublic.model_validate(lilypad_span)
    assert lilypad_span_public.display_name == "test_function"

    # Test LLM scope display name
    llm_span = SpanTable(
        organization_uuid=ORGANIZATION_UUID,
        span_id="span456",
        project_uuid=uuid4(),
        version_uuid=uuid4(),
        version_num=1,
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


def test_version_models() -> None:
    """Test Version model variants."""
    version_data = {
        "version_num": 1,
        "project_uuid": uuid4(),
        "function_uuid": uuid4(),
        "function_name": "test_func",
        "function_hash": "abc123",
    }

    # Test VersionCreate
    version_create = VersionCreate(**version_data)
    assert version_create.version_num == 1
    assert version_create.function_name == "test_func"

    # Test VersionPublic
    uuid = uuid4()
    version_public = VersionPublic(
        uuid=uuid,
        **version_data,
        function=FunctionPublic(
            uuid=uuid4(), name="test_func", hash="abc123", code="def test(): pass"
        ),
        prompt=None,
        spans=[],
    )
    assert version_public.uuid == uuid
    assert version_public.function.name == "test_func"

    # Test ActiveVersionPublic
    uuid = uuid4()
    active_version = ActiveVersionPublic(
        uuid=uuid,
        **version_data,
        function=FunctionPublic(
            uuid=uuid4(), name="test_func", hash="abc123", code="def test(): pass"
        ),
        prompt=PromptPublic(
            uuid=uuid4(),
            hash="def123",
            template="Test template",
            provider=Provider.OPENAI,
            model="gpt-4",
        ),
        spans=[],
    )
    assert active_version.uuid == uuid
    assert active_version.prompt.provider == Provider.OPENAI


def test_relationships(session) -> None:
    """Test model relationships and cascading deletes."""
    # Create test project
    project = ProjectTable(
        name="test_project",
        organization_uuid=ORGANIZATION_UUID,
    )
    session.add(project)
    session.commit()

    # Create function linked to project
    function = FunctionTable(
        organization_uuid=ORGANIZATION_UUID,
        name="test_func",
        hash="abc123",
        code="def test(): pass",
        project_uuid=project.uuid,  # pyright: ignore [reportArgumentType]
    )
    session.add(function)
    session.commit()

    # Create version linked to function and project
    version = VersionTable(
        organization_uuid=ORGANIZATION_UUID,
        version_num=1,
        project_uuid=project.uuid,
        function_uuid=function.uuid,
        function_name="test_func",
        function_hash="abc123",
    )
    session.add(version)
    session.commit()

    # Create prompt linked to project
    prompt = PromptTable(
        organization_uuid=ORGANIZATION_UUID,
        hash="def123",
        template="Test template",
        provider=Provider.OPENAI,
        model="gpt-4",
        project_uuid=project.uuid,  # pyright: ignore [reportArgumentType]
    )
    session.add(prompt)
    session.commit()

    # Test relationships
    assert function in project.functions
    assert version in project.versions
    assert prompt in project.prompts
    assert version in function.versions

    # Test cascade delete
    session.delete(project)
    session.commit()

    # Verify all related records are deleted
    assert session.get(FunctionTable, function.uuid) is None
    assert session.get(VersionTable, version.uuid) is None
    assert session.get(PromptTable, prompt.uuid) is None


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
