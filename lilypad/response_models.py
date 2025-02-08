"""A module for versioned response models in Lilypad."""

import string
from collections.abc import Callable
from typing import Any, Generic, TypeVar, cast

from pydantic import BaseModel, ConfigDict, Field, create_model
from typing_extensions import ParamSpec

from lilypad._utils import Closure
from lilypad.generations import current_generation
from lilypad.server.client import LilypadClient
from lilypad.server.schemas.response_models import ResponseModelPublic

_P = ParamSpec("_P")
_ResponseModelT = TypeVar("_ResponseModelT", bound=BaseModel)


def _snake_to_pascal(snake: str) -> str:
    return string.capwords(snake.replace("_", " ")).replace(" ", "")


def _build_object_type(
    properties: dict[str, Any], required: list[str], name: str
) -> type[BaseModel]:
    fields = {}
    for prop_name, prop_schema in properties.items():
        class_name = _snake_to_pascal(prop_name)
        type_ = _json_schema_to_python_type(prop_schema, class_name)
        if prop_name in required:
            fields[prop_name] = (
                type_,
                Field(..., description=prop_schema.get("description")),
            )
        else:
            fields[prop_name] = (
                type_ | None,
                Field(None, description=prop_schema.get("description")),
            )

    return create_model(name, __config__=ConfigDict(extra="allow"), **fields)


def _json_schema_to_python_type(schema: dict[str, Any], name: str = "Model") -> Any:  # noqa: ANN401
    """Recursively convert a JSON Schema snippet into a Python type annotation or a dynamically generated pydantic model."""
    json_type = schema.get("type", "any")

    if json_type == "string":
        return str
    elif json_type == "number":
        return float
    elif json_type == "integer":
        return int
    elif json_type == "boolean":
        return bool
    elif json_type == "array":
        # Recursively determine the items type for arrays
        items_schema = schema.get("items", {})
        items_type = _json_schema_to_python_type(items_schema)
        return list[items_type]
    elif json_type == "object":
        # Recursively build a dynamic model for objects
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        return _build_object_type(properties, required, name)
    else:
        # Default fallback
        return Any


def _create_model_from_json_schema(json_schema: dict[str, Any]) -> type[BaseModel]:
    """Create a Pydantic model from a JSON schema."""
    properties = json_schema.get("properties", {})
    required_fields = json_schema.get("required", [])

    fields = {}
    for field_name, field_schema in properties.items():
        field_type = _json_schema_to_python_type(field_schema)

        if field_name in required_fields:
            default = Field(..., description=field_schema.get("description"))
            annotation = field_type
        else:
            default = Field(None, description=field_schema.get("description"))
            annotation = field_type | None

        fields[field_name] = (annotation, default)

    return create_model(
        _snake_to_pascal(json_schema["title"]),
        __config__=ConfigDict(extra="allow"),
        **fields,
    )


def _extract_example(schema: dict, definitions: dict) -> Any:
    """Extract an example from a JSON schema."""
    if "examples" in schema:
        return schema["examples"]

    if "$ref" in schema:
        ref = schema["$ref"]
        ref_name = ref.split("/")[-1]
        ref_schema = definitions.get(ref_name, {})
        return _extract_example(ref_schema, definitions)

    schema_type = schema.get("type")

    if schema_type == "object":
        properties = schema.get("properties", {})
        obj_example = {}
        for prop_name, prop_schema in properties.items():
            prop_example = _extract_example(prop_schema, definitions)
            if prop_example is not None:
                obj_example[prop_name] = prop_example
        return obj_example if obj_example else None

    if schema_type == "array":
        items_schema = schema.get("items", {})
        item_example = _extract_example(items_schema, definitions)
        if item_example is not None:
            return item_example if isinstance(item_example, list) else [item_example]
        return None
    return schema.get("default") or schema.get("title") or ""


class ResponseModel(BaseModel, Generic[_ResponseModelT]):
    """A generic base class for versioned response models.

    This class acts as an interface for versioned response models and can
    be used with generics to represent the concrete model type.
    """

    @classmethod
    def response_model(cls) -> type[_ResponseModelT]:
        """Return the class associated with the current response model version."""
        raise NotImplementedError("response_model method not set")

    @classmethod
    def examples(cls) -> list[dict[str, Any]]:
        """Return examples associated with the current response model version."""
        raise NotImplementedError("examples method not set")


def response_model() -> Callable[
    [type[_ResponseModelT]], ResponseModel[_ResponseModelT]
]:
    """A decorator to create a versioned response model from a Pydantic model.

    This decorator can be used to create a versioned response model from a Pydantic model.

    Returns: A versioned response model class.
    """

    def decorator(cls: type[_ResponseModelT]) -> ResponseModel[_ResponseModelT]:
        if not issubclass(cls, BaseModel):
            raise TypeError(
                "@response_model can only be applied to subclasses of BaseModel"
            )

        Closure.from_fn(cls)

        # Prepare field definitions directly using (annotation, FieldInfo) tuples
        field_definitions = {}
        for field_name, field_info in cls.model_fields.items():
            # field_info is a FieldInfo instance from Pydantic model definition
            field_definitions[field_name] = (field_info.annotation, field_info)

        # Create a new model using create_model
        NewModel = create_model(
            f"{cls.__name__}ResponseModel",
            __base__=ResponseModel[
                cls
            ],  # Use ResponseModel parametrized by cls as the base
            __doc__=cls.__doc__
            if cls.__doc__
            else f"A versioned response model for {cls.__name__}.",
            **field_definitions,
        )

        def get_response_model_version(
            model: type[ResponseModel[_ResponseModelT]],
        ) -> ResponseModelPublic:
            lilypad_client = LilypadClient()
            """Get or create the active version of this response model."""
            generation = current_generation.get()
            response_model_version = lilypad_client.get_response_model_active_version(
                cls, generation
            )
            if response_model_version is None:
                schema_data = model.model_json_schema()
                extracted_example = _extract_example(
                    schema_data, schema_data.get("definitions", {})
                )
                response_model_version = (
                    lilypad_client.get_or_create_response_model_version(
                        cls,
                        schema_data,
                        [extracted_example] if extracted_example is not None else [],
                    )
                )
            if response_model_version is None:
                raise ValueError(
                    f"Response model active version not found or could not be created for class: {cls.__name__}"
                )
            return response_model_version

        @classmethod
        def response_model_method(
            cls_: type[ResponseModel[_ResponseModelT]],
        ) -> type[BaseModel]:
            """Return the class associated with the current response model version."""
            model_version = get_response_model_version(cls_)
            return _create_model_from_json_schema(model_version.schema_data)

        @classmethod
        def examples_method(
            cls_: type[ResponseModel[_ResponseModelT]],
        ) -> list[dict[str, Any]]:
            """Return examples associated with the current version of the response model."""
            model_version = get_response_model_version(cls_)
            return model_version.examples or []

        # Attach classmethods to the new model
        NewModel.response_model = response_model_method  # pyright: ignore [reportAttributeAccessIssue]
        NewModel.examples = examples_method  # pyright: ignore [reportAttributeAccessIssue]

        return cast(ResponseModel[_ResponseModelT], NewModel)

    return decorator
