"""cascade delete

Revision ID: 0004
Revises: 0003
Create Date: 2025-01-15 17:37:52.341676

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("api_keys", schema=None) as batch_op:
        batch_op.drop_constraint("api_keys_user_uuid_users_fkey", type_="foreignkey")
        batch_op.drop_constraint(
            "api_keys_project_uuid_projects_fkey", type_="foreignkey"
        )
        batch_op.drop_constraint(
            "api_keys_organization_uuid_organizations_fkey", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            batch_op.f("api_keys_organization_uuid_organizations_fkey"),
            "organizations",
            ["organization_uuid"],
            ["uuid"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            batch_op.f("api_keys_user_uuid_users_fkey"),
            "users",
            ["user_uuid"],
            ["uuid"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            batch_op.f("api_keys_project_uuid_projects_fkey"),
            "projects",
            ["project_uuid"],
            ["uuid"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("generations", schema=None) as batch_op:
        batch_op.drop_constraint(
            "generations_organization_uuid_organizations_fkey", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            batch_op.f("generations_organization_uuid_organizations_fkey"),
            "organizations",
            ["organization_uuid"],
            ["uuid"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("projects", schema=None) as batch_op:
        batch_op.drop_constraint(
            "projects_organization_uuid_organizations_fkey", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            batch_op.f("projects_organization_uuid_organizations_fkey"),
            "organizations",
            ["organization_uuid"],
            ["uuid"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("prompts", schema=None) as batch_op:
        batch_op.drop_constraint(
            "prompts_organization_uuid_organizations_fkey", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            batch_op.f("prompts_organization_uuid_organizations_fkey"),
            "organizations",
            ["organization_uuid"],
            ["uuid"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("response_models", schema=None) as batch_op:
        batch_op.drop_constraint(
            "response_models_organization_uuid_organizations_fkey", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            batch_op.f("response_models_organization_uuid_organizations_fkey"),
            "organizations",
            ["organization_uuid"],
            ["uuid"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("spans", schema=None) as batch_op:
        batch_op.create_index(
            "idx_spans_project_parent_filtered",
            ["project_uuid"],
            unique=False,
            postgresql_where=sa.text("parent_span_id IS NULL"),
        )
        batch_op.create_index(
            batch_op.f("spans_parent_span_id_idx"), ["parent_span_id"], unique=False
        )
        batch_op.drop_constraint(
            "spans_organization_uuid_organizations_fkey", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            batch_op.f("spans_organization_uuid_organizations_fkey"),
            "organizations",
            ["organization_uuid"],
            ["uuid"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("user_organizations", schema=None) as batch_op:
        batch_op.drop_constraint(
            "user_organizations_organization_uuid_organizations_fkey",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "user_organizations_user_uuid_users_fkey", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            batch_op.f("user_organizations_user_uuid_users_fkey"),
            "users",
            ["user_uuid"],
            ["uuid"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            batch_op.f("user_organizations_organization_uuid_organizations_fkey"),
            "organizations",
            ["organization_uuid"],
            ["uuid"],
            ondelete="CASCADE",
        )

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("user_organizations", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("user_organizations_organization_uuid_organizations_fkey"),
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            batch_op.f("user_organizations_user_uuid_users_fkey"), type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "user_organizations_user_uuid_users_fkey", "users", ["user_uuid"], ["uuid"]
        )
        batch_op.create_foreign_key(
            "user_organizations_organization_uuid_organizations_fkey",
            "organizations",
            ["organization_uuid"],
            ["uuid"],
        )

    with op.batch_alter_table("spans", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("spans_organization_uuid_organizations_fkey"), type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "spans_organization_uuid_organizations_fkey",
            "organizations",
            ["organization_uuid"],
            ["uuid"],
        )
        batch_op.drop_index(batch_op.f("spans_parent_span_id_idx"))
        batch_op.drop_index(
            "idx_spans_project_parent_filtered",
            postgresql_where=sa.text("parent_span_id IS NULL"),
        )

    with op.batch_alter_table("response_models", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("response_models_organization_uuid_organizations_fkey"),
            type_="foreignkey",
        )
        batch_op.create_foreign_key(
            "response_models_organization_uuid_organizations_fkey",
            "organizations",
            ["organization_uuid"],
            ["uuid"],
        )

    with op.batch_alter_table("prompts", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("prompts_organization_uuid_organizations_fkey"),
            type_="foreignkey",
        )
        batch_op.create_foreign_key(
            "prompts_organization_uuid_organizations_fkey",
            "organizations",
            ["organization_uuid"],
            ["uuid"],
        )

    with op.batch_alter_table("projects", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("projects_organization_uuid_organizations_fkey"),
            type_="foreignkey",
        )
        batch_op.create_foreign_key(
            "projects_organization_uuid_organizations_fkey",
            "organizations",
            ["organization_uuid"],
            ["uuid"],
        )

    with op.batch_alter_table("generations", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("generations_organization_uuid_organizations_fkey"),
            type_="foreignkey",
        )
        batch_op.create_foreign_key(
            "generations_organization_uuid_organizations_fkey",
            "organizations",
            ["organization_uuid"],
            ["uuid"],
        )

    with op.batch_alter_table("api_keys", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("api_keys_project_uuid_projects_fkey"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("api_keys_user_uuid_users_fkey"), type_="foreignkey"
        )
        batch_op.drop_constraint(
            batch_op.f("api_keys_organization_uuid_organizations_fkey"),
            type_="foreignkey",
        )
        batch_op.create_foreign_key(
            "api_keys_organization_uuid_organizations_fkey",
            "organizations",
            ["organization_uuid"],
            ["uuid"],
        )
        batch_op.create_foreign_key(
            "api_keys_project_uuid_projects_fkey",
            "projects",
            ["project_uuid"],
            ["uuid"],
        )
        batch_op.create_foreign_key(
            "api_keys_user_uuid_users_fkey", "users", ["user_uuid"], ["uuid"]
        )

    # ### end Alembic commands ###
