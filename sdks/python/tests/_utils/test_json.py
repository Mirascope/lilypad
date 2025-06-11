"""Test cases for JSON utilities."""

import dataclasses
import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from uuid import UUID
from collections import deque
from ipaddress import IPv4Address, IPv6Address
import re

from pydantic import BaseModel

from lilypad._utils.json import (
    jsonable_encoder,
    json_dumps,
    fast_jsonable,
    to_text,
    isoformat,
    decimal_encoder,
    UndefinedType,
    _to_json_serializable,
)


class Color(Enum):
    """Test enum."""

    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class SimpleModel(BaseModel):
    """Test Pydantic model."""

    name: str
    age: int
    active: bool = True


class NestedModel(BaseModel):
    """Test nested Pydantic model."""

    id: int
    user: SimpleModel
    tags: list[str]


@dataclasses.dataclass
class DataClassExample:
    """Test dataclass."""

    name: str
    value: float
    items: list[str]


def test_isoformat():
    """Test date/time ISO format conversion."""
    # Test date
    date = datetime.date(2023, 12, 25)
    assert isoformat(date) == "2023-12-25"

    # Test time
    time = datetime.time(14, 30, 45)
    assert isoformat(time) == "14:30:45"

    # Test datetime
    dt = datetime.datetime(2023, 12, 25, 14, 30, 45)
    assert isoformat(dt) == "2023-12-25T14:30:45"


def test_decimal_encoder():
    """Test decimal encoding."""
    # Integer-like decimal
    assert decimal_encoder(Decimal("42")) == 42
    assert decimal_encoder(Decimal("0")) == 0
    assert decimal_encoder(Decimal("-10")) == -10

    # Float-like decimal
    assert decimal_encoder(Decimal("42.5")) == 42.5
    assert decimal_encoder(Decimal("0.1")) == 0.1
    assert decimal_encoder(Decimal("-10.75")) == -10.75

    # Scientific notation
    assert decimal_encoder(Decimal("1E+2")) == 100
    assert decimal_encoder(Decimal("1E-2")) == 0.01


def test_jsonable_encoder_primitives():
    """Test jsonable_encoder with primitive types."""
    assert jsonable_encoder("hello") == "hello"
    assert jsonable_encoder(42) == 42
    assert jsonable_encoder(3.14) == 3.14
    assert jsonable_encoder(True) is True
    assert jsonable_encoder(None) is None


def test_jsonable_encoder_pydantic():
    """Test jsonable_encoder with Pydantic models."""
    model = SimpleModel(name="Alice", age=30)
    result = jsonable_encoder(model)
    assert result == {"name": "Alice", "age": 30, "active": True}

    # Test exclude_defaults
    result = jsonable_encoder(model, exclude_defaults=True)
    assert result == {"name": "Alice", "age": 30}

    # Test exclude_none with a model that allows None
    class OptionalModel(BaseModel):
        name: str
        age: int
        active: bool | None = None

    model_with_none = OptionalModel(name="Bob", age=25, active=None)
    result = jsonable_encoder(model_with_none, exclude_none=True)
    assert result == {"name": "Bob", "age": 25}


def test_jsonable_encoder_nested_pydantic():
    """Test jsonable_encoder with nested Pydantic models."""
    user = SimpleModel(name="Alice", age=30)
    nested = NestedModel(id=1, user=user, tags=["python", "testing"])

    result = jsonable_encoder(nested)
    assert result == {"id": 1, "user": {"name": "Alice", "age": 30, "active": True}, "tags": ["python", "testing"]}


def test_jsonable_encoder_dataclass():
    """Test jsonable_encoder with dataclasses."""
    dc = DataClassExample(name="test", value=3.14, items=["a", "b", "c"])
    result = jsonable_encoder(dc)
    assert result == {"name": "test", "value": 3.14, "items": ["a", "b", "c"]}


def test_jsonable_encoder_enum():
    """Test jsonable_encoder with enums."""
    assert jsonable_encoder(Color.RED) == "red"
    assert jsonable_encoder(Color.GREEN) == "green"


def test_jsonable_encoder_path():
    """Test jsonable_encoder with Path objects."""
    path = Path("/home/user/file.txt")
    assert jsonable_encoder(path) == "/home/user/file.txt"


def test_jsonable_encoder_dict():
    """Test jsonable_encoder with dictionaries."""
    data = {"name": "Alice", "age": 30, "active": True}
    assert jsonable_encoder(data) == data

    # Test with include
    result = jsonable_encoder(data, include={"name", "age"})
    assert result == {"name": "Alice", "age": 30}

    # Test with exclude
    result = jsonable_encoder(data, exclude={"active"})
    assert result == {"name": "Alice", "age": 30}

    # Test exclude_none
    data_with_none = {"name": "Bob", "age": None}
    result = jsonable_encoder(data_with_none, exclude_none=True)
    assert result == {"name": "Bob"}


