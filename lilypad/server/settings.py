"""Server settings"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Server settings"""

    # WorkOS settings
    workos_api_key: str = Field(default="dummy_key", description="WorkOS API key")
    workos_client_id: str = Field(
        default="dummy_client_id", description="WorkOS Client ID"
    )

    # JWT settings
    jwt_secret: str = Field(default="my_secret_key", description="JWT secret key")
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = Field(
        default=1440, description="Token expiration in minutes (24 hours)"
    )

    environment: str = Field(default="development")

    model_config = SettingsConfigDict(env_prefix="LILYPAD_")


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()
