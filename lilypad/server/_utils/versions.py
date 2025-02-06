from textwrap import dedent

from ..._utils.closure import _run_ruff


def construct_function(
    arg_types: dict[str, str], function_name: str, include_import: bool = False
) -> str:
    arg_list = [f"{arg_name}: {arg_type}" for arg_name, arg_type in arg_types.items()]

    import_line = "import lilypad" if include_import else ""
    func_def = f"""
    {import_line}
    @lilypad.prompt()
    def {function_name}({", ".join(arg_list)}): ...
    """
    return _run_ruff(dedent(func_def)).strip()
