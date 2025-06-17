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


# Additional tests for missing coverage


def test_jsonable_encoder_include_exclude_edge_cases():
    """Test jsonable_encoder with edge cases for include/exclude."""
    data = {"a": 1, "b": 2, "c": 3}

    # Test with list include/exclude instead of set
    result = jsonable_encoder(data, include=["a", "b"])
    assert result == {"a": 1, "b": 2}

    result = jsonable_encoder(data, exclude=["c"])
    assert result == {"a": 1, "b": 2}

    # Test with dict include/exclude
    result = jsonable_encoder(data, include={"a": True, "b": True})
    assert result == {"a": 1, "b": 2}


def test_jsonable_encoder_custom_encoder_inheritance():
    """Test custom encoder with inheritance."""

    class BaseType:
        def __init__(self, value):
            self.value = value

    class DerivedType(BaseType):
        pass

    # Custom encoder for base type should work for derived type
    custom_encoder = {BaseType: lambda obj: f"base_{obj.value}"}

    derived_obj = DerivedType("test")
    result = jsonable_encoder(derived_obj, custom_encoder=custom_encoder)
    assert result == "base_test"


def test_jsonable_encoder_pydantic_root_model():
    """Test jsonable_encoder with Pydantic root models."""
    from unittest.mock import patch

    # Simulate a root model response
    class RootModel(BaseModel):
        value: str

    model = RootModel(value="test")
    # Manually add __root__ to simulate old Pydantic behavior
    model_dict = model.model_dump()
    model_dict["__root__"] = "root_value"

    # Use patch to mock the method without causing deletion issues
    with patch.object(type(model), "model_dump", return_value=model_dict):
        result = jsonable_encoder(model)
        # Should process the __root__ value recursively
        assert result == "root_value"


def test_jsonable_encoder_complex_object_fallback():
    """Test jsonable_encoder fallback for complex objects."""

    class ComplexObject:
        def __init__(self):
            self.name = "test"
            self.value = 42

    obj = ComplexObject()
    result = jsonable_encoder(obj)
    assert result == {"name": "test", "value": 42}


def test_jsonable_encoder_mapping_fallback():
    """Test jsonable_encoder with Mapping objects."""
    from collections import UserDict

    class CustomMapping(UserDict):
        def __init__(self):
            super().__init__({"key": "value", "num": 123})

    mapping = CustomMapping()
    result = jsonable_encoder(mapping)
    assert result == {"key": "value", "num": 123}


def test_jsonable_encoder_iterable_fallback():
    """Test jsonable_encoder with custom iterable objects."""

    class CustomIterable:
        def __init__(self, data):
            self._data = data

        def __iter__(self):
            return iter(self._data.items())

    iterable = CustomIterable({"a": 1, "b": 2})
    result = jsonable_encoder(iterable)
    assert result == {"a": 1, "b": 2}


def test_jsonable_encoder_error_handling():
    """Test jsonable_encoder error handling."""

    class ProblematicObject:
        def __iter__(self):
            raise ValueError("Cannot iterate")

        def __getattribute__(self, name):
            if name == "__dict__":
                raise AttributeError("No __dict__")
            if name == "dir":
                raise AttributeError("No dir")
            return super().__getattribute__(name)

        def __dir__(self):
            raise RuntimeError("Cannot get dir")

    obj = ProblematicObject()

    # Should raise ValueError with list of errors
    import pytest

    with pytest.raises(ValueError):
        jsonable_encoder(obj)


def test_jsonable_encoder_type_object():
    """Test jsonable_encoder with type objects."""

    class TestClass:
        class_var = "test_value"

    result = jsonable_encoder(TestClass)
    # Should use vars() for type objects
    assert isinstance(result, dict)
    # Class objects have __dict__ so vars() should work
    expected_attrs = vars(TestClass)
    # Verify some attributes are present
    assert "class_var" in result
    assert result["class_var"] == "test_value"


def test_decimal_encoder_edge_cases():
    """Test decimal_encoder with edge cases."""
    # Test with very large exponent
    assert decimal_encoder(Decimal("1E+10")) == 10000000000

    # Test with negative exponent
    assert decimal_encoder(Decimal("1E-10")) == 1e-10

    # Test with zero exponent
    assert decimal_encoder(Decimal("1E+0")) == 1


