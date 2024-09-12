"""Basic usage example of recommending a `Book` response model."""

from mirascope.core import openai
from pydantic import BaseModel

import lilypad
import lilypad.dummy_database

mock_db = {
    "recommend_book": lilypad.dummy_database.Data(
        prompt_template="recommend a {genre} book",
        provider="openai",
        model="gpt-4o-mini",
        json_mode=False,
        call_params=openai.OpenAICallParams(),
    ),
}

lilypad.dummy_database.set_dummy_database(mock_db)


class Book(BaseModel):  # noqa: D100,D101
    title: str
    author: str


@lilypad.prompt()
def recommend_book(genre: str) -> Book: ...  # noqa: D103


book = recommend_book("fantasy")
print(book)
