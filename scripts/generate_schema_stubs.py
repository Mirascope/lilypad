#!/usr/bin/env python3
"""Script to generate model stubs for new entities."""

import os
from pathlib import Path
from string import Template

import typer

app = typer.Typer()

# Templates for each file
SERVICE_TEMPLATE = Template('''"""The `${EntityService}` class for ${entity_plural}."""

from ..models.${entity_plural} import ${Entity}Table
from ..schemas.${entity_plural} import ${Entity}Create
from .base_organization import BaseOrganizationService


class ${Entity}Service(BaseOrganizationService[${Entity}Table, ${Entity}Create]):
    """The service class for ${entity_plural}."""

    table: type[${Entity}Table] = ${Entity}Table
    create_model: type[${Entity}Create] = ${Entity}Create
''')

SCHEMA_TEMPLATE = Template('''"""${Entity_plural} schemas."""

from datetime import datetime
from uuid import UUID

from ..models.${entity_plural} import _${Entity}Base


class ${Entity}Create(_${Entity}Base):
    """${Entity} Create Model."""

    ...


class ${Entity}Public(_${Entity}Base):
    """${Entity} Public Model."""

    uuid: UUID
    created_at: datetime
    
    # Add specific fields for the public model
    # Example: functions: list[FunctionPublic] = []
''')

MODEL_TEMPLATE = Template('''"""${Entity_plural} models."""

from sqlmodel import SQLModel

from .base_organization_sql_model import BaseOrganizationSQLModel
from .table_names import ${ENTITY_UPPER}_TABLE_NAME

class _${Entity}Base(SQLModel):
    """Base ${Entity} Model."""

    # Define your fields here
    # Example: name: str = Field(nullable=False)


class ${Entity}Table(_${Entity}Base, BaseOrganizationSQLModel, table=True):
    """${Entity} Table Model."""

    __tablename__ = ${ENTITY_UPPER}_TABLE_NAME  # type: ignore
    
    # Define your relationships here
    # Example:
    # organization: "OrganizationTable" = Relationship(back_populates="${entity_plural}")
''')

TABLE_NAMES_APPEND = Template('''${ENTITY_UPPER}_TABLE_NAME = "${entity_plural}"''')

SERVICE_INIT_APPEND = Template("""from .${entity_plural} import ${Entity}Service""")

SERVICE_ALL_APPEND = Template(""""${Entity}Service",""")

MODEL_INIT_APPEND = Template("""from .${entity_plural} import ${Entity}Table""")

MODEL_ALL_APPEND = Template(""""${Entity}Table",""")


