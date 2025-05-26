"""Tests for the tool decorator and related functionality."""

import pytest
from mirascope.core import BaseTool

from lilypad.lib.tools import tool


# Sample functions and tools for testing
def sample_basic_function(text: str) -> str:
    """Process the input text.

    Args:
        text: The text to process
    """
    return f"Processed: {text}"


def sample_function_with_multiple_args(title: str, author: str, year: int) -> str:
    """Format book information.

    Args:
        title: The title of the book
        author: The author of the book
        year: The publication year
    """
    return f"{title} by {author} ({year})"


async def sample_async_function(text: str) -> str:
    """Process the input text asynchronously.

    Args:
        text: The text to process
    """
    return f"Async processed: {text}"


# Tests
def test_basic_tool_decoration():
    """Test basic function decoration with @tool()"""
    decorated = tool()(sample_basic_function)

    # Check that the decoration created a BaseTool subclass
    assert issubclass(decorated, BaseTool)

    # Check that the docstring was preserved
    assert decorated.__doc__ == """Process the input text."""

    # Create an instance and test it
    instance = decorated(text="hello")  # pyright: ignore [reportCallIssue]
    assert instance.text == "hello"  # pyright: ignore [reportAttributeAccessIssue]
    assert instance.call() == "Processed: hello"


def test_tool_with_multiple_arguments():
    """Test tool decoration of a function with multiple arguments"""
    decorated = tool()(sample_function_with_multiple_args)

    # Check the generated tool fields
    assert "title" in decorated.model_fields
    assert "author" in decorated.model_fields
    assert "year" in decorated.model_fields

    # Verify field types
    assert decorated.model_fields["title"].annotation is str
    assert decorated.model_fields["author"].annotation is str
    assert decorated.model_fields["year"].annotation is int

    # Test instance creation and calling
    instance = decorated(title="The Book", author="John Doe", year=2024)  # pyright: ignore [reportCallIssue]
    assert instance.call() == "The Book by John Doe (2024)"


@pytest.mark.asyncio
async def test_async_function_decoration():
    """Test that async functions can be decorated"""
    decorated = tool()(sample_async_function)

    # Check basic class properties
    assert issubclass(decorated, BaseTool)
    assert "text" in decorated.model_fields

    # Create instance
    instance = decorated(text="test")  # pyright: ignore [reportCallIssue]
    assert instance.text == "test"  # pyright: ignore [reportAttributeAccessIssue]
    assert await instance.call() == "Async processed: test"


def test_tool_validation():
    """Test that decorated tools properly validate their inputs"""
    decorated = tool()(sample_function_with_multiple_args)

    # Test missing required argument
    with pytest.raises(ValueError, match="1 validation error"):
        decorated(title="Book", year=2024)  # pyright: ignore [reportCallIssue]

    # Test invalid type
    with pytest.raises(ValueError, match="1 validation error"):
        decorated(title="Book", author="John", year="invalid")  # pyright: ignore [reportCallIssue]


def test_tool_args_property():
    """Test that the decorated tool provides access to its arguments"""
    decorated = tool()(sample_function_with_multiple_args)
    instance = decorated(title="Book", author="John", year=2024)  # pyright: ignore [reportCallIssue]

    args = instance.args
    assert args == {"title": "Book", "author": "John", "year": 2024}


def test_tool_without_docstring():
    """Test decoration of a function without a docstring"""

    def no_doc_function(text: str) -> str:
        return f"Result: {text}"

    decorated = tool()(no_doc_function)
    assert "Must include required parameters" in decorated._description()


def test_tool_inheritance_preservation():
    """Test that tool decoration preserves base class methods"""

    class CustomBaseTool(BaseTool):
        def custom_method(self) -> str:
            return "custom"

    def test_func(text: str) -> str:
        """Test function"""
        return text

    # Create tool using CustomBaseTool as base
    decorated = CustomBaseTool.type_from_fn(test_func)
    instance = decorated(text="test")  # pyright: ignore [reportCallIssue, reportAbstractUsage]

    # Verify both the new functionality and inherited method work
    assert instance.call() == "test"
    assert instance.custom_method() == "custom"


def test_tool_with_default_values():
    """Test tool decoration with function having default values"""

    def func_with_defaults(text: str, repeat: int = 1) -> str:
        """Function with default value.

        Args:
            text: The text to repeat
            repeat: Number of times to repeat
        """
        return text * repeat

    decorated = tool()(func_with_defaults)

    # Test with only required argument
    instance1 = decorated(text="hello")  # pyright: ignore [reportCallIssue]
    assert instance1.call() == "hello"

    # Test with all arguments
    instance2 = decorated(text="hello", repeat=2)  # pyright: ignore [reportCallIssue]
    assert instance2.call() == "hellohello"


def test_tool_type_annotations():
    """Test that type annotations are correctly preserved"""

    def typed_function(text: str, count: int, flag: bool = False) -> str:
        """Function with various types"""
        return text

    decorated = tool()(typed_function)

    # Check field types
    assert decorated.model_fields["text"].annotation is str
    assert decorated.model_fields["count"].annotation is int
    assert decorated.model_fields["flag"].annotation is bool


def test_tool_multiple_decorations():
    """Test that multiple decorations don't cause issues"""
    decorated1 = tool()(sample_basic_function)
    decorated2 = tool()(sample_basic_function)

    # Verify both decorations work independently
    instance1 = decorated1(text="test1")  # pyright: ignore [reportCallIssue]
    instance2 = decorated2(text="test2")  # pyright: ignore [reportCallIssue]

    assert instance1.call() == "Processed: test1"
    assert instance2.call() == "Processed: test2"
