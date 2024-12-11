"""The main methods for testing the `Closure class."""

import importlib.metadata
import os
from collections.abc import Callable
from functools import wraps
from typing import Any, Literal, TypeAlias

import openai as oai
from google.generativeai.generative_models import GenerativeModel
from mirascope.core import BaseMessageParam, openai, prompt_template
from openai import OpenAI as OAI
from openai.types.chat import ChatCompletionUserMessageParam

import tests._utils.closure.closure_test_functions.other
import tests._utils.closure.closure_test_functions.other as cloth
from lilypad._utils import Closure

from . import other
from . import other as oth
from .other import (
    FnInsideClass,
    ImportedClass,
    SelfFnClass,
    SubFnInsideClass,
    imported_fn,
)
from .other import ImportedClass as IC
from .other import imported_fn as ifn


def single_fn() -> str:
    """
    def single_fn() -> str:
        return "Hello, world!"
    """
    return "Hello, world!"


def sub_fn() -> str:
    """
    def single_fn() -> str:
        return "Hello, world!"


    def sub_fn() -> str:
        return single_fn()
    """
    return single_fn()


def inner_fn() -> str:
    """
    def inner_fn() -> str:
        def inner() -> str:
            return "Hello, world!"

        return inner()
    """

    def inner() -> str:
        return "Hello, world!"

    return inner()


def inner_class_fn() -> str:
    """
    def inner_class_fn() -> str:
        class Inner:
            def __call__(self) -> str:
                return "Hello, world!"

        return Inner()()
    """

    class Inner:
        def __call__(self) -> str:
            return "Hello, world!"

    return Inner()()


def inner_sub_fn() -> str:
    """
    def single_fn() -> str:
        return "Hello, world!"


    def sub_fn() -> str:
        return single_fn()


    def inner_sub_fn() -> str:
        def inner() -> str:
            return sub_fn()

        return inner()
    """

    def inner() -> str:
        return sub_fn()

    return inner()


def built_in_fn() -> Literal["Hello, world!"]:
    """
    from typing import Literal


    def built_in_fn() -> Literal["Hello, world!"]:
        return "Hello, world!"
    """
    return "Hello, world!"


def third_party_fn() -> BaseMessageParam:
    """
    from mirascope.core import BaseMessageParam


    def third_party_fn() -> BaseMessageParam:
        return BaseMessageParam(role="user", content="Hello, world!")
    """
    return BaseMessageParam(role="user", content="Hello, world!")


@openai.call("gpt-4o-mini")
def decorated_fn() -> str:
    """
    from mirascope.core import openai


    @openai.call("gpt-4o-mini")
    def decorated_fn() -> str:
        return "Hello, world!"
    """
    return "Hello, world!"


@openai.call("gpt-4o-mini")
@prompt_template("Hello, world!")
def multi_decorated_fn():
    """
    from mirascope.core import openai, prompt_template


    @openai.call("gpt-4o-mini")
    @prompt_template("Hello, world!")
    def multi_decorated_fn(): ...
    """


def user_defined_import_fn() -> str:
    """
    def imported_fn() -> str:
        return "Hello, world!"


    def user_defined_import_fn() -> str:
        return imported_fn()
    """
    return other.imported_fn()


def user_defined_from_import_fn() -> str:
    """
    def imported_fn() -> str:
        return "Hello, world!"


    def user_defined_from_import_fn() -> str:
        return imported_fn()
    """
    return imported_fn()


def user_defined_class_import_fn() -> str:
    """
    class ImportedClass:
        def __call__(self) -> str:
            return "Hello, world!"


    def user_defined_class_import_fn() -> str:
        return ImportedClass()()
    """
    return other.ImportedClass()()


def user_defined_class_from_import_fn() -> str:
    """
    class ImportedClass:
        def __call__(self) -> str:
            return "Hello, world!"


    def user_defined_class_from_import_fn() -> str:
        return ImportedClass()()
    """
    return ImportedClass()()


