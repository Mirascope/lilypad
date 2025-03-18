"""Migration script to move existing plain text keys to secure storage."""

import argparse
import asyncio

# Setup migration logger
import logging

from sqlmodel import select, text

from lilypad.server._utils.audit_logger import AuditAction, AuditLogger
from lilypad.server.db.session import get_session
from lilypad.server.models import UserTable
from lilypad.server.secret_manager.secret_manager_factory import get_secret_manager

migration_logger = logging.getLogger("secrets.migration")
handler = logging.FileHandler("secret_migration.log")
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
migration_logger.addHandler(handler)
migration_logger.setLevel(logging.INFO)


async def migrate_keys(dry_run: bool = False) -> None:
    """Migrate all existing plain text keys to secure storage."""
    migration_logger.info("Starting migration of plain text keys to secure storage...")

    session = next(get_session())
    try:
        # Disable statement logging for security
        if not dry_run:
            session.execute(text("ALTER SYSTEM SET statement_log = 'none'"))
            session.commit()
            migration_logger.info("Disabled system-wide statement logging for security")

        # Get all users
        users = session.exec(select(UserTable)).all()
        migration_logger.info(f"Found {len(users)} users to process")

        # Create services
        secret_manager = get_secret_manager(session)
        audit_logger = AuditLogger(session)

        migrated_count = 0
        failed_count = 0
        verification_map = {}

        for user in users:
            if not user.keys:
                continue

            user_id = str(user.uuid)
            migration_logger.info(
                f"Processing user {user.email} with {len(user.keys)} keys"
            )

            new_keys = {}
            original_keys = {}

            for service_name, api_key in user.keys.items():
                if not api_key:  # Skip empty keys
                    continue

                original_keys[service_name] = api_key

                org_id = (
                    str(user.active_organization_uuid)
                    if user.active_organization_uuid
                    else "personal"
                )
                name = f"user_{user_id}_org_{org_id}_{service_name}_key"
                description = f"API key for {service_name} for user {user.email}"

                try:
                    if not dry_run:
                        secret_id = secret_manager.store_secret(
                            name, api_key, description
                        )
                        new_keys[service_name] = secret_id
                        verification_map[secret_id] = api_key

                        masked_key = (
                            api_key[:4] + "*" * (len(api_key) - 4)
                            if len(api_key) > 4
                            else "****"
                        )
                        migration_logger.info(
                            f"  Migrated key for {service_name}: {masked_key} -> {secret_id}"
                        )

                        audit_logger.log_secret_access(
                            user_id=user_id,
                            action=AuditAction.CREATE,
                            service_name=service_name,
                            secret_id=secret_id,
                            success=True,
                            additional_info={"operation": "migration"},
                        )
                    else:
                        masked_key = (
                            api_key[:4] + "*" * (len(api_key) - 4)
                            if len(api_key) > 4
                            else "****"
                        )
                        migration_logger.info(
                            f"  [DRY RUN] Would migrate key for {service_name}: {masked_key}"
                        )
                except Exception as e:
                    migration_logger.error(
                        f"  Error migrating key for {service_name}: {str(e)}"
                    )
                    failed_count += 1

            if not dry_run and new_keys:
                verified = True
                for service_name, secret_id in new_keys.items():
                    try:
                        retrieved_secret = secret_manager.get_secret(secret_id)
                        original_key = original_keys[service_name]

                        if retrieved_secret != original_key:
                            migration_logger.error(
                                f"  Verification failed for {service_name}: retrieved key doesn't match original"
                            )
                            verified = False
                            break
                    except Exception as e:
                        migration_logger.error(
                            f"  Verification failed for {service_name}: {str(e)}"
                        )
                        verified = False
                        break

                if verified:
                    user.keys = new_keys
                    session.add(user)
                    session.commit()
                    session.refresh(user)
                    migrated_count += 1
                    migration_logger.info(
                        f"  Successfully updated user {user.email} with {len(new_keys)} secure keys"
                    )
                else:
                    migration_logger.error(
                        f"  Failed to update user {user.email} due to verification failures"
                    )
                    failed_count += 1

        migration_logger.info(
            f"Migration complete. Migrated keys for {migrated_count} users. Failed: {failed_count}"
        )

    except Exception as e:
        migration_error = f"Error during migration: {str(e)}"
        migration_logger.error(migration_error)
        if not dry_run:
            session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Migrate plain text keys to secure storage"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without modifying data",
    )
    parser.add_argument(
        "--log-file", type=str, default="secret_migration.log", help="Log file path"
    )

    args = parser.parse_args()

    if args.log_file != "secret_migration.log":
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
