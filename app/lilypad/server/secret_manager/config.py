"""Configuration for AWS Secret Manager."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AWSSecretManagerConfig:
    """Immutable configuration for AWS Secret Manager."""

    region_name: str = "us-east-1"
    force_delete: bool = False
    enable_metrics: bool = False  # Changed default to False
    max_retries: int = 3
    pre_initialize: bool = False
    kms_key_id: str | None = None

    # AWS limits: https://docs.aws.amazon.com/secretsmanager/latest/userguide/reference_limits.html
    MAX_SECRET_SIZE_BYTES: int = 65536  # 64KB AWS limit
    MAX_SECRET_NAME_LENGTH: int = 512  # AWS allows 512 characters
    MAX_BATCH_SIZE: int = 20  # AWS batch API limit
    MAX_CONCURRENT_WORKERS: int = 5  # Limit concurrent API calls

    # Recovery window (days)
    DEFAULT_RECOVERY_WINDOW_DAYS: int = 30  # Changed from 7 to 30 for safety

    # Performance thresholds
    SLOW_OPERATION_THRESHOLD_MS: float = 1000.0
    HIGH_ERROR_RATE_THRESHOLD: float = 0.95  # 95% success rate
