"""The initial meta judge prompt for generating annotaitons"""

from mirascope import llm
from mirascope.core import prompt_template
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


@llm.call(
    "openai",
    "gpt-4o",
    stream=True,
    json_mode=True,
    response_model=ResultsModel,
)
@prompt_template(
    """
    Please generate a JSON output that complies with the following JSON Schema. 
    The output should only include valid JSON data according to the schema and 
    should not contain any additional text or markdown formatting.

    Please provide an example output that fits this schema.

    - idealOutput: str
    - reasoning: str
    - exact: bool
    - label: Literal['pass','fail']

    Example:
        {{
            "results": {{
                "key": {{
                    "idealOutput": "value",
                    "reasoning": "value",
                    "exact": True,
                    "label": "pass"
                }}
            }}
        }}
    """
)
async def annotate_trace() -> None:
    """A placeholder prompt for annotating traces."""
