import openai
from pydantic import BaseModel

import lilypad
from lilypad import configure

# client = openai.Client()
configure()


@lilypad.synced.llm_fn()
def recommend_book(genre: str) -> str: ...


if __name__ == "__main__":
    print(recommend_book("sci-fi"))
