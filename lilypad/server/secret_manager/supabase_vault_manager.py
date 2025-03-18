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
        self._disable_statement_logging()

    @contextmanager
    def _transaction(self) -> Generator[Session, None, None]:
        """Context manager for transaction handling."""
        try:
            yield self.session
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def _disable_statement_logging(self) -> None:
        """Disable statement logging for security when handling secrets."""
        try:
            self.session.execute(text("SET LOCAL statement_timeout = 0"))
            self.session.execute(text("SET LOCAL log_statement = 'none'"))
        except Exception:
            pass

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

    def get_secret(self, secret_id: str) -> str:
        """Retrieve a secret from Supabase Vault."""
        with self._transaction():
            result = self.session.execute(
                text(
                    "SELECT decrypted_secret FROM vault.decrypted_secrets WHERE id = :id"
                ),
                {"id": secret_id},
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
