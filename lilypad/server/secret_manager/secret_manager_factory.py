"""Factory for creating secret manager instances."""

from enum import Enum, auto

from sqlmodel import Session

from .secret_manager import SecretManager
from .supabase_vault_manager import SupabaseVaultManager


class SecretManagerType(Enum):
    """Supported secret manager types."""

    SUPABASE_VAULT = auto()


def get_secret_manager(
    session: Session,
    manager_type: SecretManagerType = SecretManagerType.SUPABASE_VAULT,
) -> SecretManager:
    """Factory function to get a secret manager implementation."""
    if manager_type == SecretManagerType.SUPABASE_VAULT:
        return SupabaseVaultManager(session)
    else:
        raise ValueError(f"Unsupported secret manager type: {manager_type}")
