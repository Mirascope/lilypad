"""Generate the client schemas for the server with CLI commands."""

import json
import sys
from enum import Enum
from pathlib import Path

import typer
from datamodel_code_generator import (
    DataModelType,
    PythonVersion,
)
from datamodel_code_generator.format import CodeFormatter, Formatter
from datamodel_code_generator.model import DataModel, get_data_model_types
from datamodel_code_generator.parser.openapi import OpenAPIParser

app = typer.Typer(help="Lilypad schema generator CLI", no_args_is_help=True)

PROJECT_ROOT = Path(__file__).parent.parent
CLIENT_DIR = PROJECT_ROOT / "lilypad/server/client"
CLIENT_SCHEMAS_DIR = CLIENT_DIR / "schemas"
CLIENT_SCHEMAS_INIT = CLIENT_SCHEMAS_DIR / "__init__.py"
CLIENT_INIT = CLIENT_DIR / "__init__.py"
SCHEMAS_FILE_HEADER = '"""The Schema models for the Lilypad {name} API."""'
CLIENT_INIT_FILE_HEADER = '"""Client module for Lilypad server."""'
SCHEMAS_INIT_FILE_HEADER = '"""The Schema models for the Lilypad API."""'

OPENAPI_SCHEMAS_PATH = "#/components/schemas"

FORMATTERS = [Formatter.RUFF_CHECK, Formatter.RUFF_FORMAT]

ENCODING = "utf-8"


V0_TARGET_MODELS = [
    "GenerationPublic",
    "OrganizationPublic",
    "ProjectPublic",
    "SpanPublic",
    "GenerationCreate",
    "LicenseInfo",
    "Provider",
]


class Endpoint(str, Enum):
    """Supported API endpoints."""

    V0 = "v0"


class LilypadOpenAPIParser(OpenAPIParser):
    """Lilypad OpenAPI parser."""

    target_model_names: list[str] = []

    @classmethod
    def reference_path_collector(
        cls,
        collected_reference_path: set[str],
        path_to_model: dict[str, DataModel],
        model: DataModel,
        checked_models: set[str],
    ) -> None:
        """Collect the reference paths."""
        if model.path in checked_models:
            return None
        checked_models.add(model.path)
        if model.reference.path not in collected_reference_path:
            collected_reference_path.add(model.reference.path)
        model_reference_classes = model.reference_classes
        if not model_reference_classes:
            return None
        if not (model_reference_classes - collected_reference_path):
            return None

        for reference_class in model_reference_classes:
            reference_model = path_to_model[reference_class]
            cls.reference_path_collector(
                collected_reference_path, path_to_model, reference_model, checked_models
            )

    def parse_raw(self) -> None:
        """Parse the raw data."""
        super().parse_raw()
        path_to_model = {model.reference.path: model for model in self.results}
        collected_reference_path = set()
        for target_model_name in self.target_model_names:
            model = path_to_model.get(f"{OPENAPI_SCHEMAS_PATH}/{target_model_name}")
            if not model:
                raise ValueError(f"Model not found: {target_model_name}")
            self.reference_path_collector(
                collected_reference_path, path_to_model, model, set()
            )

        # Create new filtered model list
        self.results = [
            model
            for model in self.results
            if model.reference.path in collected_reference_path
        ]


