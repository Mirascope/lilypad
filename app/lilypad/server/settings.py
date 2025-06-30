"""Server settings"""

from typing import Any
from urllib.parse import urlparse

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from lilypad.ee.server import REMOTE_API_URL, REMOTE_CLIENT_URL


class Settings(BaseSettings):
    """Server settings"""

    # Server settings
    environment: str = Field(default="production")
    port: int = Field(default=8000)
    remote_api_url: str = Field(default=REMOTE_API_URL)
    remote_client_url: str = Field(default=REMOTE_CLIENT_URL)
    api_key: str | None = None
    project_id: str | None = None
    serve_frontend: bool | None = Field(
        default=None, description="Serve the client in the root"
    )
    experimental: bool = Field(default=False)
    playground_venv_path: str = Field(default=".playground-venv")
    # GitHub OAuth settings
    github_client_id: str = Field(default="my_client_id")
    github_client_secret: str = Field(default="my_client_secret")

    # Google OAuth settings
    google_client_id: str = Field(default="my_client_id")
    google_client_secret: str = Field(default="my_client_secret")
    # JWT settings
    jwt_secret: str = Field(default="my_secret_key", description="JWT secret key")
    jwt_algorithm: str = "HS256"

    # PostHog settings
    posthog_api_key: str | None = None
    posthog_host: str | None = None

    # Resend
    resend_api_key: str | None = None

    # OpenSearch
    opensearch_host: str | None = None
    opensearch_port: int | None = None
    opensearch_user: str | None = None
    opensearch_password: str | None = None
    opensearch_use_ssl: bool = False

    # Kafka settings
    kafka_bootstrap_servers: str | None = None
    kafka_topic_span_ingestion: str = Field(default="span-ingestion")
    kafka_topic_stripe_ingestion: str = Field(default="stripe-ingestion")
    kafka_consumer_group: str = Field(default="lilypad-span-processor")
    kafka_max_concurrent_traces: int = Field(default=1000)
    kafka_max_spans_per_trace: int = Field(default=500)
    kafka_buffer_ttl_seconds: int = Field(default=300)
    kafka_cleanup_interval_seconds: int = Field(default=60)
    kafka_auto_setup_topics: bool = Field(default=False)

    # Database settings
    db_host: str | None = None
    db_name: str | None = None
    db_user: str | None = None
    db_password: str | None = None
    db_port: int | None = None

    # Worker configuration
    worker_count: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Number of worker processes",
    )
    db_max_connections: int = Field(
        default=100,
        ge=20,
        le=1000,
        description="Maximum database connections allowed",
    )

    @property
    def calculated_pool_size(self) -> int:
        """Calculate safe pool size per worker based on total connections."""
        # Reserve connections for maintenance, migrations, etc.
        reserved_connections = 10
        available_connections = self.db_max_connections - reserved_connections

        # Each worker gets an equal share
        per_worker_connections = available_connections // self.worker_count

        # Split between pool and overflow (60% pool, 40% overflow)
        pool_size = int(per_worker_connections * 0.6)

        # Ensure minimum viable pool size
        return max(5, min(pool_size, 50))

    @property
    def calculated_max_overflow(self) -> int:
        """Calculate safe max overflow per worker."""
        # Reserve connections for maintenance
        reserved_connections = 10
        available_connections = self.db_max_connections - reserved_connections

        # Each worker gets an equal share
        per_worker_connections = available_connections // self.worker_count

        # Split between pool and overflow (60% pool, 40% overflow)
        overflow_size = int(per_worker_connections * 0.4)

        # Ensure minimum viable overflow
        return max(2, min(overflow_size, 20))

    db_pool_size: int = Field(default=20, ge=5, le=100)
    db_max_overflow: int = Field(default=10, ge=0, le=50)
    db_pool_recycle: int = Field(default=3600, ge=0)
    db_pool_pre_ping: bool = Field(default=True)
    db_pool_timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Seconds to wait for connection",
    )
    kafka_db_thread_pool_size: int = Field(
        default=4, description="Number of threads for Kafka processor DB operations"
    )
    use_async_db: bool = Field(
        default=False, description="Use async database connections (experimental)"
    )

    # Stripe settings
    stripe_api_key: str | None = None
    stripe_secret_api_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_cloud_product_id: str | None = None
    stripe_cloud_pro_flat_price_id: str | None = None
    stripe_cloud_pro_meter_price_id: str | None = None
    stripe_cloud_team_flat_price_id: str | None = None
    stripe_cloud_team_meter_price_id: str | None = None
    stripe_spans_metering_id: str | None = None

    # Secret Manager settings
    secret_manager_type: str = Field(
        default="SUPABASE_VAULT",
        description="Type of secret manager to use: SUPABASE_VAULT or AWS_SECRET_MANAGER",
    )
    aws_region: str = Field(
        default="us-east-1",
        description="AWS region for Secret Manager (only used when secret_manager_type is AWS_SECRET_MANAGER)",
    )
    aws_secret_manager_force_delete: bool = Field(
        default=False,
        description="Force immediate deletion of secrets without recovery window (use with caution)",
    )
    aws_secret_manager_max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts for AWS Secret Manager API calls",
    )
    aws_secret_manager_enable_metrics: bool = Field(
        default=False,  # Changed to False by default for security
        description="Enable metrics collection for AWS Secret Manager operations",
    )
    aws_secret_manager_pre_initialize: bool = Field(
        default=False,
        description="Pre-initialize AWS client to reduce first request latency",
    )
    aws_secret_manager_kms_key_id: str | None = Field(
        default=None,
        description="KMS key ID for encrypting secrets (optional)",
    )

    @property
    def config(self) -> dict[str, Any]:
        """Get the configuration for the current environment"""
        configs = {
            "development": {
                "api_url": "http://localhost:8000",
                "client_url": "http://localhost:5173",
            },
            "local": {
                "api_url": self.remote_api_url,
                "client_url": self.remote_client_url,
            },
            "production": {
                "api_url": self.remote_api_url,
                "client_url": self.remote_client_url,
            },
        }
        return configs.get(self.environment, configs["development"])

    @property
    def api_url(self) -> str:
        """Get the API URL"""
        return self.config["api_url"]

    @property
    def client_url(self) -> str:
        """Get the client URL"""
        return self.config["client_url"]

    @property
    def remote_client_hostname(self) -> str:
        """Get the remote client hostname"""
        return urlparse(self.client_url).hostname or ""

    model_config = SettingsConfigDict(env_prefix="LILYPAD_")

    def __init__(self, **data: Any) -> None:
        """Initialize settings with calculated defaults."""
        super().__init__(**data)

        # If pool sizes weren't explicitly set, use calculated values
        if "db_pool_size" not in data:
            self.db_pool_size = self.calculated_pool_size
        if "db_max_overflow" not in data:
            self.db_max_overflow = self.calculated_max_overflow

        # Log the configuration
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"Database pool configuration: "
            f"workers={self.worker_count}, "
            f"max_connections={self.db_max_connections}, "
            f"pool_size={self.db_pool_size}, "
            f"max_overflow={self.db_max_overflow}, "
            f"total_per_worker={self.db_pool_size + self.db_max_overflow}, "
            f"total_all_workers={self.worker_count * (self.db_pool_size + self.db_max_overflow)}"
        )


def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()
