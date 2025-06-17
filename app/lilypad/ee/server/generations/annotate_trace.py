"""The initial meta judge prompt for generating annotations"""

from collections.abc import AsyncGenerator

from pydantic import BaseModel, Field


class Result(BaseModel):
    """The result model for the judge prompt."""

    idealOutput: str
    reasoning: str
    exact: bool
    label: str


class ResultsModel(BaseModel):
    """The return model for the judge prompt."""

    results: dict[str, Result] = Field(
        description="The collection of keys and results.",
    )


MOCK_ANNOTATION_DATA = {
    "results": {
        "key": {
            "idealOutput": "The expected outcome was achieved successfully.",
            "reasoning": "The logic applied was consistent with the requirements specified, ensuring that the solution met all given criteria.",
            "exact": True,
            "label": "pass",
        }
    },
    "status": "completed",
}


# @llm.call(
#     "openai",
#     "gpt-4o",
#     stream=True,
#     json_mode=True,
#     response_model=ResultsModel,
# )
# @prompt_template(
#     """
#     Please generate a JSON output that complies with the following JSON Schema.
#     The output should only include valid JSON data according to the schema and
#     should not contain any additional text or markdown formatting.
#
#     Please provide an example output that fits this schema.
#
#     - idealOutput: str
#     - reasoning: str
#     - exact: bool
#     - label: Literal['pass','fail']
#
#     Example:
#         {{
#             "results": {{
#                 "key": {{
#                     "idealOutput": "value",
#                     "reasoning": "value",
#                     "exact": True,
#                     "label": "pass"
#                 }}
#             }}
#         }}
#     """
# )
async def annotate_trace() -> AsyncGenerator[ResultsModel, None]:
    """A placeholder prompt for annotating traces.

    NOTE: Returns static mock data as actual generation is not implemented.
    Yields the mock data once in Server-Sent Event 'data' format.
    """
    # Yield the static mock data formatted as a Server-Sent Event
    yield ResultsModel.model_validate(MOCK_ANNOTATION_DATA)  # pragma: no cover