def fn_inside_class_fn() -> str:
    """
    def imported_fn() -> str:
        return "Hello, world!"


    class FnInsideClass:
        def __call__(self) -> str:
            return imported_fn()


    def fn_inside_class_fn() -> str:
        return FnInsideClass()()
    """
    return FnInsideClass()()


def sub_fn_inside_class_fn() -> str:
    """
    def imported_fn() -> str:
        return "Hello, world!"


    def imported_sub_fn() -> str:
        return imported_fn()


    class SubFnInsideClass:
        def __call__(self) -> str:
            return imported_sub_fn()


    def sub_fn_inside_class_fn() -> str:
        return SubFnInsideClass()()
    """
    return SubFnInsideClass()()


def self_fn_class_fn() -> str:
    """
    class SelfFnClass:
        def fn(self) -> str:
            return "Hello, world!"

        def __call__(self) -> str:
            return self.fn()


    def self_fn_class_fn() -> str:
        return SelfFnClass()()
    """
    return SelfFnClass()()


def standard_import_fn() -> str:
    """
    import os


    def standard_import_fn() -> str:
        return os.getenv("HELLO_WORLD", "Hello, world!")
    """
    return os.getenv("HELLO_WORLD", "Hello, world!")


def dotted_import_fn() -> str:
    """
    import importlib.metadata


    def dotted_import_fn() -> str:
        return importlib.metadata.version("python-lilypad")
    """
    return importlib.metadata.version("python-lilypad")


def aliased_module_import_fn(query: str) -> str:
    """
    import openai as oai


    def aliased_module_import_fn(query: str) -> str:
        client = oai.OpenAI()
        completion = client.chat.completions.create(
            model="gpt-4o-mini", messages=[{"role": "user", "content": query}]
        )
        return str(completion.choices[0].message.content)
    """
    client = oai.OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4o-mini", messages=[{"role": "user", "content": query}]
    )
    return str(completion.choices[0].message.content)


def aliased_import_fn(query: str) -> str:
    """
    from openai import OpenAI as OAI


    def aliased_import_fn(query: str) -> str:
        client = OAI()
        completion = client.chat.completions.create(
            model="gpt-4o-mini", messages=[{"role": "user", "content": query}]
        )
        return str(completion.choices[0].message.content)
    """
    client = OAI()
    completion = client.chat.completions.create(
        model="gpt-4o-mini", messages=[{"role": "user", "content": query}]
    )
    return str(completion.choices[0].message.content)


def user_defined_aliased_module_import_fn() -> str:
    """
    def imported_fn() -> str:
        return "Hello, world!"


    def user_defined_aliased_module_import_fn() -> str:
        return imported_fn()
    """
    return oth.imported_fn()


def user_defined_aliased_module_import_class_fn() -> str:
    """
    class ImportedClass:
        def __call__(self) -> str:
            return "Hello, world!"


    def user_defined_aliased_module_import_class_fn() -> str:
        return ImportedClass()()
    """
    return oth.ImportedClass()()


def user_defined_aliased_import_fn() -> str:
    """
    def imported_fn() -> str:
        return "Hello, world!"


    def user_defined_aliased_import_fn() -> str:
        return imported_fn()
    """
    return ifn()


def user_defined_aliased_class_import_fn() -> str:
    """
    class ImportedClass:
        def __call__(self) -> str:
            return "Hello, world!"


    def user_defined_aliased_class_import_fn() -> str:
        return ImportedClass()()
    """
    return IC()()


def user_defined_dotted_import_fn() -> str:
    """
    def imported_fn() -> str:
        return "Hello, world!"


    def user_defined_dotted_import_fn() -> str:
        return imported_fn()
    """
    return tests._utils.closure.closure_test_functions.other.imported_fn()


def user_defined_aliased_dotted_import_fn() -> str:
    """
    def imported_fn() -> str:
        return "Hello, world!"


    def user_defined_aliased_dotted_import_fn() -> str:
        return imported_fn()
    """
    return cloth.imported_fn()


