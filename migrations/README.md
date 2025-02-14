# Alembic Migrations

## How to make a migration?

alembic revision --autogenerate -m "{YOUR_MESSAGE_HERE}"

## How to apply a migration?

alembic upgrade `target-revision` \
Ex: alembic upgrade head

> target-revision Can be a number (positive), `head`, or relative (ae10+2) where ae10 is a hash

## How to fake a migration?

alembic stamp `target-revision` \
Ex: alembic stamp head

> target-revision will be same as upgrade

## How to revert a migration?

alembic downgrade `target-revision` \
Ex: alembic downgrade -1

> target-revision Can be a number (negative), `base`, or relative (head-2)

## How does alembic keep track of migrations?

Alembic creates a table called `alembic_version`. Calling upgrade writes to the `alembic_version` table, and calling downgrade delete from the table
