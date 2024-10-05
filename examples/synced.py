import openai
from pydantic import BaseModel

import lilypad
from lilypad.configure import init

# client = openai.Client()
init()


@lilypad.synced.prompt()
def recommend_book(genre: str) -> str: ...


if __name__ == "__main__":
    print(recommend_book("sci-fi"))
