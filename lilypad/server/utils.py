"""Utilities for the FastAPI server."""

import hashlib

from lilypad.models import CallArgsCreate
from lilypad.server.models import FnParamsTable


def calculate_fn_params_hash(call_args: FnParamsTable | CallArgsCreate) -> str:
    """Calculate the hash of the function parameters."""
    fn_params_str = (
        str(call_args.call_params)
        + str(call_args.prompt_template)
        + str(call_args.model)
        + str(call_args.provider)
    )
    return hashlib.sha256(fn_params_str.encode("utf-8")).hexdigest()
