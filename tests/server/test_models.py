"""Test cases for server models."""

import pytest
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


@pytest.fixture
def engine():
    """Create an in-memory database engine for testing."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create a new database session for testing."""
    with Session(engine) as session:
        yield session
        session.rollback()


def test_base_sql_model():
    """Test BaseSQLModel initialization."""

    class TestModel(BaseSQLModel, table=True):
        __tablename__ = "testmodel"
        id: int | None = Field(default=None, primary_key=True)
        name: str

    model = TestModel(name="test")
    assert model.name == "test"
    assert model.created_at is not None


def test_function_models():
    """Test Function model variants."""
    # Test FunctionCreate
    func_data = {
        "name": "test_func",
        "hash": "abc123",
        "code": "def test(): pass",
        "arg_types": {"arg1": "str"},
        "project_id": 1,
    }
    func_create = FunctionCreate(**func_data)
    assert func_create.name == "test_func"
    assert func_create.hash == "abc123"

    # Test FunctionPublic
    func_public = FunctionPublic(
        id=1, **{k: v for k, v in func_data.items() if k != "project_id"}
    )
    assert func_public.id == 1
    assert func_public.name == "test_func"


def test_project_models(session):
    """Test Project model variants and relationships."""
    # Test ProjectCreate
    proj_create = ProjectCreate(name="test_project")
    assert proj_create.name == "test_project"

    # Test ProjectTable with relationships
    proj_table = ProjectTable(name="test_project")
    session.add(proj_table)
    session.commit()
    session.refresh(proj_table)

    assert proj_table.id is not None
    assert proj_table.name == "test_project"
    assert proj_table.functions == []
    assert proj_table.prompts == []
    assert proj_table.versions == []

    # Test ProjectPublic
    proj_public = ProjectPublic(
        id=1, name="test_project", functions=[], prompts=[], versions=[]
    )
    assert proj_public.id == 1
    assert proj_public.name == "test_project"


def test_prompt_models():
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
    prompt_public = PromptPublic(id=1, **prompt_data)
    assert prompt_public.id == 1
    assert prompt_public.template == "Test template"

    # Test ResponseFormat
    resp_format = ResponseFormat(type="json_object")
    assert resp_format.type == "json_object"


def test_span_models():
    """Test Span model variants."""
    # Test SpanCreate
    span_create = SpanCreate(
        id="span123",
        project_id=1,
        version_id=1,
        version_num=1,
        scope=Scope.LILYPAD,
        data={"key": "value"},
    )
    assert span_create.id == "span123"
    assert span_create.scope == Scope.LILYPAD

    # Test SpanPublic display name conversion for LILYPAD scope
    lilypad_span = SpanTable(
        id="span123",
        project_id=1,
        version_id=1,
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
        id="span456",
        project_id=1,
        version_id=1,
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


def test_version_models():
    """Test Version model variants."""
    version_data = {
        "version_num": 1,
        "project_id": 1,
        "function_id": 1,
        "function_name": "test_func",
        "function_hash": "abc123",
    }

    # Test VersionCreate
    version_create = VersionCreate(**version_data)
    assert version_create.version_num == 1
    assert version_create.function_name == "test_func"

    # Test VersionPublic
    version_public = VersionPublic(
        id=1,
        **version_data,
        function=FunctionPublic(
            id=1, name="test_func", hash="abc123", code="def test(): pass"
        ),
        prompt=None,
        spans=[],
    )
    assert version_public.id == 1
    assert version_public.function.name == "test_func"

    # Test ActiveVersionPublic
    active_version = ActiveVersionPublic(
        id=1,
        **version_data,
        function=FunctionPublic(
            id=1, name="test_func", hash="abc123", code="def test(): pass"
        ),
        prompt=PromptPublic(
            id=1,
            hash="def123",
            template="Test template",
            provider=Provider.OPENAI,
            model="gpt-4",
        ),
        spans=[],
    )
    assert active_version.id == 1
    assert active_version.prompt.provider == Provider.OPENAI


def test_relationships(session):
    """Test model relationships and cascading deletes."""
    # Create test project
    project = ProjectTable(name="test_project")
    session.add(project)
    session.commit()

    # Create function linked to project
    function = FunctionTable(
        name="test_func", hash="abc123", code="def test(): pass", project_id=project.id
    )
    session.add(function)
    session.commit()

    # Create version linked to function and project
    version = VersionTable(
        version_num=1,
        project_id=project.id,
        function_id=function.id,
        function_name="test_func",
        function_hash="abc123",
    )
    session.add(version)
    session.commit()

    # Create prompt linked to project
    prompt = PromptTable(
        hash="def123",
        template="Test template",
        provider=Provider.OPENAI,
        model="gpt-4",
        project_id=project.id,
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
    assert session.get(FunctionTable, function.id) is None
    assert session.get(VersionTable, version.id) is None
    assert session.get(PromptTable, prompt.id) is None


def test_provider_enum():
    """Test Provider enum values."""
    assert Provider.OPENAI.value == "openai"
    assert Provider.ANTHROPIC.value == "anthropic"
    assert Provider.OPENROUTER.value == "openrouter"
    assert Provider.GEMINI.value == "gemini"


def test_scope_enum():
    """Test Scope enum values."""
    assert Scope.LILYPAD.value == "lilypad"
    assert Scope.LLM.value == "llm"
