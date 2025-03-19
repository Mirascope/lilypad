"""Abstract base class for secret management."""

from abc import ABC, abstractmethod


class SecretManager(ABC):
    """Interface for secret management services."""

    @abstractmethod
    def store_secret(
        self, name: str, secret: str, description: str | None = None
    ) -> str:
        """Store a secret and return its ID."""
        ...

    @abstractmethod
    def get_secret(self, secret_id: str) -> str | None:
        """Retrieve a secret by its ID."""
        ...

    @abstractmethod
    def update_secret(self, secret_id: str, secret: str) -> bool:
        """Update an existing secret."""
        ...

    @abstractmethod
    def delete_secret(self, secret_id: str) -> bool:
        """Delete a secret by its ID."""
        ...

    @abstractmethod
    def get_secret_id_by_name(self, name: str) -> str | None:
        """Retrieve the secret ID by name."""
        ...