def test_to_json_serializable_custom_serializers():
    """Test _to_json_serializable with custom serializers."""

    class CustomType:
        def __init__(self, value):
            self.value = value

    # Test with working custom serializer
    custom_serializers = {CustomType: lambda obj: f"custom_{obj.value}"}
    obj = CustomType("test")
    result = _to_json_serializable(obj, custom_serializers=custom_serializers)
    assert result == "custom_test"

    # Test with failing custom serializer
    failing_serializers = {CustomType: lambda obj: 1 / 0}  # Division by zero
    result = _to_json_serializable(obj, custom_serializers=failing_serializers)
    # Should fall back to default behavior
    assert result == obj  # Should return the object as-is when no encoder found


def test_to_json_serializable_global_serializers():
    """Test _to_json_serializable with global serializer registry."""

    class CustomType:
        def __init__(self, value):
            self.value = value

    # Test with working global serializer
    import unittest.mock

    with unittest.mock.patch("lilypad._utils.json.get_serializer") as mock_get_serializer:
        mock_get_serializer.return_value = lambda obj: f"global_{obj.value}"
        obj = CustomType("test")
        result = _to_json_serializable(obj)
        assert result == "global_test"

    # Test with failing global serializer
    with unittest.mock.patch("lilypad._utils.json.get_serializer") as mock_get_serializer:
        mock_get_serializer.return_value = lambda obj: 1 / 0  # Division by zero
        obj = CustomType("test")
        result = _to_json_serializable(obj)
        # Should fall back to default behavior
        assert result == obj


def test_to_json_serializable_dataclass_fields():
    """Test _to_json_serializable with dataclass field access."""

    @dataclasses.dataclass
    class DataClassWithNone:
        name: str
        value: int | None = None

    dc = DataClassWithNone(name="test", value=None)
    result = _to_json_serializable(dc)
    assert result == {"name": "test", "value": None}


def test_to_json_serializable_sequences():
    """Test _to_json_serializable with various sequence types."""

    # Test generator
    def test_generator():
        yield 1
        yield 2
        yield 3

    result = _to_json_serializable(test_generator())
    assert result == [1, 2, 3]

    # Test frozenset
    result = _to_json_serializable(frozenset([3, 1, 2]))
    assert sorted(result) == [1, 2, 3]


def test_any_to_text_error_handling():
    """Test _any_to_text error handling."""
    from lilypad._utils.json import _any_to_text

    class UnserializableObject:
        def __repr__(self):
            return "UnserializableObject()"

        def __getattribute__(self, name):
            if name in ("__dict__", "__slots__", "__class__"):
                raise AttributeError(f"No {name}")
            if name == "__repr__":
                return lambda: "UnserializableObject()"
            if name in ("__dir__", "dir"):
                raise AttributeError(f"No {name}")
            raise AttributeError(f"No attribute {name}")

        def __dir__(self):
            raise RuntimeError("Cannot get dir")

    obj = UnserializableObject()
    result = _any_to_text(obj)
    # Should fall back to repr() when everything else fails
    assert result == "UnserializableObject()"


def test_any_to_text_primitive_passthrough():
    """Test _any_to_text with JSON-safe primitives."""
    from lilypad._utils.json import _any_to_text

    # Test primitives that should be returned as-is
    assert _any_to_text("hello") == "hello"
    assert _any_to_text(42) == 42
    assert _any_to_text(3.14) == 3.14
    assert _any_to_text(True) is True
    assert _any_to_text(False) is False
    assert _any_to_text(None) is None


def test_jsonable_encoder_generator_handling():
    """Test jsonable_encoder with generators."""

    def test_generator():
        yield 1
        yield 2
        yield 3

    result = jsonable_encoder(test_generator())
    assert result == [1, 2, 3]


def test_jsonable_encoder_nested_sequences():
    """Test jsonable_encoder with nested sequences."""
    nested_data = [{"a": 1}, {"b": [2, 3]}, {4, 5, 6}]
    result = jsonable_encoder(nested_data)

    # Set should be converted to list
    assert result[0] == {"a": 1}
    assert result[1] == {"b": [2, 3]}
    assert sorted(result[2]) == [4, 5, 6]  # Set order is not guaranteed


def test_to_json_serializable_circular_reference_multiple_objects():
    """Test _to_json_serializable with multiple circular references."""
    obj1 = {"name": "obj1"}
    obj2 = {"name": "obj2"}
    obj1["ref"] = obj2
    obj2["ref"] = obj1

    result = _to_json_serializable(obj1)
    assert result["name"] == "obj1"
    assert result["ref"]["name"] == "obj2"
    assert result["ref"]["ref"] == "<CircularRef dict>"


