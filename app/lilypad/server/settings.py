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
    kafka_consumer_group: str = Field(default="lilypad-span-processor")
    kafka_max_concurrent_traces: int = Field(default=1000)
    kafka_max_spans_per_trace: int = Field(default=500)
    kafka_buffer_ttl_seconds: int = Field(default=300)
    kafka_cleanup_interval_seconds: int = Field(default=60)

    # Database settings
    db_host: str | None = None
    db_name: str | None = None
    db_user: str | None = None
    db_password: str | None = None
    db_port: int | None = None
    db_pool_size: int = 8
    db_max_overflow: int = 2
    db_pool_recycle: int = 1800
    db_pool_pre_ping: bool = True

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


def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()
