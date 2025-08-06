"""Test utilities for lilypad._internal.utils"""

from unittest.mock import patch

import orjson

from lilypad._internal.utils import json_dumps


def test_json_dumps_uses_correct_orjson_options() -> None:
    """Test that json_dumps uses the correct orjson options and returns a UTF-8 string."""
    test_data = {"key": "value", "number": 42}

    expected_options = (
        orjson.OPT_NON_STR_KEYS
        | orjson.OPT_NAIVE_UTC
        | orjson.OPT_SERIALIZE_NUMPY
        | orjson.OPT_SERIALIZE_DATACLASS
        | orjson.OPT_SERIALIZE_UUID
    )

    with patch("orjson.dumps") as mock_dumps:
        mock_dumps.return_value = b'{"key":"value","number":42}'

        result = json_dumps(test_data)

        mock_dumps.assert_called_once_with(test_data, option=expected_options)

        assert isinstance(result, str)
        assert result == '{"key":"value","number":42}'
