"""Generate the client schemas for the server."""

import json
from pathlib import Path

from datamodel_code_generator import (
    DataModelType,
    Formatter,
    PythonVersion,
)
from datamodel_code_generator.model import DataModel, get_data_model_types
from datamodel_code_generator.parser.openapi import OpenAPIParser

PROJECT_ROOT = Path(__file__).parent.parent
CLIENT_SCHEMAS_DIR = PROJECT_ROOT / "lilypad/server/client/schemas"

FILE_HEADER = '"""The Schema models for the Lilypad {name} API."""'

OPENAPI_SCHEMAS_PATH = "#/components/schemas"


class CustomOpenAPIParser(OpenAPIParser):
    target_model_names: list[str] = []

    @classmethod
    def reference_path_collector(
        cls,
        collected_reference_path: list[str],
        path_to_model: dict[str, DataModel],
        model: DataModel,
        checked_models: set[str],
    ) -> None:
        """Collect the reference paths."""
        if model.path in checked_models:
            return None
        checked_models.add(model.path)
        if model.reference.path not in collected_reference_path:
            collected_reference_path.append(model.reference.path)
        model_reference_classes = model.reference_classes
        if not model_reference_classes:
            return None
        if not (model_reference_classes - set(collected_reference_path)):
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
        collected_reference_path = []
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
) -> None:
    """Generate the client schema."""
    if not target_model_names:
        return None
    # generate(
    #     input_=input_,
    #     output=output,
    #     input_file_type=InputFileType.OpenAPI,
    #     output_model_type=DataModelType.PydanticV2BaseModel,
    #     target_python_version=PythonVersion.PY_310,
    #     use_standard_collections=True,
    #     use_schema_description=True,
    #     use_field_description=True,
    #     use_union_operator=True,
    #     reuse_model=True,
    #     field_constraints=True,
    #     set_default_enum_member=True,
    #     custom_file_header=FILE_HEADER.format(name=output.stem),
    #     use_subclass_enum=True,
    #     capitalise_enum_members=True,
    #     formatters=[Formatter.RUFF_CHECK, Formatter.RUFF_FORMAT],
    # )

    target_python_version = PythonVersion.PY_310
    data_model_types = get_data_model_types(
        DataModelType.PydanticV2BaseModel, target_python_version
    )

    parser = CustomOpenAPIParser(
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
        formatters=[Formatter.RUFF_CHECK, Formatter.RUFF_FORMAT],
    )
    parser.target_model_names = target_model_names
    generated_models = parser.parse()
    custom_file_header = FILE_HEADER.format(name=output.stem)

    if not output.parent.exists():
        output.parent.mkdir(parents=True)
    with output.open("wt", encoding="utf-8") as file:
        file.write(custom_file_header)
        file.write("\n\n")
        file.write(generated_models)


def main() -> None:
    """Generate the client schemas."""
    from lilypad.ee.server.api.v0 import ee_api as ee_v0
    from lilypad.server.api.v0 import api as v0

    v0_openapi = json.dumps(v0.openapi())
    generate_client_schema(
        v0_openapi,
        CLIENT_SCHEMAS_DIR / "v0.py",
        ["GenerationPublic", "OrganizationPublic", "ProjectPublic", "SpanPublic"],
    )

    ee_v0_openapi = json.dumps(ee_v0.openapi())
    generate_client_schema(ee_v0_openapi, CLIENT_SCHEMAS_DIR / "ee_v0.py", [])


if __name__ == "__main__":
    main()
