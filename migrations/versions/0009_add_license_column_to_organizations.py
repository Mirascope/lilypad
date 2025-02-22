"""add_license_column_to_organizations

Revision ID: 0009
Revises: 0008
Create Date: 2025-02-06 16:13:13.394158

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlmodel.sql.sqltypes import AutoString

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add license column to organizations table
    with op.batch_alter_table("organizations", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "license",
                AutoString(),
                nullable=True,
                comment="License key for the organization. NULL means FREE tier",
            )
        )
        # Add an index for faster license lookups and ensure uniqueness
        batch_op.create_index(
            "ix_organizations_license",
            ["license"],
            unique=True,
            postgresql_where=sa.text("license IS NOT NULL"),
        )


def downgrade() -> None:
    # Remove license column from organizations table
    with op.batch_alter_table("organizations", schema=None) as batch_op:
        batch_op.drop_index("ix_organizations_license")
        batch_op.drop_column("license")
