"""An interim dummy database to power the system lol."""

from typing import TypedDict


class _Info(TypedDict):
    prompt_template: str
    tools: list[str]


DUMMY_DATABASE: dict[str, _Info] = {}


def set_dummy_database(database: dict[str, _Info]) -> None:
    """Sets the dummy database."""
    global DUMMY_DATABASE
    DUMMY_DATABASE = database


def get_dummy_database() -> dict[str, _Info]:
    """Gets the dummy database."""
    global DUMMY_DATABASE
    return DUMMY_DATABASE
