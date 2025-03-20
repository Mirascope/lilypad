"""Migration script to move existing plain text keys to external secure storage using SecretManager."""

import argparse
import asyncio
import logging

from sqlmodel import select

from lilypad.server._utils.audit_logger import AuditAction, AuditLogger
from lilypad.server.db.session import get_session
from lilypad.server.models import UserTable
from lilypad.server.models.external_api_keys import ExternalAPIKeyTable
from lilypad.server.secret_manager.secret_manager_factory import get_secret_manager

migration_logger = logging.getLogger("external_api_keys.migration")
handler = logging.FileHandler("external_api_keys_migration.log")
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
migration_logger.addHandler(handler)
migration_logger.setLevel(logging.INFO)


async def migrate_keys(dry_run: bool = False) -> None:
    """Migrate all existing plain text keys to the new external API keys table using SecretManager."""
    migration_logger.info(
        "Starting migration of plain text keys to external secure storage..."
    )
    session = next(get_session())
    # Initialize the SecretManager instance for secret operations
    secret_manager = get_secret_manager(session)
    try:
        # Get all users
        users = session.exec(select(UserTable)).all()
        migration_logger.info(f"Found {len(users)} users to process")

        audit_logger = AuditLogger(session)
        migrated_count = 0
        failed_count = 0

        for user in users:
            # Skip if no keys exist in the old JSON column.
            if not user.keys:
                continue

            user_id = str(user.uuid)
            migration_logger.info(
                f"Processing user {user.email} with {len(user.keys)} keys"
            )
            migration_success = True  # Assume success unless a key fails

            for service_name, api_key in user.keys.items():
                if not api_key:  # Skip empty keys
                    continue

                description = (
                    f"External API key for {service_name} for user {user.email}"
                )
                masked_key = (
                    api_key[:4] + "*" * (len(api_key) - 4)
                    if len(api_key) > 4
                    else "****"
                )
                migration_logger.info(
                    f"Processing key for service {service_name}: original key {masked_key}"
                )
                try:
                    if not dry_run:
                        # Store the plain API key in SecretManager and obtain the secret_id
                        secret_id = secret_manager.store_secret(
                            service_name, api_key, description
                        )
                        # Create a new ExternalAPIKeyTable record with the secret_id
                        new_record = ExternalAPIKeyTable(
                            user_id=user.uuid,
                            service_name=service_name,
                            secret_id=secret_id,
                            description=description,
                        )
                        session.add(new_record)
                        session.commit()
                        session.refresh(new_record)

                        # Verification: Retrieve the stored secret via SecretManager
                        stmt = select(ExternalAPIKeyTable).where(
                            ExternalAPIKeyTable.id == new_record.id
                        )
                        retrieved = session.exec(stmt).first()
                        stored_api_key = (
                            secret_manager.get_secret(retrieved.secret_id)
                            if retrieved
                            else None
                        )
                        if retrieved is None or stored_api_key != api_key:
                            migration_logger.error(
                                f"Verification failed for {service_name}: retrieved key does not match original."
                            )
                            migration_success = False
                            failed_count += 1
                            break
                        else:
                            migration_logger.info(
                                f"Migrated key for {service_name}: {masked_key} -> ExternalAPIKey ID {new_record.id}"
                            )
                            audit_logger.log_secret_access(
                                user_id=user_id,
                                action=AuditAction.CREATE,
                                service_name=service_name,
                                secret_id=new_record.secret_id,
                                success=True,
                                additional_info={"operation": "migration"},
                            )
                    else:
                        migration_logger.info(
                            f"[DRY RUN] Would migrate key for {service_name}: {masked_key}"
                        )
                except Exception as e:
                    migration_logger.error(
                        f"Error migrating key for {service_name}: {str(e)}"
                    )
                    migration_success = False
                    failed_count += 1
                    break

            # If migration succeeded for this user, clear the old keys.
            if not dry_run and migration_success:
                user.keys = {}  # Clear the old JSON keys field
                session.add(user)
                session.commit()
                session.refresh(user)
                migrated_count += 1
                migration_logger.info(
                    f"Successfully updated user {user.email} with migrated external keys."
                )
            elif not migration_success:
                migration_logger.error(
                    f"Failed to update user {user.email} due to migration errors."
                )

        migration_logger.info(
            f"Migration complete. Migrated users: {migrated_count}. Failed: {failed_count}."
        )

    except Exception as e:
        migration_logger.error(f"Error during migration: {str(e)}")
        if not dry_run:
            session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Migrate plain text keys to external secure storage (ExternalAPIKeyTable) using SecretManager"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without modifying data",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="external_api_keys_migration.log",
        help="Log file path",
    )

    args = parser.parse_args()

    # Update logger file handler if necessary.
    if args.log_file != "external_api_keys_migration.log":
        for handler in migration_logger.handlers:
            if isinstance(handler, logging.FileHandler):
                migration_logger.removeHandler(handler)
        new_handler = logging.FileHandler(args.log_file)
        new_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        migration_logger.addHandler(new_handler)

    if args.dry_run:
        migration_logger.info("Starting DRY RUN migration")

    asyncio.run(migrate_keys(dry_run=args.dry_run))
