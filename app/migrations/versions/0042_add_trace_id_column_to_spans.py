"""Add trace_id column to spans table

Revision ID: 0042
Revises: 0041
Create Date: 2025-06-19 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0042"
down_revision: str | None = "0041"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("spans", sa.Column("trace_id", sa.String(), nullable=True))

    op.create_index("ix_spans_trace_id", "spans", ["trace_id"])
    op.create_index("ix_spans_trace_id_span_id", "spans", ["trace_id", "span_id"])
    op.create_index(
        "ix_spans_trace_id_parent_span_id", "spans", ["trace_id", "parent_span_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_spans_trace_id_parent_span_id", table_name="spans")
    op.drop_index("ix_spans_trace_id_span_id", table_name="spans")
    op.drop_index("ix_spans_trace_id", table_name="spans")

    # Drop column
    op.drop_column("spans", "trace_id")
