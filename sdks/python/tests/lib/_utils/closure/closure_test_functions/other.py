"""Other functions used in the main closure test functions."""

from enum import Enum
from typing import Annotated
from functools import wraps
from collections.abc import Callable

from pydantic import Field, BaseModel
from mirascope.core import FromCallArgs, openai

from lilypad.lib._utils import Closure


def imported_fn() -> str:
    return "Hello, world!"


def imported_sub_fn() -> str:
    return imported_fn()


class ImportedClass:
    def __call__(self) -> str:
        return "Hello, world!"


class FnInsideClass:
    def __call__(self) -> str:
        return imported_fn()


class SubFnInsideClass:
    def __call__(self) -> str:
        return imported_sub_fn()


class SelfFnClass:
    def fn(self) -> str:
        return "Hello, world!"

    def __call__(self) -> str:
        return self.fn()


def imported_decorator(fn: Callable) -> Callable[[], Closure]:
    @wraps(fn)
    def inner() -> Closure:
        return Closure.from_fn(fn)

    return inner


def mock_decorator_fn(model, response_model) -> Callable:
    def inner(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        return wrapper

    return inner


class TicketCategory(str, Enum):
    BUG_REPORT = "Bug Report"
    FEATURE_REQUEST = "Feature Request"


class TicketPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


class Ticket(BaseModel):
    issue: Annotated[str, FromCallArgs()]
    category: TicketCategory
    priority: TicketPriority
    summary: str = Field(
        ...,
        description="A highlight summary of the most important details of the ticket.",
    )


@mock_decorator_fn(
    "gpt-4o-mini",
    response_model=Ticket,
)
def triage_issue(issue: str) -> str:
    return "How can I help you today?"


def request_assistance(question: str) -> str:
    """Requests assistance from an expert.

    Ensure `question` is as clear and concise as possible.
    This will help the expert provide a more accurate response.
    """
    return input(f"[NEED ASSISTANCE] {question}, [ANSWER] ")


@openai.call(
    "gpt-4o-mini",
    tools=[request_assistance],
)
def customer_support_bot(issue: str, history: list[openai.OpenAIMessageParam]) -> openai.OpenAIDynamicConfig:
    ticket = triage_issue(issue)
    return {"computed_fields": {"ticket": ticket}}
