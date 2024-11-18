import textwrap

from lilypad._utils.closure import format_code


def construct_function(
    arg_types: dict[str, str], function_name: str, configure: bool = False
) -> str:
    arg_list = [f"{arg_name}: {arg_type}" for arg_name, arg_type in arg_types.items()]

    configure_line = "lilypad.configure()\n" if configure else ""
    func_def = f"""
    {configure_line}

    @lilypad.prompt()
    def {function_name}({', '.join(arg_list)}) -> str: ...
    """
    source = textwrap.dedent(func_def)
    code = format_code(source)
    return code
