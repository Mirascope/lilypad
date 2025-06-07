"""add span polling indexes

Revision ID: 0040
Revises: 0039
Create Date: 2025-06-03 10:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0040"
down_revision: str | None = "0039"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "idx_spans_project_created_at_parent",
        "spans",
        ["project_uuid", "created_at", "parent_span_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_spans_project_created_at_parent", table_name="spans")
