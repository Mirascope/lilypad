"""make organization name unique

Revision ID: 0040
Revises: 0039
Create Date: 2025-06-05 08:36:47.917448

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import column, func, select, table

# revision identifiers, used by Alembic.
revision: str = "0040"
down_revision: str | None = "0039"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create a reference to the organizations table
    organizations = table(
        "organizations",
        column("uuid", UUID),
        column("name", sa.String),
        column("created_at", sa.DateTime(timezone=True)),
    )

    # Get a connection to execute queries
    connection = op.get_bind()

    # Find all duplicate names (names that appear more than once)
    duplicates_query = (
        select(organizations.c.name, func.count(organizations.c.name).label("count"))
        .group_by(organizations.c.name)
        .having(func.count(organizations.c.name) > 1)
    )

    duplicate_names = connection.execute(duplicates_query).fetchall()

    # For each duplicate name, update all but the first occurrence
    for name, _ in duplicate_names:
        # Get all organizations with this name, ordered by created_at (oldest first)
        orgs_with_name = connection.execute(
            select(organizations.c.uuid)
            .where(organizations.c.name == name)
            .order_by(organizations.c.created_at)
        ).fetchall()

        # Skip the first one (keep the oldest unchanged), update the rest
        for index, (org_uuid,) in enumerate(orgs_with_name[1:], start=1):
            new_name = f"{name}_{index}"

            # Keep incrementing if the new name already exists
            name_check = connection.execute(
                select(func.count(organizations.c.uuid)).where(
                    organizations.c.name == new_name
                )
            ).scalar()

            suffix = index
            while name_check is not None and name_check > 0:
                suffix += 1
                new_name = f"{name}_{suffix}"
                name_check = connection.execute(
                    select(func.count(organizations.c.uuid)).where(
                        organizations.c.name == new_name
                    )
                ).scalar()

            # Update the organization with the new unique name
            connection.execute(
                organizations.update()
                .where(organizations.c.uuid == org_uuid)
                .values(name=new_name)
            )

    # Now add the unique constraint
    with op.batch_alter_table("organizations", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            batch_op.f("organizations_name_key"), ["name"]
        )


def downgrade() -> None:
    # Remove the unique constraint
    with op.batch_alter_table("organizations", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("organizations_name_key"), type_="unique")
