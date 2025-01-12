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
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("generations_hash_idx", table_name="generations")
    op.create_index(op.f("generations_hash_idx"), "generations", ["hash"], unique=False)
    op.create_unique_constraint(
        "unique_project_generation_hash", "generations", ["project_uuid", "hash"]
    )
    op.drop_constraint("projects_name_key", "projects", type_="unique")
    op.create_unique_constraint(
        "unique_project_name", "projects", ["organization_uuid", "name"]
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("unique_project_name", "projects", type_="unique")
    op.create_unique_constraint("projects_name_key", "projects", ["name"])
    op.drop_constraint("unique_project_generation_hash", "generations", type_="unique")
    op.drop_index(op.f("generations_hash_idx"), table_name="generations")
    op.create_index("generations_hash_idx", "generations", ["hash"], unique=True)
    # ### end Alembic commands ###
