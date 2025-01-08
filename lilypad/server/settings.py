"""Server settings"""

from functools import lru_cache
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Server settings"""

    # Server settings
    environment: str = Field(default="production")
    port: int = Field(default=8000)
    remote_base_url: str = Field(default="https://app.lilypad.so")

    # GitHub OAuth settings
    github_client_id: str = Field(default="my_client_id")
    github_client_secret: str = Field(default="my_client_secret")
    # JWT settings
    jwt_secret: str = Field(default="my_secret_key", description="JWT secret key")
    jwt_algorithm: str = "HS256"

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
                "base_url": "http://localhost:8000",
                "client_url": "http://localhost:5173",
            },
            "local": {
                "base_url": self.remote_base_url,
                "client_url": self.remote_base_url,
            },
            "production": {
                "base_url": self.remote_base_url,
                "client_url": self.remote_base_url,
            },
        }
        return configs.get(self.environment, configs["development"])

    @property
    def base_url(self) -> str:
        """Get the API URL"""
        return self.config["base_url"]

    @property
    def client_url(self) -> str:
        """Get the client URL"""
        return self.config["client_url"]

    model_config = SettingsConfigDict(env_prefix="LILYPAD_")


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()
