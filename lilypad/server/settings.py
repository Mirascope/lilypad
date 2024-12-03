"""Server settings"""

from functools import lru_cache
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Server settings"""

    # Server settings
    environment: str = Field(default="development")
    port: int = Field(default=8000)
    local_client_url: str = Field(default="http://localhost:8000")
    local_api_url: str = Field(default="http://localhost:8000/api")
    prod_client_url: str = Field(default="")
    prod_api_url: str = Field(default="")

    # GitHub OAuth settings
    github_client_id: str | None = None
    github_client_secret: str | None = None

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
                "api_url": "http://localhost:8000/api",
                "client_url": "",
            },
            "local": {
                "api_url": self.local_api_url,
                "client_url": self.local_client_url,
            },
            "production": {
                "api_url": self.prod_api_url,
                "client_url": self.prod_client_url,
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


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()
