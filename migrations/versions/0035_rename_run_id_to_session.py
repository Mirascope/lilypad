"""rename run id to session

Revision ID: 0035
Revises: 0034
Create Date: 2025-04-28 10:19:29.001406

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlmodel.sql.sqltypes import AutoString

# revision identifiers, used by Alembic.
revision: str = "0035"
down_revision: str | None = "0034"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("spans", schema=None) as batch_op:
        batch_op.add_column(sa.Column("session_id", AutoString(), nullable=True))
        batch_op.drop_index("spans_run_id_idx")
        batch_op.create_index(
            batch_op.f("spans_session_id_idx"), ["session_id"], unique=False
        )
        batch_op.drop_column("run_id")

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("spans", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("run_id", sa.VARCHAR(), autoincrement=False, nullable=True)
        )
        batch_op.drop_index(batch_op.f("spans_session_id_idx"))
        batch_op.create_index("spans_run_id_idx", ["run_id"], unique=False)
        batch_op.drop_column("session_id")

    # ### end Alembic commands ###
