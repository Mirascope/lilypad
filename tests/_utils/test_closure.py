"""Tests for the `_utils.closure` module."""

import inspect

from mirascope.core import openai, prompt_template
from pydantic import BaseModel

from lilypad._utils.closure import compute_closure


def _fn():
    return "test"


def test_simple_function_no_deps():
    """Tests a simple function with no dependencies."""
    expected = inspect.cleandoc("""
    def _fn():
        return "test"
    """)
    assert compute_closure(_fn)[0] == expected + "\n"


def _helper2():
    return _helper3()


def _helper3():
    return "helper3"


def _helper1():
    return _helper2()


def test_function_ordering():
    """Tests that function dependencies are ordered correctly in the closure."""
    expected = inspect.cleandoc("""
    def _helper3():
        return "helper3"


    def _helper2():
        return _helper3()


    def _helper1():
        return _helper2()
    """)
    assert compute_closure(_helper1)[0] == expected + "\n"


@openai.call("gpt-4o-mini")
def _recommend_book(genre: str) -> str:
    return f"Recommend a {genre} book"


def test_decorated_function():
    """Tests that a decorated function's closure is computed correctly."""
    expected = inspect.cleandoc("""
    @openai.call("gpt-4o-mini")
    def _recommend_book(genre: str) -> str:
        return f"Recommend a {genre} book"
    """)
    assert compute_closure(_recommend_book)[0] == expected + "\n"


@openai.call("gpt-4o-mini")
@prompt_template("Recommend a {genre} author")
def _recommend_author(genre: str): ...


def test_multiple_decorators():
    """Tests that multiple decorators are handled correctly."""
    expected = inspect.cleandoc("""
    @openai.call("gpt-4o-mini")
    @prompt_template("Recommend a {genre} author")
    def _recommend_author(genre: str): ...
    """)
    assert compute_closure(_recommend_author)[0] == expected + "\n"


def _outer():
    def inner():
        return "inner"

    return inner()


def test_nested_functions():
    """Tests that nested functions are handled correctly."""
    expected = inspect.cleandoc("""
    def _outer():
        def inner():
            return "inner"

        return inner()
    """)
    assert compute_closure(_outer)[0] == expected + "\n"


def _no_source():
    pass


def test_no_source():
    """Tests that functions with no source code are handled correctly."""
    expected = inspect.cleandoc("""
    def _no_source():
        pass
    """)
    assert compute_closure(_no_source)[0] == expected + "\n"


class _Book(BaseModel):
    title: str
    author: str


def _return_book() -> _Book: ...


def test_class_return_type():
    """Tests that a class is included in the closure of a function."""
    expected = inspect.cleandoc("""
    class _Book(BaseModel):
        title: str
        author: str

    
    def _return_book() -> _Book: ...
    """)
    assert compute_closure(_return_book)[0] == expected + "\n"


@openai.call("gpt-4o-mini", response_model=_Book)
def _recommend_book_class(genre: str) -> str:
    return f"Recommend a {genre} book"


def test_class_argument_in_decorator():
    """Tests that a class argument in a decorator is included in the closure."""
    expected = inspect.cleandoc("""
    class _Book(BaseModel):
        title: str
        author: str
    
    
    @openai.call("gpt-4o-mini", response_model=_Book)
    def _recommend_book_class(genre: str) -> str:
        return f"Recommend a {genre} book"
    """)
    assert compute_closure(_recommend_book_class)[0] == expected + "\n"


class _InnerClass(BaseModel):
    inner: str


class _OuterClass(BaseModel):
    outer: str
    inner: _InnerClass


def _fn_with_class():
    inner = _InnerClass(inner="inner")
    _ = _OuterClass(outer="outer", inner=inner)


def test_class_in_function():
    """Tests that a class defined in a function is included in the closure."""
    expected = inspect.cleandoc("""
    class _OuterClass(BaseModel):
        outer: str
        inner: _InnerClass

    
    class _InnerClass(BaseModel):
        inner: str
    
    
    def _fn_with_class():
        inner = _InnerClass(inner="inner")
        _ = _OuterClass(outer="outer", inner=inner)
    """)
    assert compute_closure(_fn_with_class)[0] == expected + "\n"


# DOES NOT WORK YET. SAD :(
# template = "Recommend a {genre} book series"


# @openai.call("gpt-4o-mini")
# @prompt_template(template)
# def recommend_book_series(genre: str): ...


# def test_local_variable_inclusion():
#     """Tests that local variables are included in the closure."""
#     expected = inspect.cleandoc("""
#     @openai.call("gpt-4o-mini")
#     @prompt_template("Recommend a {genre} book series")
#     def recommend_book_series(genre: str): ...
#     """)
#     assert compute_closure(recommend_book_series) == expected + "\n"


def _get_available_series() -> list[str]:
    return ["The Kingkiller Chronicle"]


@openai.call("gpt-4o-mini")
@prompt_template("Recommend a {genre} book series from this list: {series}")
def _recommend_book_series_from_available(genre: str) -> openai.OpenAIDynamicConfig:
    return {"computed_fields": {"series": _get_available_series()}}


def test_multiple_decorators_with_dependencies():
    """Tests that multiple decorators with dependencies are handled correctly."""
    expected = inspect.cleandoc("""
    def _get_available_series() -> list[str]:
        return ["The Kingkiller Chronicle"]


    @openai.call("gpt-4o-mini")
    @prompt_template("Recommend a {genre} book series from this list: {series}")
    def _recommend_book_series_from_available(genre: str) -> openai.OpenAIDynamicConfig:
        return {"computed_fields": {"series": _get_available_series()}}
    """)
    assert compute_closure(_recommend_book_series_from_available)[0] == expected + "\n"