def generate_client_schema(
    input_: str, output: Path, target_model_names: list[str]
) -> list[str]:
    """Generate the client schema."""
    if not target_model_names:
        return []

    target_python_version = PythonVersion.PY_310
    data_model_types = get_data_model_types(
        DataModelType.PydanticV2BaseModel, target_python_version
    )

    parser = LilypadOpenAPIParser(
        source=input_,
        data_model_type=data_model_types.data_model,
        data_model_root_type=data_model_types.root_model,
        data_model_field_type=data_model_types.field_model,
        data_type_manager_type=data_model_types.data_type_manager,
        target_python_version=target_python_version,
        dump_resolve_reference_action=data_model_types.dump_resolve_reference_action,
        field_constraints=True,
        use_standard_collections=True,
        use_schema_description=True,
        use_field_description=True,
        reuse_model=True,
        set_default_enum_member=True,
        use_union_operator=True,
        capitalise_enum_members=True,
        keep_model_order=False,
        use_subclass_enum=True,
        use_annotated=True,
        formatters=FORMATTERS,
    )
    parser.target_model_names = target_model_names
    generated_models = parser.parse()
    custom_file_header = SCHEMAS_FILE_HEADER.format(name=output.stem)

    if not output.parent.exists():
        output.parent.mkdir(parents=True)
    with output.open("wt", encoding=ENCODING) as file:
        file.write(custom_file_header)
        file.write("\n\n")
        file.write(generated_models)
    return [model.name for model in parser.results]


def get_openapi_schema(endpoint: Endpoint) -> dict:
    """Get the OpenAPI schema for the specified endpoint."""
    if endpoint == Endpoint.V0:
        from lilypad.server.api.v0 import api as v0

        return v0.openapi()
    else:
        raise ValueError(f"Unsupported endpoint: {endpoint}")


@app.command()
def generate_python() -> None:
    """Generate the Python client schemas."""
    from lilypad.server.api.v0 import api as v0

    # Generate the client schemas for v0
    v0_generated_models = sorted(
        generate_client_schema(
            json.dumps(v0.openapi()),
            CLIENT_SCHEMAS_DIR / "v0.py",
            V0_TARGET_MODELS,
        )
    )

    # Prepare the imports for the schemas __init__.py
    imports = ""
    if v0_generated_models:
        imports += "from .v0 import {v0_target_models}\n".format(
            v0_target_models=", ".join(v0_generated_models)
        )

    code_formatter = CodeFormatter(
        python_version=PythonVersion.PY_310,
        formatters=FORMATTERS,
        settings_path=PROJECT_ROOT,
        encoding=ENCODING,
    )

    # Generate the schemas __init__.py
    schema_exports = ", ".join(f'"{name}"' for name in sorted(v0_generated_models))
    schemas_init = (
        f"{SCHEMAS_INIT_FILE_HEADER}\n{imports}\n__all__ = [{schema_exports}]"
    )

    CLIENT_SCHEMAS_INIT.write_text(
        code_formatter.format_code(schemas_init), encoding=ENCODING
    )

    # Generate the client module __init__.py
    client_imports = "from .schemas import {target_models}\n".format(
        target_models=", ".join(v0_generated_models)
    )

    client_exports = ", ".join(
        f'"{name}"' for name in sorted(v0_generated_models + ["LilypadClient"])
    )
    client_init = f"{CLIENT_INIT_FILE_HEADER}\nfrom .lilypad_client import LilypadClient\n{client_imports}\n__all__ = [{client_exports}]"
    CLIENT_INIT.write_text(code_formatter.format_code(client_init), encoding=ENCODING)

    typer.echo(f"Generated Python client schemas: {len(v0_generated_models)} models")


@app.command()
def generate_openapi(
    endpoint: Endpoint = typer.Option(  #  noqa: B008
        default="v0", help="API endpoint to generate OpenAPI schema for"
    ),
    output: Path | None = typer.Option(  #  noqa: B008
        None, help="Output file path. If not specified, outputs to stdout for piping"
    ),
) -> None:
    """Generate the OpenAPI schema for the specified endpoint."""
    try:
        schema = get_openapi_schema(endpoint)
        output_json = json.dumps(schema, indent=2)

        if output:
            output.write_text(output_json, encoding=ENCODING)
            # Print status message to stderr so it doesn't interfere with piping
            typer.echo(f"OpenAPI schema for {endpoint} written to {output}", err=True)
        else:
            # Print JSON to stdout with no additional messages for clean piping
            sys.stdout.write(output_json)
    except ImportError as e:
        typer.echo(f"Error importing API module: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error generating OpenAPI schema: {e}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
