"""user organization

Revision ID: 0007
Revises: 0006
Create Date: 2025-01-29 21:52:49.297062

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from alembic_postgresql_enum import TableReference
from sqlmodel.sql.sqltypes import AutoString

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "organization_invites",
        sa.Column("uuid", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("organization_uuid", sa.Uuid(), nullable=False),
        sa.Column("invited_by", sa.Uuid(), nullable=False),
        sa.Column("email", AutoString(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("token", AutoString(), nullable=False),
        sa.Column("resend_email_id", AutoString(), nullable=False),
        sa.ForeignKeyConstraint(
            ["invited_by"],
            ["users.uuid"],
            name=op.f("organization_invites_invited_by_users_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organization_uuid"],
            ["organizations.uuid"],
            name=op.f("organization_invites_organization_uuid_organizations_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("uuid", name=op.f("organization_invites_pkey")),
        sa.UniqueConstraint("token", name=op.f("organization_invites_token_key")),
    )
    with op.batch_alter_table("organization_invites", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("organization_invites_invited_by_idx"),
            ["invited_by"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("organization_invites_organization_uuid_idx"),
            ["organization_uuid"],
            unique=False,
        )

    op.sync_enum_values(  # type: ignore[attr-defined]
        enum_schema="public",
        enum_name="userrole",
        new_values=["OWNER", "ADMIN", "MEMBER"],
        affected_columns=[
            TableReference(
                table_schema="public",
                table_name="user_organizations",
                column_name="role",
            )
        ],
        enum_values_to_rename=[],
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.sync_enum_values(  # type: ignore[attr-defined]
        enum_schema="public",
        enum_name="userrole",
        new_values=["ADMIN", "MEMBER"],
        affected_columns=[
            TableReference(
                table_schema="public",
                table_name="user_organizations",
                column_name="role",
            )
        ],
        enum_values_to_rename=[],
    )
    with op.batch_alter_table("organization_invites", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("organization_invites_organization_uuid_idx"))
        batch_op.drop_index(batch_op.f("organization_invites_invited_by_idx"))

    op.drop_table("organization_invites")
    # ### end Alembic commands ###
