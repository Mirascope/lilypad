from lilypad.server._utils.versions import construct_function


def test_construct_function():
    """Test constructing function code"""
    arg_types = {
        "text": "str",
        "temperature": "float"
    }
    function_name = "test_function"

    code = construct_function(arg_types, function_name)
    assert "@lilypad.prompt()" in code
    assert "def test_function(text: str, temperature: float)" in code
    assert "-> str" in code

def test_construct_function_with_configure():
    """Test constructing function code with configure flag"""
    arg_types = {"text": "str"}
    function_name = "test_function"

    code = construct_function(arg_types, function_name, configure=True)
    assert "lilypad.configure()" in code
    assert "@lilypad.prompt()" in code
    assert "def test_function(text: str)" in code

def test_construct_function_no_args():
    """Test constructing function with no arguments"""
    code = construct_function({}, "test_function")
    assert "@lilypad.prompt()" in code
    assert "def test_function()" in code
    assert "-> str" in code