def annotated_input_arg_fn(var: Any) -> str:
    """
    from typing import Any


    def annotated_input_arg_fn(var: Any) -> str:
        return str(var)
    """
    return str(var)


def annotated_assignment_fn() -> str:
    """
    from openai.types.chat import ChatCompletionUserMessageParam


    def annotated_assignment_fn() -> str:
        message: ChatCompletionUserMessageParam = {
            "role": "user",
            "content": "Hello, world!",
        }
        return str(message)
    """
    message: ChatCompletionUserMessageParam = {
        "role": "user",
        "content": "Hello, world!",
    }
    return str(message)


def internal_imports_fn() -> str:
    """
    def imported_fn() -> str:
        return "Hello, world!"


    def internal_imports_fn() -> str:
        from openai import OpenAI

        client = OpenAI()
        completion = client.chat.completions.create(
            model="gpt-4o-mini", messages=[{"role": "user", "content": imported_fn()}]
        )
        return str(completion.choices[0].message.content)
    """
    from openai import OpenAI

    from .other import imported_fn

    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4o-mini", messages=[{"role": "user", "content": imported_fn()}]
    )
    return str(completion.choices[0].message.content)


MyType: TypeAlias = Literal["Hello, world!"]


def type_alias_fn() -> MyType:
    """
    from typing import Literal, TypeAlias

    MyType: TypeAlias = Literal["Hello, world!"]


    def type_alias_fn() -> MyType:
        var: MyType = "Hello, world!"
        return var
    """
    var: MyType = "Hello, world!"
    return var


client = oai.OpenAI()


@openai.call("gpt-4o-mini", client=client)
def global_var_fn() -> str:
    """
    import openai as oai
    from mirascope.core import openai

    client = oai.OpenAI()


    @openai.call("gpt-4o-mini", client=client)
    def global_var_fn() -> str:
        return "Hello, world!"
    """
    return "Hello, world!"


def _decorator(fn: Callable) -> Callable[[], Closure]:
    @wraps(fn)
    def inner() -> Closure:
        return Closure.from_fn(fn)

    return inner


def import_with_different_dist_name_fn() -> type[GenerativeModel]:
    """
    from google.generativeai.generative_models import GenerativeModel


    def import_with_different_dist_name_fn() -> type[GenerativeModel]:
        return GenerativeModel
    """
    return GenerativeModel


@_decorator
def closure_inside_decorator_fn() -> str:
    """
    from collections.abc import Callable
    from functools import wraps

    from lilypad._utils import Closure


    def _decorator(fn: Callable) -> Callable[[], Closure]:
        @wraps(fn)
        def inner() -> Closure:
            return Closure.from_fn(fn)

        return inner


    @_decorator
    def closure_inside_decorator_fn() -> str:
        return "Hello, world!"
    """
    return "Hello, world!"


@other.imported_decorator
def closure_inside_imported_decorator_fn() -> str:
    """
    from collections.abc import Callable
    from functools import wraps

    from lilypad._utils import Closure


    def imported_decorator(fn: Callable) -> Callable[[], Closure]:
        @wraps(fn)
        def inner() -> Closure:
            return Closure.from_fn(fn)

        return inner


    @imported_decorator
    def closure_inside_imported_decorator_fn() -> str:
        return "Hello, world!"
    """
    return "Hello, world!"


def closure_with_long_function_name_that_wraps_around_fn(
    arg1: str,
    arg2: str,
) -> ChatCompletionUserMessageParam:
    """
    from openai.types.chat import ChatCompletionUserMessageParam


    def closure_with_long_function_name_that_wraps_around_fn(
        arg1: str, arg2: str
    ) -> ChatCompletionUserMessageParam:
        return {"role": "user", "content": "Hello, world!"}
    """
    return {"role": "user", "content": "Hello, world!"}