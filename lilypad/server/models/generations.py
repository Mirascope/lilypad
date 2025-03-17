"""Generations models."""

import ast
import keyword
import re
from datetime import datetime
from typing import TYPE_CHECKING, Any, Self
from uuid import UUID

from mirascope.core.base import CommonCallParams
from pydantic import BaseModel, field_validator, model_validator
from sqlalchemy import Column
from sqlmodel import Field, Relationship, SQLModel

from ..._utils import DependencyInfo
from .base_organization_sql_model import BaseOrganizationSQLModel
from .base_sql_model import JSONTypeDecorator, get_json_column
from .table_names import (
    GENERATION_TABLE_NAME,
    PROJECT_TABLE_NAME,
)

if TYPE_CHECKING:
    from ...ee.server.models.annotations import AnnotationTable
    from ...ee.server.models.deployments import DeploymentTable
    from .projects import ProjectTable
    from .spans import SpanTable

MAX_ARG_NAME_LENGTH = 100
MAX_TYPE_NAME_LENGTH = 100

# Avoid overwriting built-in special names like __import__.
ALLOWED_NAME_REGEX = re.compile(r"^(?!__)[A-Za-z_][A-Za-z0-9_]*$")


def extract_function_info(source: str) -> tuple[str, dict[str, str]]:
    """Parse the given source code and extract the function name and its arguments with type hints.

    Returns:
        A tuple (function_name, args_info) where:
            - function_name is the name of the function.
            - args_info is a dict mapping each argument name to its type annotation as a string (or None if absent).
    """
    tree = ast.parse(source)

    # Assume the first statement is a FunctionDef.
    func_def = tree.body[0]
    if not isinstance(func_def, ast.FunctionDef):
        raise ValueError("No function definition found in source.")

    # Extract the function name.
    function_name = func_def.name

    # Extract argument names and type annotations.
    args_info = {}
    for arg in func_def.args.args:
        arg_annotation = (
            str(ast.unparse(arg.annotation)) if arg.annotation is not None else None
        )
        if arg_annotation is None:
            raise ValueError("All parameters must have a type annotation.")
        args_info[arg.arg] = arg_annotation

    return function_name, args_info


class _GenerationBase(SQLModel):
    """Base Generation Model."""

    project_uuid: UUID | None = Field(
        default=None, foreign_key=f"{PROJECT_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    version_num: int | None = Field(default=None)
    name: str = Field(nullable=False, index=True, min_length=1, max_length=512)
    signature: str = Field(nullable=False)
    code: str = Field(nullable=False)
    hash: str = Field(nullable=False, index=True)
    dependencies: dict[str, DependencyInfo] = Field(
        sa_column=get_json_column(), default_factory=dict
    )
    arg_types: dict[str, str] = Field(sa_column=get_json_column(), default_factory=dict)
    arg_values: dict[str, Any] = Field(
        sa_column=get_json_column(), default_factory=dict
    )
    archived: datetime | None = Field(default=None, index=True)
    custom_id: str | None = Field(default=None, index=True)
    prompt_template: str | None = Field(default=None)
    provider: str | None = Field(default=None)
    model: str | None = Field(default=None)
    call_params: CommonCallParams = Field(
        sa_column=Column(JSONTypeDecorator, nullable=False), default_factory=dict
    )
    is_default: bool | None = Field(default=False, index=True, nullable=True)
    is_managed: bool | None = Field(default=False, index=True, nullable=True)

    @field_validator("arg_types")
    def validate_arg_types(cls, value: dict[str, str]) -> dict[str, str]:
        for arg_name, arg_type in value.items():
            if len(arg_name) > MAX_ARG_NAME_LENGTH:
                raise ValueError(
                    f"Invalid argument name: '{arg_name}'. Must be less than {MAX_ARG_NAME_LENGTH} characters."
                )
            if len(value[arg_name]) > MAX_TYPE_NAME_LENGTH:
                raise ValueError(
                    f"Invalid type name: '{value[arg_name]}'. Must be less than {MAX_TYPE_NAME_LENGTH} characters."
                )

            if not arg_name.isidentifier():
                raise ValueError("Name must be a valid Python identifier.")

            if keyword.iskeyword(arg_name):
                raise ValueError("Name must not be a Python keyword.")

            if len(arg_type) > MAX_TYPE_NAME_LENGTH:
                raise ValueError(
                    f"Invalid type name: '{arg_type}'. Must be less than {MAX_TYPE_NAME_LENGTH} characters."
                )
        return value

    @field_validator("name")
    def validate_name(cls, value: str) -> str:
        if len(value) > 512:
            raise ValueError("Name must be less than 512 characters.")

        if not value.isidentifier():
            raise ValueError("Name must be a valid Python identifier.")
        if keyword.iskeyword(value):
            raise ValueError("Name must not be a Python keyword.")

        if ALLOWED_NAME_REGEX.match(value) is None:
            raise ValueError("Name must be a valid Python identifier.")

        return value

    @model_validator(mode="after")
    def validate_name_and_arg_types(self) -> Self:
        if self.arg_types is None:
            return self

        joined_args = ", ".join(
            [f"{arg_name}: {arg_type}" for arg_name, arg_type in self.arg_types.items()]
        )
        try:
            parse_function_name, parsed_args = extract_function_info(
                f"def {self.name}({joined_args}): ..."
            )
        except:  # noqa: E722
            raise ValueError("Failed to parse function name and arguments.")

        if parse_function_name != self.name:
            raise ValueError(
                f"Function name '{self.name}' does not match parsed function name '{parse_function_name}'."
            )

        if parsed_args != self.arg_types:
            raise ValueError(
                f"Function arguments '{self.arg_types}' do not match parsed arguments '{parsed_args}'."
            )
        return self


class GenerationUpdate(BaseModel):
    """Generation update model."""

    is_default: bool | None = None


class GenerationTable(_GenerationBase, BaseOrganizationSQLModel, table=True):
    """Generation table."""

    __tablename__ = GENERATION_TABLE_NAME  # type: ignore
    project: "ProjectTable" = Relationship(back_populates="generations")
    spans: list["SpanTable"] = Relationship(
        back_populates="generation", cascade_delete=True
    )
    annotations: list["AnnotationTable"] = Relationship(
        back_populates="generation",
        sa_relationship_kwargs={"lazy": "selectin"},  # codespell:ignore selectin
        cascade_delete=True,
    )
    deployments: list["DeploymentTable"] = Relationship(
        back_populates="generation", cascade_delete=True
    )