def test_jsonable_encoder_sequences():
    """Test jsonable_encoder with various sequence types."""
    # List
    assert jsonable_encoder([1, 2, 3]) == [1, 2, 3]

    # Set
    result = jsonable_encoder({1, 2, 3})
    assert sorted(result) == [1, 2, 3]

    # Tuple
    assert jsonable_encoder((1, 2, 3)) == [1, 2, 3]

    # Deque
    assert jsonable_encoder(deque([1, 2, 3])) == [1, 2, 3]


def test_jsonable_encoder_datetime():
    """Test jsonable_encoder with datetime objects."""
    # Date
    date = datetime.date(2023, 12, 25)
    assert jsonable_encoder(date) == "2023-12-25"

    # Time
    time = datetime.time(14, 30, 45)
    assert jsonable_encoder(time) == "14:30:45"

    # Datetime
    dt = datetime.datetime(2023, 12, 25, 14, 30, 45)
    assert jsonable_encoder(dt) == "2023-12-25T14:30:45"

    # Timedelta
    td = datetime.timedelta(days=1, hours=2, minutes=30)
    assert jsonable_encoder(td) == 95400.0  # Total seconds


def test_jsonable_encoder_special_types():
    """Test jsonable_encoder with special types."""
    # UUID
    uuid = UUID("12345678-1234-5678-1234-567812345678")
    assert jsonable_encoder(uuid) == str(uuid)

    # IPv4Address
    ipv4 = IPv4Address("192.168.1.1")
    assert jsonable_encoder(ipv4) == "192.168.1.1"

    # IPv6Address
    ipv6 = IPv6Address("::1")
    assert jsonable_encoder(ipv6) == "::1"

    # Decimal
    dec = Decimal("42.5")
    assert jsonable_encoder(dec) == 42.5

    # Regex pattern
    pattern = re.compile(r"\d+")
    assert jsonable_encoder(pattern) == r"\d+"


def test_jsonable_encoder_undefined():
    """Test jsonable_encoder with UndefinedType."""
    undefined = UndefinedType()
    assert jsonable_encoder(undefined) is None


def test_jsonable_encoder_custom_encoder():
    """Test jsonable_encoder with custom encoders."""

    class CustomType:
        def __init__(self, value):
            self.value = value

    custom_encoder = {CustomType: lambda obj: f"custom_{obj.value}"}

    obj = CustomType("test")
    result = jsonable_encoder(obj, custom_encoder=custom_encoder)
    assert result == "custom_test"


def test_jsonable_encoder_sqlalchemy_safe():
    """Test jsonable_encoder with SQLAlchemy safety."""
    data = {"name": "test", "_sa_instance_state": "should_be_excluded", "_sa_metadata": "also_excluded", "value": 42}

    result = jsonable_encoder(data, sqlalchemy_safe=True)
    assert "_sa_instance_state" not in result
    assert "_sa_metadata" not in result
    assert result == {"name": "test", "value": 42}


def test_json_dumps():
    """Test json_dumps function."""
    data = {"name": "Alice", "age": 30, "active": True, "scores": [1, 2, 3]}

    result = json_dumps(data)
    assert isinstance(result, str)
    assert '"name":"Alice"' in result
    assert '"age":30' in result


def test_to_json_serializable():
    """Test _to_json_serializable function."""
    # Test with simple model
    model = SimpleModel(name="Alice", age=30)
    result = _to_json_serializable(model)
    assert result == {"name": "Alice", "age": 30, "active": True}

    # Test with circular reference detection
    data = {"key": "value"}
    data["self"] = data
    result = _to_json_serializable(data)
    assert result["self"] == "<CircularRef dict>"


def test_fast_jsonable():
    """Test fast_jsonable function."""
    # Primitives
    assert fast_jsonable("hello") == "hello"
    assert fast_jsonable(42) == 42
    assert fast_jsonable(3.14) == 3.14
    assert fast_jsonable(True) is True
    assert fast_jsonable(None) is None

    # Complex objects
    model = SimpleModel(name="Alice", age=30)
    result = fast_jsonable(model)
    assert isinstance(result, str)
    assert "Alice" in result

    # Lists
    result = fast_jsonable([1, 2, 3])
    assert result == "[1,2,3]"


def test_to_text():
    """Test to_text function."""
    # String
    assert to_text("hello") == "hello"

    # Numbers
    assert to_text(42) == "42"
    assert to_text(3.14) == "3.14"

    # Boolean
    assert to_text(True) == "True"
    assert to_text(False) == "False"

    # None
    assert to_text(None) == "None"

    # Complex objects
    model = SimpleModel(name="Alice", age=30)
    result = to_text(model)
    assert isinstance(result, str)
    assert "Alice" in result

    # Custom serializers
    class CustomType:
        def __init__(self, value):
            self.value = value

    custom_serializers = {CustomType: lambda obj: f"custom_{obj.value}"}

    obj = CustomType("test")
    result = to_text(obj, custom_serializers=custom_serializers)
    assert result == "custom_test"
