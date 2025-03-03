"""Server settings"""

from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Server settings"""

    # Server settings
    environment: str = Field(default="production")
    port: int = Field(default=8000)
    remote_api_url: str = Field(default="https://api.lilypad.so")
    remote_client_url: str = Field(default="https://app.lilypad.so")
    api_key: str | None = None
    project_id: str | None = None
    serve_frontend: str | None = Field(
        default=None, description="Serve the client in the root"
    )
    experimental: bool = Field(default=False)

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

    # Database settings
    db_host: str | None = None
    db_name: str | None = None
    db_user: str | None = None
    db_password: str | None = None
    db_port: int | None = None

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

    model_config = SettingsConfigDict(env_prefix="LILYPAD_")


def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()