@app.command()
def generate(name: str):
    """Generate model stubs for a new entity."""
    # Convert name to different formats
    entity = name.lower()
    entity_plural = f"{entity}s"
    Entity = entity.capitalize()
    Entity_plural = entity_plural.capitalize()
    ENTITY_UPPER = entity.upper()

    # Create directories if they don't exist
    app_server_dir = Path("lilypad/server")
    services_dir = app_server_dir / "services"
    schemas_dir = app_server_dir / "schemas"
    models_dir = app_server_dir / "models"

    for directory in [services_dir, schemas_dir, models_dir]:
        if not directory.exists():
            print(f"Creating directory: {directory}")
            directory.mkdir(parents=True, exist_ok=True)

    # Generate service file
    service_file = services_dir / f"{entity_plural}.py"
    if not service_file.exists():
        print(f"Generating service file: {service_file}")
        with open(service_file, "w") as f:
            f.write(
                SERVICE_TEMPLATE.substitute(
                    Entity=Entity,
                    EntityService=f"{Entity}Service",
                    entity_plural=entity_plural,
                )
            )
    else:
        print(f"Service file already exists: {service_file}")

    # Generate schema file
    schema_file = schemas_dir / f"{entity_plural}.py"
    if not schema_file.exists():
        print(f"Generating schema file: {schema_file}")
        with open(schema_file, "w") as f:
            f.write(
                SCHEMA_TEMPLATE.substitute(
                    Entity=Entity,
                    Entity_plural=Entity_plural,
                    entity_plural=entity_plural,
                )
            )
    else:
        print(f"Schema file already exists: {schema_file}")

    # Generate model file
    model_file = models_dir / f"{entity_plural}.py"
    if not model_file.exists():
        print(f"Generating model file: {model_file}")
        with open(model_file, "w") as f:
            f.write(
                MODEL_TEMPLATE.substitute(
                    Entity=Entity,
                    Entity_plural=Entity_plural,
                    entity_plural=entity_plural,
                    entity=entity,
                    ENTITY_UPPER=ENTITY_UPPER,
                )
            )
    else:
        print(f"Model file already exists: {model_file}")

    # Update table_names.py
    table_names_file = models_dir / "table_names.py"
    if table_names_file.exists():
        print(f"Appending to table_names.py")
        # Check if the table name already exists
        with open(table_names_file, "r") as f:
            content = f.read()

        table_name_line = f'{ENTITY_UPPER}_TABLE_NAME = "{entity_plural}"'
        if table_name_line not in content:
            with open(table_names_file, "a") as f:
                f.write(
                    "\n"
                    + TABLE_NAMES_APPEND.substitute(
                        ENTITY_UPPER=ENTITY_UPPER, entity_plural=entity_plural
                    )
                )
        else:
            print(
                f"Table name {ENTITY_UPPER}_TABLE_NAME already exists in table_names.py"
            )
    else:
        print(f"Creating table_names.py")
        with open(table_names_file, "w") as f:
            f.write('"""Table names for the database models."""\n\n')
            f.write(
                TABLE_NAMES_APPEND.substitute(
                    ENTITY_UPPER=ENTITY_UPPER, entity_plural=entity_plural
                )
            )

    # Update services/__init__.py
    services_init_file = services_dir / "__init__.py"
    service_import_line = SERVICE_INIT_APPEND.substitute(
        entity_plural=entity_plural, Entity=Entity
    )
    service_all_line = SERVICE_ALL_APPEND.substitute(Entity=Entity)

    if services_init_file.exists():
        print(f"Updating services/__init__.py")
        with open(services_init_file, "r") as f:
            content = f.read()

        # Add import if not exists
        if service_import_line not in content:
            # Find the last import line
            lines = content.split("\n")
            import_lines = [
                i for i, line in enumerate(lines) if line.startswith("from .")
            ]
            if import_lines:
                last_import_line = max(import_lines)
                lines.insert(last_import_line + 1, service_import_line)
            else:
                # No imports yet, add at the beginning
                lines.insert(0, service_import_line)

            # Find __all__ and add the new service
            all_line_index = next(
                (i for i, line in enumerate(lines) if line.startswith("__all__")), None
            )
            if all_line_index is not None:
                # Find the closing bracket
                closing_bracket_index = next(
                    (
                        i
                        for i, line in enumerate(lines[all_line_index:], all_line_index)
                        if "]" in line
                    ),
                    None,
                )
                if closing_bracket_index is not None:
                    # Add the new service before the closing bracket
                    lines[closing_bracket_index] = lines[closing_bracket_index].replace(
                        "]", f"    {service_all_line}\n]"
                    )

            with open(services_init_file, "w") as f:
                f.write("\n".join(lines))
    else:
        print(f"Creating services/__init__.py")
        with open(services_init_file, "w") as f:
            f.write(f"{service_import_line}\n\n")
            f.write(f"__all__ = [\n    {service_all_line}\n]\n")

    # Update models/__init__.py
    models_init_file = models_dir / "__init__.py"
    model_import_line = MODEL_INIT_APPEND.substitute(
        entity_plural=entity_plural, Entity=Entity
    )
    model_all_line = MODEL_ALL_APPEND.substitute(Entity=Entity)

    if models_init_file.exists():
        print(f"Updating models/__init__.py")
        with open(models_init_file, "r") as f:
            content = f.read()

        # Add import if not exists
        if model_import_line not in content:
            # Find the last import line
            lines = content.split("\n")
            import_lines = [
                i for i, line in enumerate(lines) if line.startswith("from .")
            ]
            if import_lines:
                last_import_line = max(import_lines)
                lines.insert(last_import_line + 1, model_import_line)
            else:
                # No imports yet, add at the beginning
                lines.insert(0, model_import_line)

            # Find __all__ and add the new model
            all_line_index = next(
                (i for i, line in enumerate(lines) if line.startswith("__all__")), None
            )
            if all_line_index is not None:
                # Find the closing bracket
                closing_bracket_index = next(
                    (
                        i
                        for i, line in enumerate(lines[all_line_index:], all_line_index)
                        if "]" in line
                    ),
                    None,
                )
                if closing_bracket_index is not None:
                    # Add the new model before the closing bracket
                    lines[closing_bracket_index] = lines[closing_bracket_index].replace(
                        "]", f"    {model_all_line}\n]"
                    )

            with open(models_init_file, "w") as f:
                f.write("\n".join(lines))
    else:
        print(f"Creating models/__init__.py")
        with open(models_init_file, "w") as f:
            f.write(f"{model_import_line}\n\n")
            f.write(f"__all__ = [\n    {model_all_line}\n]\n")

    print(f"Successfully generated stubs for entity: {name}")


if __name__ == "__main__":
    app()
