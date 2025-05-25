"""fix unique constraint

Revision ID: 0003
Revises: 0002
Create Date: 2025-01-09 10:30:27.633575

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Handle generations table changes
    with op.batch_alter_table("generations") as batch_op:
        batch_op.drop_index("generations_hash_idx")
        batch_op.create_index("generations_hash_idx", ["hash"])
        batch_op.create_unique_constraint(
            "unique_project_generation_hash", ["project_uuid", "hash"]
        )

    # Handle projects table changes
    with op.batch_alter_table("projects") as batch_op:
        batch_op.drop_constraint("projects_name_key", type_="unique")
        batch_op.create_unique_constraint(
            "unique_project_name", ["organization_uuid", "name"]
        )


def downgrade() -> None:
    # Handle projects table changes
    with op.batch_alter_table("projects") as batch_op:
        batch_op.drop_constraint("unique_project_name", type_="unique")
        batch_op.create_unique_constraint("projects_name_key", ["name"])

    # Handle generations table changes
    with op.batch_alter_table("generations") as batch_op:
        batch_op.drop_constraint("unique_project_generation_hash", type_="unique")
        batch_op.drop_index("generations_hash_idx")
        batch_op.create_index("generations_hash_idx", ["hash"], unique=True)