def test_generate_encoders_by_class_tuples():
    """Test generate_encoders_by_class_tuples function."""
    from lilypad._utils.json import generate_encoders_by_class_tuples

    # Use a single encoder function reference for multiple types
    def multiplier_encoder(x):
        return x * 2

    type_encoder_map = {
        str: lambda x: x.upper(),
        int: multiplier_encoder,
        float: multiplier_encoder,  # Same encoder as int
    }

    result = generate_encoders_by_class_tuples(type_encoder_map)

    # Should group types by encoder function
    assert len(result) == 2  # Two unique encoders

    # Find the encoder that handles int/float
    for encoder, types in result.items():
        if encoder is multiplier_encoder:
            assert int in types
            assert float in types
            break
    else:
        assert False, "multiplier_encoder not found in result"


def test_map_standard_types():
    """Test MAP_STANDARD_TYPES constant."""
    from lilypad._utils.json import MAP_STANDARD_TYPES

    assert MAP_STANDARD_TYPES["List"] == "list"
    assert MAP_STANDARD_TYPES["Dict"] == "dict"
    assert MAP_STANDARD_TYPES["Set"] == "set"
    assert MAP_STANDARD_TYPES["Tuple"] == "tuple"
    assert MAP_STANDARD_TYPES["NoneType"] == "None"


def test_undefined_type():
    """Test UndefinedType class."""
    undefined1 = UndefinedType()
    undefined2 = UndefinedType()

    # Should be different instances
    assert undefined1 is not undefined2
    assert isinstance(undefined1, UndefinedType)
    assert isinstance(undefined2, UndefinedType)


def test_jsonable_encoder_with_custom_encoder_class_hierarchy():
    """Test jsonable_encoder with custom encoders and class hierarchies."""

    class BaseType:
        def __init__(self, value):
            self.value = value

    class DerivedType(BaseType):
        pass

    # Test custom encoder with class tuple matching
    custom_encoder = {BaseType: lambda obj: f"encoded_{obj.value}"}

    obj = DerivedType("test")
    result = jsonable_encoder(obj, custom_encoder=custom_encoder)
    assert result == "encoded_test"


def test_jsonable_encoder_fallback_to_vars():
    """Test jsonable_encoder fallback to vars() for objects without __dict__."""

    class TypeWithoutDict:
        __slots__ = ("value",)

        def __init__(self, value):
            self.value = value

    class TypeWithoutDictAndNoVars:
        """A type that will trigger the exception path."""

        __slots__ = ()

    # This should trigger the path where we try to get attributes from dir()
    obj = TypeWithoutDictAndNoVars()

    # The jsonable_encoder should handle this gracefully
    result = jsonable_encoder(obj)
    assert isinstance(result, dict)


def test_to_json_serializable_enum():
    """Test _to_json_serializable with Enum objects."""
    result = _to_json_serializable(Color.RED)
    assert result == "red"


def test_to_json_serializable_decimal():
    """Test _to_json_serializable with Decimal objects."""
    from decimal import Decimal

    decimal_val = Decimal("123.456")
    result = _to_json_serializable(decimal_val)
    assert result == 123.456


def test_to_json_serializable_timedelta():
    """Test _to_json_serializable with timedelta objects."""
    import datetime

    delta = datetime.timedelta(hours=2, minutes=30)
    result = _to_json_serializable(delta)
    assert result == 9000.0  # 2.5 hours in seconds


def test_to_json_serializable_ipv4_ipv6_and_path():
    """Test _to_json_serializable with IP addresses and Path objects."""
    from ipaddress import IPv4Address, IPv6Address, IPv4Interface, IPv4Network, IPv6Interface, IPv6Network
    from pathlib import PurePath
    from uuid import UUID

    # Test IPv4Address
    ipv4 = IPv4Address("192.168.1.1")
    assert _to_json_serializable(ipv4) == "192.168.1.1"

    # Test IPv6Address
    ipv6 = IPv6Address("::1")
    assert _to_json_serializable(ipv6) == "::1"

    # Test IPv4Interface
    ipv4_interface = IPv4Interface("192.168.1.1/24")
    assert _to_json_serializable(ipv4_interface) == "192.168.1.1/24"

    # Test IPv4Network
    ipv4_network = IPv4Network("192.168.1.0/24")
    assert _to_json_serializable(ipv4_network) == "192.168.1.0/24"

    # Test IPv6Interface
    ipv6_interface = IPv6Interface("::1/128")
    assert _to_json_serializable(ipv6_interface) == "::1/128"

    # Test IPv6Network
    ipv6_network = IPv6Network("::1/128")
    assert _to_json_serializable(ipv6_network) == "::1/128"

    # Test PurePath
    path = PurePath("/tmp/test.txt")
    assert _to_json_serializable(path) == "/tmp/test.txt"

    # Test UUID
    uuid_obj = UUID("12345678-1234-5678-9abc-123456789abc")
    assert _to_json_serializable(uuid_obj) == "12345678-1234-5678-9abc-123456789abc"


