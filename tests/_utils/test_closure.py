"""Tests for the `_utils.closure` module."""

import inspect

from mirascope.core import openai, prompt_template
from pydantic import BaseModel

from lilypad._utils.closure import compute_closure


def fn():
    return "test"


def test_simple_function_no_deps():
    """Tests a simple function with no dependencies."""
    expected = inspect.cleandoc("""
    def fn():
        return "test"
    """)
    assert compute_closure(fn)[0] == expected + "\n"


def helper2():
    return helper3()


def helper3():
    return "helper3"


def helper1():
    return helper2()


def test_function_ordering():
    """Tests that function dependencies are ordered correctly in the closure."""
    expected = inspect.cleandoc("""
    def helper3():
        return "helper3"


    def helper2():
        return helper3()


    def helper1():
        return helper2()
    """)
    assert compute_closure(helper1)[0] == expected + "\n"


@openai.call("gpt-4o-mini")
def recommend_book(genre: str) -> str:
    return f"Recommend a {genre} book"


def test_decorated_function():
    """Tests that a decorated function's closure is computed correctly."""
    expected = inspect.cleandoc("""
    @openai.call("gpt-4o-mini")
    def recommend_book(genre: str) -> str:
        return f"Recommend a {genre} book"
    """)
    assert compute_closure(recommend_book)[0] == expected + "\n"


@openai.call("gpt-4o-mini")
@prompt_template("Recommend a {genre} author")
def recommend_author(genre: str): ...


def test_multiple_decorators():
    """Tests that multiple decorators are handled correctly."""
    expected = inspect.cleandoc("""
    @openai.call("gpt-4o-mini")
    @prompt_template("Recommend a {genre} author")
    def recommend_author(genre: str): ...
    """)
    assert compute_closure(recommend_author)[0] == expected + "\n"


def outer():
    def inner():
        return "inner"

    return inner()


def test_nested_functions():
    """Tests that nested functions are handled correctly."""
    expected = inspect.cleandoc("""
    def outer():
        def inner():
            return "inner"

        return inner()
    """)
    assert compute_closure(outer)[0] == expected + "\n"


def no_source():
    pass


def test_no_source():
    """Tests that functions with no source code are handled correctly."""
    expected = inspect.cleandoc("""
    def no_source():
        pass
    """)
    assert compute_closure(no_source)[0] == expected + "\n"


class Book(BaseModel):
    title: str
    author: str


def return_book() -> Book: ...


def test_class_return_type():
    """Tests that a class is included in the closure of a function."""
    expected = inspect.cleandoc("""
    class Book(BaseModel):
        title: str
        author: str

    
    def return_book() -> Book: ...
    """)
    assert compute_closure(return_book)[0] == expected + "\n"


@openai.call("gpt-4o-mini", response_model=Book)
def recommend_book_class(genre: str) -> str:
    return f"Recommend a {genre} book"


def test_class_argument_in_decorator():
    """Tests that a class argument in a decorator is included in the closure."""
    expected = inspect.cleandoc("""
    class Book(BaseModel):
        title: str
        author: str
    
    
    @openai.call("gpt-4o-mini", response_model=Book)
    def recommend_book_class(genre: str) -> str:
        return f"Recommend a {genre} book"
    """)
    assert compute_closure(recommend_book_class)[0] == expected + "\n"


class InnerClass(BaseModel):
    inner: str


class OuterClass(BaseModel):
    outer: str
    inner: InnerClass


def fn_with_class():
    inner = InnerClass(inner="inner")
    outer = OuterClass(outer="outer", inner=inner)


def test_class_in_function():
    """Tests that a class defined in a function is included in the closure."""
    expected = inspect.cleandoc("""
    class OuterClass(BaseModel):
        outer: str
        inner: InnerClass

    
    class InnerClass(BaseModel):
        inner: str
    
    
    def fn_with_class():
        inner = InnerClass(inner="inner")
        outer = OuterClass(outer="outer", inner=inner)
    """)
    assert compute_closure(fn_with_class)[0] == expected + "\n"


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


def get_available_series() -> list[str]:
    return ["The Kingkiller Chronicle"]


@openai.call("gpt-4o-mini")
@prompt_template("Recommend a {genre} book series from this list: {series}")
def recommend_book_series_from_available(genre: str) -> openai.OpenAIDynamicConfig:
    return {"computed_fields": {"series": get_available_series()}}


def test_multiple_decorators_with_dependencies():
    """Tests that multiple decorators with dependencies are handled correctly."""
    expected = inspect.cleandoc("""
    def get_available_series() -> list[str]:
        return ["The Kingkiller Chronicle"]


    @openai.call("gpt-4o-mini")
    @prompt_template("Recommend a {genre} book series from this list: {series}")
    def recommend_book_series_from_available(genre: str) -> openai.OpenAIDynamicConfig:
        return {"computed_fields": {"series": get_available_series()}}
    """)
    assert compute_closure(recommend_book_series_from_available)[0] == expected + "\n"
