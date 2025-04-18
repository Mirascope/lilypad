"""cascade delete

Revision ID: 0033
Revises: 0032
Create Date: 2025-04-17 12:26:22.042858

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0033"
down_revision: str | None = "0032"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("user_consents", schema=None) as batch_op:
        batch_op.drop_constraint(
            "user_consents_user_uuid_users_fkey", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            batch_op.f("user_consents_user_uuid_users_fkey"),
            "users",
            ["user_uuid"],
            ["uuid"],
            ondelete="CASCADE",
        )

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("user_consents", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("user_consents_user_uuid_users_fkey"), type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "user_consents_user_uuid_users_fkey", "users", ["user_uuid"], ["uuid"]
        )

    # ### end Alembic commands ###
