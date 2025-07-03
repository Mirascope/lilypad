"""Add indexes for data retention

Revision ID: 0043
Revises: 0042
Create Date: 2025-06-24 11:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0043"
down_revision: str | None = "0042"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "idx_spans_org_created",
        "spans",
        ["organization_uuid", "created_at"],
        postgresql_using="btree",
    )

    op.create_index(
        "idx_comments_span_uuid",
        "comments",
        ["span_uuid"],
        postgresql_using="btree",
        if_not_exists=True,
    )

    op.create_index(
        "idx_annotations_span_uuid",
        "annotations",
        ["span_uuid"],
        postgresql_using="btree",
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("idx_annotations_span_uuid", table_name="annotations", if_exists=True)
    op.drop_index("idx_comments_span_uuid", table_name="comments", if_exists=True)
    op.drop_index("idx_spans_org_created", table_name="spans", if_exists=True)
