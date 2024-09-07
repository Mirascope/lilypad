"""Pulling a prompt from the server."""

from openai import OpenAI

import lilypad

client = OpenAI()


@lilypad.trace
def recommend_book(genre: str) -> str | None:
    """Recommends a `genre` book using OpenAI"""
    prompt = lilypad.prompt(recommend_book)(genre)
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=lilypad.openai.messages(prompt),
    )
    message = completion.choices[0].message
    return message.content


print(recommend_book("fantasy"))
