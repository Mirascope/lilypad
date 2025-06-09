"""Factory for creating secret manager instances."""

from enum import Enum, auto

from sqlmodel import Session

from ..settings import get_settings
from .aws_secret_manager import AWSSecretManager
from .config import AWSSecretManagerConfig
from .secret_manager import SecretManager
from .supabase_vault_manager import SupabaseVaultManager


class SecretManagerType(Enum):
    """Supported secret manager types."""

    SUPABASE_VAULT = auto()
    AWS_SECRET_MANAGER = auto()


def get_secret_manager(
    session: Session | None = None,
    manager_type: SecretManagerType | None = None,
) -> SecretManager:
    """Factory function to get a secret manager implementation.

    Args:
        session: SQLModel session (required for Supabase Vault)
        manager_type: Type of secret manager to use. If None, determined from settings

    Returns:
        SecretManager implementation
    """
    settings = get_settings()

    # Determine manager type from settings if not specified
    if manager_type is None:
        secret_manager_env = settings.secret_manager_type
        try:
            manager_type = SecretManagerType[secret_manager_env]
        except KeyError:
            raise ValueError(f"Invalid SECRET_MANAGER_TYPE: {secret_manager_env}")

    if manager_type == SecretManagerType.SUPABASE_VAULT:
        if session is None:
            raise ValueError("Session is required for Supabase Vault Manager")
        return SupabaseVaultManager(session)
    elif manager_type == SecretManagerType.AWS_SECRET_MANAGER:
        # Get AWS configuration from settings
        config = AWSSecretManagerConfig(
            region_name=settings.aws_region,
            force_delete=settings.aws_secret_manager_force_delete,
            enable_metrics=settings.aws_secret_manager_enable_metrics,
            max_retries=settings.aws_secret_manager_max_retries,
            pre_initialize=getattr(
                settings, "aws_secret_manager_pre_initialize", False
            ),
            kms_key_id=getattr(settings, "aws_secret_manager_kms_key_id", None),
        )
        return AWSSecretManager(config)
    else:
        raise ValueError(f"Unsupported secret manager type: {manager_type}")
