import lilypad
from pydantic import BaseModel


class Book(BaseModel):
    title: str
    author: str


@lilypad.llm_fn(synced=True)
def recommend_book(genre: str) -> Book: ...
