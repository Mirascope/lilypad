"""Tests for the stubs command."""

from pathlib import Path
from typing import Any

import pytest

from lilypad.cli.commands.stubs import (
    _generate_protocol_stub_content,
    _merge_parameters,
    _normalize_signature,
    _parse_parameters_from_signature,
    _parse_return_type,
    stubs_command,
)

SIMPLE_SIG = """
import lilypad

@lilypad.generation()
def my_func(a: int, b: str = "default") -> bool: ...
"""

ASYNC_SIG = """
import lilypad

@lilypad.generation()
async def my_async_func(x: float, y: float = 3.14) -> str: ...
"""

ARG_TYPES_DICT = {"a": "int", "b": "str"}


@pytest.fixture
def normalized_simple_sig():
    """Return the normalized signature."""
    return _normalize_signature(SIMPLE_SIG)


def test_normalize_signature(normalized_simple_sig: str):
    """Test the _normalize_signature function."""
    assert "pass" in normalized_simple_sig
    assert "@" not in normalized_simple_sig


def test_parse_parameters_from_signature():
    """Test the _parse_parameters_from_signature function."""
    params = _parse_parameters_from_signature(SIMPLE_SIG)
    assert "a: int" in params
    assert any("b:" in p and "default" in p for p in params)


def test_merge_parameters():
    """Test the _merge_parameters function."""
    merged = _merge_parameters(SIMPLE_SIG, ARG_TYPES_DICT)
    assert any(p.startswith("a: int") for p in merged)
    assert any(p.startswith("b: str") for p in merged)


def test_parse_return_type():
    """Test the _parse_return_type function."""
    ret_type = _parse_return_type(SIMPLE_SIG)
    assert ret_type == "bool"


def test_generate_protocol_stub_content():
    """Test the _generate_protocol_stub_content function."""

    class DummyVersion:
        def __init__(self, version_num: int, signature: str, arg_types: dict):
            self.version_num = version_num
            self.signature = signature
            self.arg_types = arg_types

    versions = [
        DummyVersion(1, SIMPLE_SIG, {"a": "int", "b": "str"}),
        DummyVersion(2, SIMPLE_SIG, {"a": "int", "b": "str"}),
    ]
    stub_content = _generate_protocol_stub_content("my_func", versions, is_async=False)  # pyright: ignore [reportArgumentType]
    assert "class MyFuncVersion1(Protocol):" in stub_content
    assert "class MyFunc(Protocol):" in stub_content
    assert (
        "def version(cls, forced_version: Literal[1], override_sandbox_factory: SandBoxFactory[SandboxRunnerT] | None = None) -> MyFuncVersion1: ..."
        in stub_content
    )


def dummy_get_decorated_functions(decorator_name: str, dummy_file_path: str):
    """Dummy get_decorated_functions function"""
    return {"lilypad.generation": [(dummy_file_path, "my_func", 1, "pkg.dummy")]}


class DummyClient:
    """Dummy LilypadClient class"""

    def __init__(self, token: Any) -> None:
        pass

    def get_generations_by_name(self, fn):
        """Dummy get_generations_by_name method"""

        class DummyVersion:
            def __init__(self, version_num: int, signature: str, arg_types: dict):
                self.version_num = version_num
                self.signature = signature
                self.arg_types = arg_types

        return [
            DummyVersion(1, SIMPLE_SIG, {"a": "int", "b": "str"}),
            DummyVersion(2, SIMPLE_SIG, {"a": "int", "b": "str"}),
        ]


@pytest.fixture(autouse=True)
def override_dependencies(monkeypatch, tmp_path: Path):
    """Override dependencies for the stubs command."""
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir(exist_ok=True)
    dummy_file = (pkg_dir / "dummy.py").resolve()
    monkeypatch.setattr(
        "lilypad.cli.commands.stubs.get_decorated_functions",
        lambda decorator_name: dummy_get_decorated_functions(
            decorator_name, str(dummy_file)
        ),
    )
    from lilypad.cli.commands.stubs import LilypadClient

    monkeypatch.setattr(
        LilypadClient,
        "get_generations_by_name",
        lambda self, fn: DummyClient("").get_generations_by_name(fn),
    )


def test_stubs_command(tmp_path: Path) -> None:
    """Test the stubs command."""
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir(exist_ok=True)
    (pkg_dir / "__init__.py").write_text("")
    dummy_file = pkg_dir / "dummy.py"
    dummy_file.write_text(SIMPLE_SIG)
    stubs_command(directory=pkg_dir, exclude=[], debug=False)
    stub_file = pkg_dir / "dummy.pyi"
    assert stub_file.exists()
    output = stub_file.read_text()
    assert "class MyFunc(Protocol):" in output