def test_jsonable_encoder_registered_encoder_check():
    """Test jsonable_encoder with registered encoder check - covers line 314."""
    from lilypad._utils.json import jsonable_encoder
    from collections.abc import Mapping

    class CustomMapping(Mapping):
        """Custom mapping that triggers the registered encoder check."""

        def __init__(self, data):
            self._data = data

        def __getitem__(self, key):
            return self._data[key]

        def __iter__(self):
            return iter(self._data)

        def __len__(self):
            return len(self._data)

    mapping = CustomMapping({"key": "value", "num": 123})
    result = jsonable_encoder(mapping)
    assert result == {"key": "value", "num": 123}


def test_jsonable_encoder_object_without_dict_fallback():
    """Test jsonable_encoder fallback to vars() - covers line 334."""

    class ObjectWithoutDict:
        """Object that has __dict__ but vars() will work."""

        def __init__(self):
            self.name = "test"
            self.value = 42

        def __getattribute__(self, name):
            # Simulate issues with direct dict access while keeping __dict__
            if name == "__dict__":
                # Return dict but simulate earlier conversion attempt failed
                return {"name": "test", "value": 42}
            return super().__getattribute__(name)

    obj = ObjectWithoutDict()
    result = jsonable_encoder(obj)
    assert result == {"name": "test", "value": 42}


def test_jsonable_encoder_custom_encoder_mismatch():
    """Test jsonable_encoder with custom encoder that doesn't match type - covers line 314."""

    class CustomType:
        def __init__(self, value):
            self.value = value
            self.name = "custom"

    # Test with encoder for wrong type (str instead of CustomType)
    # This test is checking that line 314 is covered, which happens when
    # an object matches a class in encoders_by_class_tuples

    # Use a type that's in ENCODERS_BY_TYPE to trigger the path
    from collections import deque

    # Create a custom encoder that will be checked but not used
    result = jsonable_encoder(
        deque([1, 2, 3]),
        custom_encoder={str: lambda x: "wrong_type"},  # Wrong type mapping
    )
    # deque should be converted to list by the default encoder
    assert result == [1, 2, 3]


def test_jsonable_encoder_line_314_coverage():
    """Test to ensure line 314 in jsonable_encoder is covered."""
    import lilypad._utils.json as json_module
    from unittest.mock import patch

    # Create a custom type not in ENCODERS_BY_TYPE
    class CustomType:
        def __init__(self, value):
            self.value = value

    # Create a custom encoder
    def custom_encoder(obj):
        return f"encoded_{obj.value}"

    # Temporarily patch ENCODERS_BY_TYPE to ensure our type isn't there
    original_encoders = json_module.ENCODERS_BY_TYPE.copy()

    # Remove the type if it exists (it shouldn't)
    if CustomType in json_module.ENCODERS_BY_TYPE:
        del json_module.ENCODERS_BY_TYPE[CustomType]

    # Create custom encoders_by_class_tuples that includes our type
    custom_encoders_by_class_tuples = {custom_encoder: (CustomType,)}

    # Patch encoders_by_class_tuples
    with patch.object(json_module, "encoders_by_class_tuples", custom_encoders_by_class_tuples):
        obj = CustomType("test")
        result = json_module.jsonable_encoder(obj)
        assert result == "encoded_test"

    # Restore original
    json_module.ENCODERS_BY_TYPE.clear()
    json_module.ENCODERS_BY_TYPE.update(original_encoders)


def test_jsonable_encoder_fallback_to_vars_with_exception():
    """Test jsonable_encoder fallback to vars() after exception - covers line 334."""

    class ProblematicObject:
        def __init__(self):
            self.value = "test"
            self.number = 42

        def __iter__(self):
            # This will cause the first dict(obj) attempt to fail
            raise RuntimeError("Cannot iterate")

        # But has __dict__ so vars() will work

    obj = ProblematicObject()
    result = jsonable_encoder(obj)
    assert result == {"value": "test", "number": 42}
