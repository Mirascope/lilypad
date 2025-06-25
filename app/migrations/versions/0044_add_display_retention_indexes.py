"""add display retention indexes for spans

Revision ID: 0045
Revises: 0044
Create Date: 2025-01-25 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0044"
down_revision = "0043"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_spans_created_at_root",
        "spans",
        ["created_at"],
        postgresql_where=sa.text("parent_span_id IS NULL"),
        postgresql_using="btree",
    )

    op.create_index(
        "idx_spans_org_project_created",
        "spans",
        ["project_uuid", "created_at"],
        postgresql_where=sa.text("parent_span_id IS NULL"),
        postgresql_using="btree",
    )


def downgrade() -> None:
    # Drop the indexes
    op.drop_index("idx_spans_org_project_created", table_name="spans")
    op.drop_index("idx_spans_created_at_root", table_name="spans")
