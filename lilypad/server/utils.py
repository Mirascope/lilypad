"""Utilities for the FastAPI server."""

import hashlib

from lilypad.server.models.fn_params import FnParamsTable


def calculate_fn_params_hash(fn_params_table: FnParamsTable) -> str:
    """Calculate the hash of the function parameters."""
    fn_params_str = (
        str(fn_params_table.call_params)
        + str(fn_params_table.prompt_template)
        + str(fn_params_table.editor_state)
        + str(fn_params_table.model)
        + str(fn_params_table.provider)
    )
    return hashlib.sha256(fn_params_str.encode("utf-8")).hexdigest()
