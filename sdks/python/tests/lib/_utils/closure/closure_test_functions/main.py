"""The main methods for testing the `Closure class."""

import os
import time
import random
import inspect
import importlib.metadata
from typing import Any, Literal, TypeAlias
from datetime import datetime
from functools import wraps, cached_property
from collections.abc import Callable

import openai as oai
from openai import OpenAI as OAI
from pydantic import BaseModel
from mirascope.core import BaseMessageParam, openai, prompt_template
from openai.types.chat import ChatCompletionUserMessageParam
from google.generativeai.generative_models import GenerativeModel

import tests.lib._utils.closure.closure_test_functions.other
import tests.lib._utils.closure.closure_test_functions.other as cloth
from lilypad.lib._utils import Closure

from . import other, other as oth
from .other import (
    Ticket,
    SelfFnClass,
    FnInsideClass,
    ImportedClass,
    ImportedClass as IC,
    SubFnInsideClass,
    imported_fn,
    imported_fn as ifn,
    customer_support_bot,
)


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
    completion = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": query}])
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
    completion = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": query}])
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

    from lilypad.lib._utils import Closure


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

    from lilypad.lib._utils import Closure


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


class MockClient:
    """Mock client class."""

    @cached_property
    def foo(self) -> str:
        """Foo"""
        return "Hello, "

    @property
    def bar(self) -> str:
        """Bar"""
        return "world!"


def closure_with_properties_fn() -> str:
    """
    from functools import cached_property


    class MockClient:
        @cached_property
        def foo(self) -> str:
            return "Hello, "

        @property
        def bar(self) -> str:
            return "world!"


    def closure_with_properties_fn() -> str:
        model = MockClient()
        assert isinstance(model, MockClient)
        return model.foo + model.bar
    """
    model = MockClient()
    assert isinstance(model, MockClient)
    return model.foo + model.bar


def closure_with_long_function_name_that_wraps_around_fn(
    arg1: str,
    arg2: str,
) -> ChatCompletionUserMessageParam:
    """
    from openai.types.chat import ChatCompletionUserMessageParam


    def closure_with_long_function_name_that_wraps_around_fn(
        arg1: str,
        arg2: str,
    ) -> ChatCompletionUserMessageParam:
        return {"role": "user", "content": "Hello, world!"}
    """
    return {"role": "user", "content": "Hello, world!"}


def datetime_fn() -> str:
    """
    from datetime import datetime


    def datetime_fn() -> str:
        return datetime.now().strftime("%B %d, %Y")

    """
    return datetime.now().strftime("%B %d, %Y")


class Response(BaseModel):
    """Test response model."""

    response: str


@openai.call("gpt-4o-mini", response_model=Response)
def mirascope_response_model_fn() -> str:
    """
    from mirascope.core import openai
    from pydantic import BaseModel


    class Response(BaseModel):
        response: str


    @openai.call("gpt-4o-mini", response_model=Response)
    def mirascope_response_model_fn() -> str:
        return "Hello, world!"
    """
    return "Hello, world!"


def multiple_literal_fn() -> str:
    """
    def multiple_literal_fn() -> str:
        return \"\"\"Hello
                World\"\"\"
    """
    return """Hello
            World"""


def raw_string_fn() -> str:
    """
    def raw_string_fn() -> str:
        return r\"\"\"Hello
                World\"\"\"
    """
    return r"""Hello
            World"""


def multi_joined_string_fn() -> str:
    r"""
    def multi_joined_string_fn() -> str:
        return (
            "Hello, -----------------------------------------------------------------"
            "world!"
        )
    """
    return "Hello, -----------------------------------------------------------------world!"


def empty_body_fn_docstrings():
    """
    def empty_body_fn_docstrings(): ...
    """  # noqa: D200


@openai.call(
    "gpt-4o-mini",
    response_model=Ticket,
)
def nested_base_model_definitions(issue: str) -> str:
    """
    from enum import Enum
    from typing import Annotated

    from mirascope.core import FromCallArgs, openai
    from pydantic import BaseModel, Field


    class TicketPriority(str, Enum):
        LOW = "Low"
        MEDIUM = "Medium"
        HIGH = "High"
        URGENT = "Urgent"


    class TicketCategory(str, Enum):
        BUG_REPORT = "Bug Report"
        FEATURE_REQUEST = "Feature Request"


    class Ticket(BaseModel):
        issue: Annotated[str, FromCallArgs()]
        category: TicketCategory
        priority: TicketPriority
        summary: str = Field(
            ...,
            description="A highlight summary of the most important details of the ticket.",
        )


    @openai.call(
        "gpt-4o-mini",
        response_model=Ticket,
    )
    def nested_base_model_definitions(issue: str) -> str:
        return "How can I help you today?"
    """
    return "How can I help you today?"


issue = inspect.cleandoc("")


def handle_issue(issue: str) -> str:
    """
    from collections.abc import Callable
    from enum import Enum
    from functools import wraps
    from typing import Annotated

    from mirascope.core import FromCallArgs, openai
    from pydantic import BaseModel, Field


    def request_assistance(question: str) -> str:
        return input(f"[NEED ASSISTANCE] {question}, [ANSWER] ")


    class TicketPriority(str, Enum):
        LOW = "Low"
        MEDIUM = "Medium"
        HIGH = "High"
        URGENT = "Urgent"


    class TicketCategory(str, Enum):
        BUG_REPORT = "Bug Report"
        FEATURE_REQUEST = "Feature Request"


    class Ticket(BaseModel):
        issue: Annotated[str, FromCallArgs()]
        category: TicketCategory
        priority: TicketPriority
        summary: str = Field(
            ...,
            description="A highlight summary of the most important details of the ticket.",
        )


    def mock_decorator_fn(model, response_model) -> Callable:
        def inner(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                return fn(*args, **kwargs)

            return wrapper

        return inner


    @mock_decorator_fn(
        "gpt-4o-mini",
        response_model=Ticket,
    )
    def triage_issue(issue: str) -> str:
        return "How can I help you today?"


    @openai.call(
        "gpt-4o-mini",
        tools=[request_assistance],
    )
    def customer_support_bot(
        issue: str, history: list[openai.OpenAIMessageParam]
    ) -> openai.OpenAIDynamicConfig:
        ticket = triage_issue(issue)
        return {"computed_fields": {"ticket": ticket}}


    def handle_issue(issue: str) -> str:
        history = []
        response = customer_support_bot(issue, history)
        history += [response.user_message_param, response.message_param]
        while tools := response.tools:
            history += response.tool_message_params([(tool, tool.call()) for tool in tools])
            response = customer_support_bot("", history)
            history.append(response.message_param)
        return response.content
    """
    history = []
    response = customer_support_bot(issue, history)
    history += [response.user_message_param, response.message_param]
    while tools := response.tools:
        history += response.tool_message_params([(tool, tool.call()) for tool in tools])
        response = customer_support_bot("", history)
        history.append(response.message_param)
    return response.content


class Chatbot:
    """A chatbot class."""

    def __init__(self, name: str) -> None:
        self.name = name

    @openai.call("gpt-4o-mini")
    def instance_method(self) -> str:
        """
        from mirascope.core import openai


        class Chatbot:
            def __init__(self, name: str) -> None:
                self.name = name

            @openai.call("gpt-4o-mini")
            def instance_method(self) -> str:
                return f"Hello, {self.name}!"
        """
        return f"Hello, {self.name}!"


def fn_using_time_module():
    """
    import time


    def fn_using_time_module():
        return time.time()
    """
    return time.time()


def fn_using_random_module():
    """
    import random


    def fn_using_random_module():
        return random.random()
    """
    return random.random()
