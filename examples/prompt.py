"""Basic, rough example showing current prompt functionality."""

from openai import OpenAI

import lilypad
import lilypad.dummy_database

DUMMY_DATABASE: dict[str, lilypad.dummy_database._Info] = {
    "05b1d201926c00bd1033a119f3c536466719b33196c416b8dd6b312417bae3f6": {
        "prompt_template": "Recommend a {genre} book",
        "tools": [
            'class FormatBook(BaseTool):\n    title: str\n    author: str\n\n    def call(self) -> str:\n        return f"{self.title} by {self.author}"\n'
        ],
    }
}

lilypad.dummy_database.set_dummy_database(DUMMY_DATABASE)


client = OpenAI()


# @lillypad.track()
# def recommend_book(genre: str, topic: str) -> str | None:
#     """Recommends a `genre` book using OpenAI"""
#     completion = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=lillypad.openai.messages(recommend_book)(genre),
#     )
#     message = completion.choices[0].message
#     return message.content


# @lillypad.evaluate(recommend_book)
# def test_recommend_book(genre: str, expected_output: str):
#     completion = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=lillypad.openai.messages(recommend_book)(genre),
#     )
#     assert completion.choices[0].message.content == expected_output


# @lillypad.track()
# def recommend_book(genre: str, topic: str) -> str | None:
#     """Recommends a `genre` book using OpenAI"""
#     # prompt = lillypad.prompt(recommend_book)(genre, topic)
#     # tools = lillypad.tools(recommend_book)
#     completion = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=lillypad.openai.messages(recommend_book)(genre),
#         # tools=lillypad.openai.tools(tools),
#     )
#     message = completion.choices[0].message
#     # if message.tool_calls:
#     #     print(message.tool_calls)
#     #     return None
#     return message.content


# response = recommend_book("fantasy", "")
# print(response)


# from mirascope.core import BaseTool, openai

# tool_str = """\
# class FormatBook(BaseTool):
#     title: str
#     author: str

#     def call(self) -> str:
#         return f"{self.title} by {self.author}"
# """

# namespace = {"BaseTool": BaseTool}
# exec(tool_str, namespace)
# print(namespace)

# tool_type = openai.OpenAITool.type_from_base_model_type(FormatBook)
