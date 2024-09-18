"""An interim dummy database to power the system lol."""

from typing import TypedDict

from mirascope.core import base


class Data(TypedDict):
    """Mock Data From DB."""

    prompt_template: str
    provider: str
    model: str
    json_mode: bool
    call_params: base.BaseCallParams


DUMMY_DATABASE: dict[str, Data] = {}


def set_dummy_database(database: dict[str, Data]) -> None:
    """Sets the dummy database."""
    global DUMMY_DATABASE
    DUMMY_DATABASE = database


def get_dummy_database() -> dict[str, Data]:
    """Gets the dummy database."""
    global DUMMY_DATABASE
    return DUMMY_DATABASE
