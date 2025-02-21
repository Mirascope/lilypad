"""Unit tests for the generations module."""

from unittest.mock import patch
from uuid import uuid4

import pytest

from lilypad.generations import generation
from lilypad.server.schemas.generations import GenerationPublic

dummy_spans = []


@pytest.fixture
def dummy_generation_instance() -> GenerationPublic:
    """Return a dummy GenerationPublic instance."""
    return GenerationPublic(
        uuid=uuid4(),
        name="dummy_generation",
        signature="dummy_signature",
        code="def dummy(): pass",
        hash="dummy_hash",
        dependencies={},
        arg_types={},
        version_num=1,
        call_params={"provider": "openai", "model": "gpt-4o-mini"},
    )


class DummySpan:
    """A dummy span that records its name and attributes."""

    def __init__(self, name: str):
        self.name = name
        self.attributes = {}
        dummy_spans.append(self)

    def set_attribute(self, key: str, value: any) -> None:
        """Set a single attribute."""
        self.attributes[key] = value

    def set_attributes(self, attrs: dict) -> None:
        """Set multiple attributes at once."""
        self.attributes.update(attrs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        pass


class DummyTracer:
    """A dummy tracer that returns DummySpan instances."""

    def start_as_current_span(self, name: str):
        """Start a new span and return it."""
        return DummySpan(name)


@pytest.fixture(autouse=True)
def reset_dummies(monkeypatch):
    """Reset the dummy spans and the global counter before each test."""
    dummy_spans.clear()
    # Reset the global counter in the generations module.
    monkeypatch.setattr("lilypad.generations._span_counter", 0)


@pytest.fixture(autouse=True)
def patch_get_tracer(monkeypatch):
    """Patch the get_tracer method to return a DummyTracer instance."""
    monkeypatch.setattr("lilypad.generations.get_tracer", lambda _: DummyTracer())


@generation()
def sync_outer(param: str) -> str:
    """A synchronous function that calls two other synchronous functions."""
    # For testing, simply return a fixed string.
    return "sync outer"


@generation()
async def async_outer(param: str) -> str:
    """An asynchronous function that calls two other asynchronous functions."""
    return "async outer"


def test_nested_order_sync(dummy_generation_instance: GenerationPublic):
    """Test that nested synchronous spans are assigned order values in the call order.
    Expected order: outer span should have order 1, inner spans should have subsequent orders.
    """

    # Define two nested synchronous functions.
    @generation()
    def inner1(param: str) -> str:
        return "inner1 result"

    @generation()
    def inner2(param: str) -> str:
        return "inner2 result"

    @generation()
    def outer(param: str) -> str:
        a = inner1("dummy")
        b = inner2("dummy")
        return f"outer {a} {b}"

    # Patch the client's method that retrieves the generation version.
    with patch(
        "lilypad.generations.LilypadClient.get_generation_version",
        return_value=dummy_generation_instance,
    ):
        result = outer("dummy")
        assert result == "outer inner1 result inner2 result"
        # We expect three spans to be created.
        orders = [span.attributes.get("lilypad.span.order") for span in dummy_spans]
        # With reset_dummies, expected orders should be [1, 2, 3].
        assert orders == [1, 2, 3]


@pytest.mark.asyncio
async def test_nested_order_async(dummy_generation_instance: GenerationPublic):
    """Test that nested asynchronous spans are assigned order values in the call order.
    Expected order: outer span, then inner1, then inner2.
    """

    @generation()
    async def async_inner1(param: str) -> str:
        return "async inner1"

    @generation()
    async def async_inner2(param: str) -> str:
        return "async inner2"

    @generation()
    async def async_outer(param: str) -> str:
        a = await async_inner1("dummy")
        b = await async_inner2("dummy")
        return f"async outer {a} {b}"

    with patch(
        "lilypad.generations.LilypadClient.get_generation_version",
        return_value=dummy_generation_instance,
    ):
        result = await async_outer("dummy")
        assert result == "async outer async inner1 async inner2"
        orders = [span.attributes.get("lilypad.span.order") for span in dummy_spans]
        # With reset_dummies, expected orders are [1, 2, 3].
        assert orders == [1, 2, 3]


def test_version_sync(dummy_generation_instance: GenerationPublic):
    """Test the version() method for synchronous functions.
    This forces a specific version and ensures that the correct generation is used.
    """
    forced_version = 2  # Use an integer version as forced version.
    with (
        patch(
            "lilypad.generations.LilypadClient.get_generation_by_version",
            return_value=dummy_generation_instance,
        ) as mock_get_ver,
        patch(
            "lilypad.generations.LilypadClient.get_generation_version",
            return_value=dummy_generation_instance,
        ),
    ):
        # Call the version method on the synchronous function.
        versioned_func = sync_outer.version(forced_version)
        result = versioned_func("dummy")
        # In our simple test, sync_outer returns "sync outer".
        assert result == "sync outer"
        mock_get_ver.assert_called_once()


@pytest.mark.asyncio
async def test_version_async(dummy_generation_instance: GenerationPublic):
    """Test the version() method for asynchronous functions.
    This forces a specific version and ensures that the correct generation is used.
    """
    forced_version = 2  # Use an integer version as forced version.
    with (
        patch(
            "lilypad.generations.LilypadClient.get_generation_by_version",
            return_value=dummy_generation_instance,
        ) as mock_get_ver,
        patch(
            "lilypad.generations.LilypadClient.get_generation_version",
            return_value=dummy_generation_instance,
        ),
    ):
        # Call the version method on the asynchronous function.
        versioned_func = async_outer.version(forced_version)
        result = await versioned_func("dummy")
        # In our simple test, async_outer returns "async outer".
        assert result == "async outer"
        mock_get_ver.assert_called_once()


def fake_mirascope_middleware_sync(
    generation, arg_types, arg_values, is_async, prompt_template
):
    """Simulate a synchronous mirascope middleware returning a dummy result."""

    def middleware(fn):
        def wrapped(*args, **kwargs):
            return "managed sync result"

        return wrapped

    return middleware


def fake_mirascope_middleware_async(
    generation, arg_types, arg_values, is_async, prompt_template
):
    """Simulate an asynchronous mirascope middleware returning a dummy result."""

    def middleware(fn):
        async def wrapped(*args, **kwargs):
            return "managed async result"

        return wrapped

    return middleware


def fake_llm_call(**kwargs):
    """Fake llm.call which ignores its arguments and returns a dummy callable."""

    def inner(mirascope_prompt):
        return lambda *args, **kwargs: "managed sync result"

    return inner


def fake_llm_call_async(**kwargs):
    """Fake llm.call which ignores its arguments and returns a dummy callable."""

    def inner(mirascope_prompt):
        return lambda *args, **kwargs: "managed async result"

    return inner


def test_sync_managed_generation(dummy_generation_instance: GenerationPublic):
    """Test that a synchronous function decorated with @generation(managed=True)
    follows the mirascope branch.
    """
    with (
        patch(
            "lilypad.generations.create_mirascope_middleware",
            side_effect=fake_mirascope_middleware_sync,
        ),
        patch(
            "lilypad.generations.LilypadClient.get_generation_version",
            return_value=dummy_generation_instance,
        ),
        patch("lilypad.generations.llm.call", side_effect=fake_llm_call),
    ):

        @generation(managed=True)
        def managed_sync(param: str) -> str:
            return "should not be used"

        result = managed_sync("dummy")
        assert result == "managed sync result"


@pytest.mark.asyncio
async def test_async_managed_generation(dummy_generation_instance: GenerationPublic):
    """Test that an asynchronous function decorated with @generation(managed=True)
    follows the mirascope branch.
    """
    with (
        patch(
            "lilypad.generations.create_mirascope_middleware",
            side_effect=fake_mirascope_middleware_async,
        ),
        patch(
            "lilypad.generations.LilypadClient.get_generation_version",
            return_value=dummy_generation_instance,
        ),
        patch("lilypad.generations.llm.call", side_effect=fake_llm_call),
    ):

        @generation(managed=True)
        async def managed_async(param: str) -> str:
            return "should not be used"

        result = await managed_async("dummy")
        assert result == "managed async result"


def test_sync_mirascope_attr(dummy_generation_instance: GenerationPublic):
    """Test that a synchronous function with __mirascope_call__ set follows the mirascope branch."""

    def base_sync(param: str) -> str:
        return "should not be used"

    base_sync.__mirascope_call__ = True
    with (
        patch(
            "lilypad.generations.create_mirascope_middleware",
            side_effect=fake_mirascope_middleware_sync,
        ),
        patch(
            "lilypad.generations.LilypadClient.get_generation_version",
            return_value=dummy_generation_instance,
        ),
        patch("lilypad.generations.llm.call", side_effect=fake_llm_call),
    ):
        decorated = generation()(base_sync)
        result = decorated("dummy")
        assert result == "managed sync result"


@pytest.mark.asyncio
async def test_async_mirascope_attr(dummy_generation_instance: GenerationPublic):
    """Test that an asynchronous function with __mirascope_call__ set follows the mirascope branch."""

    async def base_async(param: str) -> str:
        return "should not be used"

    base_async.__mirascope_call__ = True
    with (
        patch(
            "lilypad.generations.create_mirascope_middleware",
            side_effect=fake_mirascope_middleware_async,
        ),
        patch(
            "lilypad.generations.LilypadClient.get_generation_version",
            return_value=dummy_generation_instance,
        ),
        patch("lilypad.generations.llm.call", side_effect=fake_llm_call),
    ):
        decorated = generation()(base_async)
        result = await decorated("dummy")
        assert result == "managed async result"
