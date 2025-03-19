"""Secret manager implementation using Supabase Vault."""

from collections.abc import Generator
from contextlib import contextmanager

from sqlmodel import Session, text

from .secret_manager import SecretManager


class SupabaseVaultManager(SecretManager):
    """Secret manager implementation using Supabase Vault."""

    def __init__(self, session: Session) -> None:
        """Initialize with SQLModel session."""
        self.session = session

    @contextmanager
    def _transaction(self) -> Generator[Session, None, None]:
        """Context manager for transaction handling."""
        try:
            yield self.session
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def store_secret(
        self, name: str, secret: str, description: str | None = None
    ) -> str:
        """Store a secret in Supabase Vault."""
        with self._transaction():
            result = self.session.execute(
                text("SELECT vault.create_secret(:secret, :name, :description)"),
                {"secret": secret, "name": name, "description": description},
            )
            return result.scalar_one()

    def get_secret(self, secret_id: str) -> str | None:
        """Retrieve a secret from Supabase Vault."""
        # We need to get name of the secret
        name = self.get_secret_name_by_id(secret_id)
        if not name:
            return None
        with self._transaction():
            result = self.session.execute(
                text("SELECT decrypted_secret FROM vault.decrypted_secrets WHERE name = :name"),
                {"name": name},
            )
            return result.scalar_one()

    def update_secret(self, secret_id: str, secret: str) -> bool:
        """Update a secret in Supabase Vault."""
        with self._transaction():
            self.session.execute(
                text("SELECT vault.update_secret(:id, :secret)"),
                {"id": secret_id, "secret": secret},
            )
            return True

    def delete_secret(self, secret_id: str) -> bool:
        """Delete a secret from Supabase Vault."""
        with self._transaction():
            result = self.session.execute(
                text("DELETE FROM vault.secrets WHERE id = :id RETURNING id"),
                {"id": secret_id},
            )
            return result.scalar_one_or_none() is not None

    def get_secret_id_by_name(self, name: str) -> str | None:
        """Retrieve the secret id by name from Supabase Vault."""
        with self._transaction():
            result = self.session.execute(
                text("SELECT id FROM vault.secrets WHERE name = :name"), {"name": name}
            )
            return result.scalar_one_or_none()

    def get_secret_name_by_id(self, secret_id: str) -> str | None:
        """Retrieve the secret name by its id from Supabase Vault."""
        with self._transaction():
            result = self.session.execute(
                text("SELECT name FROM vault.secrets WHERE id = :id"),
                {"id": secret_id},
            )
            return result.scalar_one_or_none()
