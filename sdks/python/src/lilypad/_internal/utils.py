"""Internal utility functions for the Lilypad SDK."""

from typing import Any

import orjson

ORJSON_OPTS = (
    orjson.OPT_NON_STR_KEYS
    | orjson.OPT_NAIVE_UTC
    | orjson.OPT_SERIALIZE_NUMPY
    | orjson.OPT_SERIALIZE_DATACLASS
    | orjson.OPT_SERIALIZE_UUID
)


def json_dumps(obj: Any) -> str:
    """Serialize Python objects to JSON using orjson."""
    # json should be utf-8 encoded, json key should be str
    return orjson.dumps(obj, option=ORJSON_OPTS).decode("utf-8")
