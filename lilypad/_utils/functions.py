"""Utilities for Python functions"""

import dataclasses
import datetime
import inspect
import os
import types
from collections import defaultdict, deque
from collections.abc import AsyncIterable, Callable, Coroutine, Iterable
from decimal import Decimal
from enum import Enum
from functools import partial, wraps
from importlib import import_module
from ipaddress import (
    IPv4Address,
    IPv4Interface,
    IPv4Network,
    IPv6Address,
    IPv6Interface,
    IPv6Network,
)
from pathlib import Path, PurePath
from re import Pattern
from types import GeneratorType
from typing import (
    Any,
    ParamSpec,
    TypeAlias,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)
from uuid import UUID

from mirascope.core import base as mb
from pydantic import BaseModel

from ..messages import Message
from ..server.schemas.generations import GenerationCreate, GenerationPublic, Provider
from .fn_is_async import fn_is_async

_P = ParamSpec("_P")
_R = TypeVar("_R")

MAP_STANDARD_TYPES = {
    "List": "list",
    "Dict": "dict",
    "Set": "set",
    "Tuple": "tuple",
    "NoneType": "None",
}


def _get_type_str(type_hint: Any) -> str:
    """Convert a type hint to its string representation.
    Handles both traditional Optional/Union syntax and new | operator syntax.
    """
    # Handle primitive types and None
    if type_hint is type(None):  # noqa
        return "None"  # Instead of "NoneType"
    if type_hint in (str, int, float, bool):
        return type_hint.__name__

    # Get the origin type
    origin = get_origin(type_hint)
    if origin is None:
        # Handle non-generic types
        if hasattr(type_hint, "__name__"):
            return type_hint.__name__
        return str(type_hint)

    # Handle Optional types (from both syntaxes)
    args = get_args(type_hint)
    if (
        (origin is Union or origin is types.UnionType)
        and len(args) == 2
        and type(None) in args
    ):
        other_type = next(arg for arg in args if arg is not type(None))
        return f"Optional[{_get_type_str(other_type)}]"

    # Handle Union types (both traditional and | operator)
    if origin is Union or origin is types.UnionType:
        formatted_args = [_get_type_str(arg) for arg in args]
        return f"Union[{', '.join(formatted_args)}]"

    # Handle other generic types (List, Dict, etc)
    args_str = ", ".join(_get_type_str(arg) for arg in args)
    if not args:
        return origin.__name__

    return f"{origin.__name__}[{args_str}]"


ArgTypes: TypeAlias = dict[str, str]
ArgValues: TypeAlias = dict[str, Any]


def inspect_arguments(
    fn: Callable, *args: Any, **kwargs: Any
) -> tuple[ArgTypes, ArgValues]:
    """Inspect a function's arguments and their values.
    Returns type information and values for all arguments.
    """
    sig = inspect.signature(fn)
    params = sig.parameters
    bound_args = sig.bind(*args, **kwargs)
    bound_args.apply_defaults()

    arg_types = {}
    arg_values = {}

    for name, param in params.items():
        if name in bound_args.arguments:
            value = bound_args.arguments[name]
            arg_values[name] = value

            if param.annotation is not param.empty:
                arg_types[name] = _get_type_str(param.annotation)
            else:
                # Infer type from value if no annotation
                arg_types[name] = type(value).__name__

    return arg_types, arg_values


def _construct_call_decorator(
    fn: Callable, provider: Provider, model: str
) -> partial[Any]:
    client = None
    if provider == Provider.OPENROUTER:
        provider = Provider.OPENAI
        if fn_is_async(fn):
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY"),
            )
        else:
            from openai import OpenAI

            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY"),
            )

    return partial(
        import_module(f"mirascope.core.{provider.value}").call,
        model=model,
        json_mode=False,
        client=client,
    )


@overload
def create_mirascope_call(
    fn: Callable[_P, Coroutine[Any, Any, _R]],
    generation: GenerationPublic | GenerationCreate,
    provider: Provider,
    model: str,
    trace_decorator: Callable | None,
) -> Callable[_P, Coroutine[Any, Any, _R]]: ...


@overload
def create_mirascope_call(
    fn: Callable[_P, _R],
    generation: GenerationPublic | GenerationCreate,
    provider: Provider,
    model: str,
    trace_decorator: Callable | None,
) -> Callable[_P, _R]: ...


