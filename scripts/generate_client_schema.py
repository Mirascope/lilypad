"""Generate the client schemas for the server."""

import json
from pathlib import Path

from datamodel_code_generator import (
    DataModelType,
    InputFileType,
    PythonVersion,
    generate,
)

PROJECT_ROOT = Path(__file__).parent.parent
CLIENT_SCHEMAS_DIR = PROJECT_ROOT / "lilypad/server/client/schemas"

FILE_HEADER = '"""The Schema models for the Lilypad {name} API."""'


def generate_client_schema(input_: str, output: Path) -> None:
    """Generate the client schema."""
    generate(
        input_=input_,
        output=output,
        input_file_type=InputFileType.OpenAPI,
        output_model_type=DataModelType.PydanticV2BaseModel,
        target_python_version=PythonVersion.PY_310,
        use_standard_collections=True,
        use_schema_description=True,
        use_field_description=True,
        use_union_operator=True,
        reuse_model=True,
        field_constraints=True,
        set_default_enum_member=True,
        custom_file_header=FILE_HEADER.format(name=output.stem),
        use_subclass_enum=True,
        capitalise_enum_members=True,
    )


def main() -> None:
    """Generate the client schemas."""
    from lilypad.ee.server.api.v0 import ee_api as ee_v0
    from lilypad.server.api.v0 import api as v0

    v0_openapi = json.dumps(v0.openapi())
    generate_client_schema(v0_openapi, CLIENT_SCHEMAS_DIR / "v0.py")

    ee_v0_openapi = json.dumps(ee_v0.openapi())
    generate_client_schema(ee_v0_openapi, CLIENT_SCHEMAS_DIR / "ee_v0.py")


if __name__ == "__main__":
    main()
