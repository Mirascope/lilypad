import openai
from pydantic import BaseModel

import lilypad
from lilypad.configure import init

init()


class Book(BaseModel):  # noqa: D100,D101
    title: str
    author: str


client = openai.Client()


@lilypad.prompt()
def recommend_book(genre: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"recommend a {genre} book"}],
    )
    return str(response.choices[0].message.content)


if __name__ == "__main__":
    recommend_book("sci-fi")