def create_mirascope_call(
    fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]],
    generation: GenerationPublic | GenerationCreate,
    provider: Provider,
    model: str,
    trace_decorator: Callable | None,
) -> Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]:
    """Returns the constructed Mirascope call function."""
    if not trace_decorator:
        trace_decorator = lambda x: x  # noqa: E731

    call_decorator = _construct_call_decorator(fn, provider, model)
    return_type = get_type_hints(fn).get("return", type(None))
    if fn_is_async(fn):

        @mb.prompt_template(generation.prompt_template)
        @wraps(fn)
        async def prompt_template_async(
            *args: _P.args, **kwargs: _P.kwargs
        ) -> mb.BaseDynamicConfig:
            return {"call_params": generation.call_params}

        @wraps(fn)
        async def inner_async(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            if return_type is str:
                traced_call = trace_decorator(call_decorator()(prompt_template_async))
                return (await traced_call(*args, **kwargs)).content
            origin_return_type = get_origin(return_type)
            if origin_return_type is AsyncIterable and get_args(return_type) == (str,):
                traced_call = trace_decorator(
                    call_decorator(stream=True)(prompt_template_async)
                )

                async def iterable() -> AsyncIterable[str]:
                    async for chunk, _ in await traced_call(*args, **kwargs):
                        yield chunk.content

                return cast(_R, iterable())
            elif origin_return_type is Message:
                traced_call = trace_decorator(
                    call_decorator(tools=list(get_args(return_type)))(
                        prompt_template_async
                    )
                )
                return cast(_R, Message(await traced_call(*args, **kwargs)))  # pyright: ignore [reportAbstractUsage] # pyright: ignore [reportAbstractUsage]
            elif (
                origin_return_type is AsyncIterable
                and len(iter_args := get_args(return_type)) == 1
                and issubclass((response_model := iter_args[0]), BaseModel)
            ):
                traced_call = trace_decorator(
                    call_decorator(response_model=response_model, stream=True)(
                        prompt_template_async
                    )
                )
                return cast(_R, await traced_call(*args, **kwargs))
            elif (
                inspect.isclass(origin_return_type)
                and issubclass(origin_return_type, Message)
                or (
                    inspect.isclass(return_type)
                    and type(return_type) is not types.GenericAlias
                    and issubclass(return_type, Message)
                )
            ):
                traced_call = trace_decorator(call_decorator()(prompt_template_async))
                return cast(_R, Message(await traced_call(*args, **kwargs)))  # pyright: ignore [reportAbstractUsage]
            elif mb._utils.is_base_type(return_type) or (
                inspect.isclass(return_type)
                and type(return_type) is not types.GenericAlias
                and issubclass(return_type, BaseModel)
            ):
                traced_call = trace_decorator(
                    call_decorator(response_model=return_type)(prompt_template_async)
                )
                return cast(_R, await traced_call(*args, **kwargs))
            else:
                raise ValueError(f"Unsupported return type `{return_type}`.")

        return inner_async
    else:

        @mb.prompt_template(generation.prompt_template)
        @wraps(fn)
        def prompt_template(
            *args: _P.args, **kwargs: _P.kwargs
        ) -> mb.BaseDynamicConfig:
            return {"call_params": generation.call_params}

        @wraps(fn)
        def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            if return_type is str:
                traced_call = trace_decorator(call_decorator()(prompt_template))
                return traced_call(*args, **kwargs).content
            origin_return_type = get_origin(return_type)
            if origin_return_type is Iterable and get_args(return_type) == (str,):
                traced_call = trace_decorator(
                    call_decorator(stream=True)(prompt_template)
                )

                def iterable() -> Iterable[str]:
                    for chunk, _ in traced_call(*args, **kwargs):
                        yield chunk.content

                return cast(_R, iterable())
            elif origin_return_type is Message:
                traced_call = trace_decorator(
                    call_decorator(tools=list(get_args(return_type)))(prompt_template)
                )
                return cast(_R, Message(traced_call(*args, **kwargs)))  # pyright: ignore [reportAbstractUsage]
            elif (
                origin_return_type is Iterable
                and len(iter_args := get_args(return_type)) == 1
                and issubclass((response_model := iter_args[0]), BaseModel)
            ):
                traced_call = trace_decorator(
                    call_decorator(response_model=response_model, stream=True)(
                        prompt_template
                    )
                )
                return cast(_R, traced_call(*args, **kwargs))
            elif (
                inspect.isclass(origin_return_type)
                and issubclass(origin_return_type, Message)
                or inspect.isclass(return_type)
                and issubclass(return_type, Message)
            ):
                traced_call = trace_decorator(call_decorator()(prompt_template))
                return cast(_R, Message(traced_call(*args, **kwargs)))  # pyright: ignore [reportAbstractUsage]
            elif mb._utils.is_base_type(return_type) or issubclass(
                return_type, BaseModel
            ):
                traced_call = trace_decorator(
                    call_decorator(response_model=return_type)(prompt_template)
                )
                return cast(_R, traced_call(*args, **kwargs))
            else:
                raise ValueError(f"Unsupported return type `{return_type}`.")

        return inner


IncEx = set[str] | dict[str, Any]


# Helper function for date and time formatting
def isoformat(o: datetime.date | datetime.time) -> str:
    """Convert date or time object to ISO format string"""
    return o.isoformat()


# Helper function for decimal encoding
def decimal_encoder(dec_value: Decimal) -> int | float:
    """Encodes a Decimal as int if there's no exponent, otherwise float

    This is useful when we use ConstrainedDecimal to represent Numeric(x,0)
    where a integer (but not int typed) is used. Encoding this as a float
    results in failed round-tripping between encode and parse.

    >>> decimal_encoder(Decimal("1.0"))
    1.0

    >>> decimal_encoder(Decimal("1"))
    1
    """
    if dec_value.as_tuple().exponent >= 0:
        return int(dec_value)
    else:
        return float(dec_value)


ENCODERS_BY_TYPE: dict[type[Any], Callable[[Any], Any]] = {
    bytes: lambda o: o.decode(),
    datetime.date: isoformat,
    datetime.datetime: isoformat,
    datetime.time: isoformat,
    datetime.timedelta: lambda td: td.total_seconds(),
    Decimal: decimal_encoder,
    Enum: lambda o: o.value,
    frozenset: list,
    deque: list,
    GeneratorType: list,
    IPv4Address: str,
    IPv4Interface: str,
    IPv4Network: str,
    IPv6Address: str,
    IPv6Interface: str,
    IPv6Network: str,
    Path: str,
    Pattern: lambda o: o.pattern,
    set: list,
    UUID: str,
}


def generate_encoders_by_class_tuples(
    type_encoder_map: dict[Any, Callable[[Any], Any]],
) -> dict[Callable[[Any], Any], tuple[Any, ...]]:
    """Generate a mapping of encoder functions to tuples of types they can handle"""
    encoders_by_class_tuples: dict[Callable[[Any], Any], tuple[Any, ...]] = defaultdict(
        tuple
    )
    for type_, encoder in type_encoder_map.items():
        encoders_by_class_tuples[encoder] += (type_,)
    return encoders_by_class_tuples


# Pre-compute the encoder lookup table
encoders_by_class_tuples = generate_encoders_by_class_tuples(ENCODERS_BY_TYPE)


class UndefinedType:
    """A class to represent undefined values"""

    pass


def jsonable_encoder(
    obj: Any,
    include: IncEx | None = None,
    exclude: IncEx | None = None,
    by_alias: bool = True,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    custom_encoder: dict[Any, Callable[[Any], Any]] | None = None,
    sqlalchemy_safe: bool = True,
) -> Any:
    """Convert any object to something that can be encoded in JSON.

    This utility function converts various Python objects into JSON-compatible types.
    It handles Pydantic models, dataclasses, enums, paths, dictionaries, lists, and more.

    Parameters:
    -----------
    obj : Any
        The input object to convert to JSON.

    include : Optional[IncEx]
        Fields to include in the output.

    exclude : Optional[IncEx]
        Fields to exclude from the output.

    by_alias : bool
        Whether to use field aliases from Pydantic models.

    exclude_unset : bool
        Whether to exclude unset fields from Pydantic models.

    exclude_defaults : bool
        Whether to exclude fields with default values from Pydantic models.

    exclude_none : bool
        Whether to exclude fields with None values.

    custom_encoder : Optional[Dict[Any, Callable[[Any], Any]]]
        Custom encoders for specific types.

    sqlalchemy_safe : bool
        Whether to exclude SQLAlchemy internal fields.

    Returns:
    --------
    Any
        A JSON-compatible representation of the input object.
    """
    custom_encoder = custom_encoder or {}

    # Apply custom encoder if available for this type
    if custom_encoder:
        if type(obj) in custom_encoder:
            return custom_encoder[type(obj)](obj)
        else:
            for encoder_type, encoder_instance in custom_encoder.items():
                if isinstance(obj, encoder_type):
                    return encoder_instance(obj)

    # Convert sets to lists for include/exclude parameters
    if include is not None and not isinstance(include, set | dict):
        include = set(include)
    if exclude is not None and not isinstance(exclude, set | dict):
        exclude = set(exclude)

    # Handle Pydantic models
    if isinstance(obj, BaseModel):
        # Convert model to dict using Pydantic v2 approach
        obj_dict = obj.model_dump(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults,
        )

        # Handle root models
        if "__root__" in obj_dict:
            obj_dict = obj_dict["__root__"]

        # Recursively encode the resulting dict
        return jsonable_encoder(
            obj_dict,
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults,
            custom_encoder=custom_encoder,
            sqlalchemy_safe=sqlalchemy_safe,
        )

    # Handle dataclasses
    if dataclasses.is_dataclass(obj):
        obj_dict = dataclasses.asdict(obj)
        return jsonable_encoder(
            obj_dict,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            custom_encoder=custom_encoder,
            sqlalchemy_safe=sqlalchemy_safe,
        )

    # Handle Enum types
    if isinstance(obj, Enum):
        return obj.value

    # Handle Path objects
    if isinstance(obj, PurePath):
        return str(obj)

    # Handle primitive types directly
    if isinstance(obj, str | int | float | type(None)):
        return obj

    # Handle undefined values
    if isinstance(obj, UndefinedType):
        return None

    # Handle dictionaries
    if isinstance(obj, dict):
        encoded_dict = {}
        allowed_keys = set(obj.keys())

        if include is not None:
            allowed_keys &= set(include)
        if exclude is not None:
            allowed_keys -= set(exclude)

        for key, value in obj.items():
            if (
                (
                    not sqlalchemy_safe
                    or (not isinstance(key, str))
                    or (not key.startswith("_sa"))
                )
                and (value is not None or not exclude_none)
                and key in allowed_keys
            ):
                encoded_key = jsonable_encoder(
                    key,
                    by_alias=by_alias,
                    exclude_unset=exclude_unset,
                    exclude_none=exclude_none,
                    custom_encoder=custom_encoder,
                    sqlalchemy_safe=sqlalchemy_safe,
                )
                encoded_value = jsonable_encoder(
                    value,
                    by_alias=by_alias,
                    exclude_unset=exclude_unset,
                    exclude_none=exclude_none,
                    custom_encoder=custom_encoder,
                    sqlalchemy_safe=sqlalchemy_safe,
                )
                encoded_dict[encoded_key] = encoded_value
        return encoded_dict

    # Handle sequences (list, set, etc.)
    if isinstance(obj, list | set | frozenset | GeneratorType | tuple | deque):
        encoded_list = []
        for item in obj:
            encoded_list.append(
                jsonable_encoder(
                    item,
                    include=include,
                    exclude=exclude,
                    by_alias=by_alias,
                    exclude_unset=exclude_unset,
                    exclude_defaults=exclude_defaults,
                    exclude_none=exclude_none,
                    custom_encoder=custom_encoder,
                    sqlalchemy_safe=sqlalchemy_safe,
                )
            )
        return encoded_list

    # Handle types with specific encoders
    if type(obj) in ENCODERS_BY_TYPE:
        return ENCODERS_BY_TYPE[type(obj)](obj)

    # Check all registered encoders (more efficient for inheritance hierarchies)
    for encoder, classes_tuple in encoders_by_class_tuples.items():
        if isinstance(obj, classes_tuple):
            return encoder(obj)

    # Handle objects without any specific encoder
    # Try to convert to dict first, then fall back to vars()
    try:
        data = dict(obj)
    except Exception as e:
        errors: list[Exception] = [e]
        try:
            data = vars(obj)
        except Exception as e:
            errors.append(e)
            raise ValueError(errors) from e

    # Recursively encode the resulting dict
    return jsonable_encoder(
        data,
        include=include,
        exclude=exclude,
        by_alias=by_alias,
        exclude_unset=exclude_unset,
        exclude_defaults=exclude_defaults,
        exclude_none=exclude_none,
        custom_encoder=custom_encoder,
        sqlalchemy_safe=sqlalchemy_safe,
    )


__all__ = [
    "create_mirascope_call",
    "inspect_arguments",
    "jsonable_encoder",
    "ArgTypes",
    "ArgValues",
]
