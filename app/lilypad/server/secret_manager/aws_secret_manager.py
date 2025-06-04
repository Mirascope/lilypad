"""Production-ready AWS Secrets Manager implementation."""

import atexit
import concurrent.futures
import logging
import os
import re
import threading
from enum import Enum
from typing import TYPE_CHECKING, Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient
else:
    SecretsManagerClient = Any

from .config import AWSSecretManagerConfig
from .exceptions import (
    BinarySecretError,
    SecretAccessDeniedError,
    SecretNotFoundError,
    SecretOperationError,
    SecretValidationError,
)
from .metrics import MetricsCollector, OperationType
from .secret_manager import SecretManager

logger = logging.getLogger(__name__)


class AWSErrorCode(str, Enum):
    """AWS Secrets Manager error codes."""

    RESOURCE_NOT_FOUND = "ResourceNotFoundException"
    ACCESS_DENIED = "AccessDeniedException"
    INVALID_REQUEST = "InvalidRequestException"
    INVALID_PARAMETER = "InvalidParameterException"
    THROTTLING = "ThrottlingException"
    LIMIT_EXCEEDED = "LimitExceededException"
    ENCRYPTION_FAILURE = "EncryptionFailure"
    INTERNAL_SERVICE_ERROR = "InternalServiceError"
    RESOURCE_EXISTS = "ResourceExistsException"
    DECRYPTION_FAILURE = "DecryptionFailure"
    INVALID_SECURITY_TOKEN = "InvalidUserException.NotFound"


class AWSSecretManager(SecretManager):
    """Thread-safe, production-ready AWS Secrets Manager implementation."""

    def __init__(self, config: AWSSecretManagerConfig | None = None) -> None:
        """Initialize AWS Secrets Manager with configuration.

        Args:
            config: Configuration object. If None, uses defaults.
        """
        self.config = config or AWSSecretManagerConfig()

        # Thread-safe client initialization
        self._client: SecretsManagerClient | None = None
        self._client_lock = threading.Lock()

        # Metrics collector (not singleton)
        self._metrics = MetricsCollector() if self.config.enable_metrics else None

        # Register cleanup on exit (only once per class)
        if not hasattr(AWSSecretManager, "_cleanup_registered"):
            atexit.register(self._cleanup)
            AWSSecretManager._cleanup_registered = True

        # Log configuration (without sensitive details)
        logger.info(
            "Initializing AWS Secret Manager",
            extra={
                "region": self.config.region_name,
                "metrics_enabled": self.config.enable_metrics,
            },
        )

        # Pre-initialize client if requested (reduces first request latency)
        if self.config.pre_initialize:
            _ = self.client

    @property
    def client(self) -> SecretsManagerClient:
        """Get or create AWS Secrets Manager client (thread-safe)."""
        # Fast path: check without lock first
        if self._client is not None:
            return self._client

        with self._client_lock:
            # Double-check locking pattern
            if self._client is None:
                config = Config(
                    region_name=self.config.region_name,
                    retries={
                        "max_attempts": self.config.max_retries,
                        "mode": "adaptive",  # Handles throttling automatically
                    },
                    max_pool_connections=50,
                    connect_timeout=5,
                    read_timeout=10,
                )

                # Check for custom endpoint (e.g., LocalStack)
                endpoint_url = os.getenv("AWS_ENDPOINT_URL")

                if endpoint_url:
                    # Using custom endpoint (LocalStack or other)
                    self._client = boto3.client(
                        "secretsmanager", endpoint_url=endpoint_url, config=config
                    )
                    logger.info(
                        "Created AWS client with custom endpoint",
                        extra={
                            "endpoint": endpoint_url,
                            "region": self.config.region_name,
                        },
                    )
                else:
                    # Using standard AWS endpoint
                    self._client = boto3.client("secretsmanager", config=config)
                    logger.debug(
                        "Created AWS client", extra={"region": self.config.region_name}
                    )
        return self._client

    def _cleanup(self) -> None:
        """Cleanup resources on exit."""
        if self._client is not None:
            try:
                self._client = None
                logger.debug("Cleaned up AWS Secret Manager client")
            except Exception as e:
                logger.error("Error during cleanup", exc_info=e)

    def _validate_secret_name(self, name: str) -> None:
        """Validate secret name to prevent injection and ensure AWS compatibility.

        Args:
            name: The secret name to validate

        Raises:
            SecretValidationError: If the name is invalid
        """
        if not name:
            raise SecretValidationError("Secret name cannot be empty")

        # AWS Secrets Manager naming rules: alphanumeric, -, _, /
        # We restrict further for security but allow / for namespacing
        if not re.match(r"^[\w\-/]+$", name):
            raise SecretValidationError(
                "Invalid secret name. Only alphanumeric characters, hyphens, underscores, and forward slashes are allowed."
            )

        if len(name) > self.config.MAX_SECRET_NAME_LENGTH:
            raise SecretValidationError(
                f"Secret name too long: {len(name)} characters (max {self.config.MAX_SECRET_NAME_LENGTH})"
            )

    def _validate_secret_value(self, secret: str) -> None:
        """Validate secret value size.

        Args:
            secret: The secret value to validate

        Raises:
            SecretValidationError: If the secret is too large
        """
        secret_bytes = secret.encode("utf-8")
        if len(secret_bytes) > self.config.MAX_SECRET_SIZE_BYTES:
            raise SecretValidationError(
                f"Secret too large: {len(secret_bytes)} bytes (max {self.config.MAX_SECRET_SIZE_BYTES} bytes)"
            )

    def _get_secret_name(self, name: str) -> str:
        """Generate a consistent secret name format.

        Args:
            name: The base name for the secret

        Returns:
            Formatted secret name
        """
        self._validate_secret_name(name)
        return f"lilypad/{name}"

    def _handle_client_error(self, error: ClientError, operation: str) -> None:
        """Handle AWS ClientError and convert to appropriate exception.

        Args:
            error: The ClientError from boto3
            operation: The operation that failed (for logging)

        Raises:
            SecretNotFoundError: If the secret was not found
            SecretAccessDeniedError: If access was denied
            SecretOperationError: For other errors
        """
        error_code = error.response.get("Error", {}).get("Code", "Unknown")

        logger.error(
            f"AWS Secrets Manager error during {operation}",
            extra={"error_code": error_code, "operation": operation},
        )

        if error_code == AWSErrorCode.RESOURCE_NOT_FOUND:
            raise SecretNotFoundError(f"Secret not found during {operation}")
        elif error_code == AWSErrorCode.ACCESS_DENIED:
            raise SecretAccessDeniedError(
                f"Access denied to AWS Secrets Manager during {operation}"
            )
        elif error_code in [
            AWSErrorCode.INVALID_REQUEST,
            AWSErrorCode.INVALID_PARAMETER,
        ]:
            raise SecretValidationError(f"Invalid request during {operation}")
        elif error_code in [AWSErrorCode.THROTTLING, AWSErrorCode.LIMIT_EXCEEDED]:
            # These should be retried automatically by boto3's adaptive mode
            raise SecretOperationError(
                f"Rate limit exceeded during {operation}. Please retry later."
            )
        elif error_code == AWSErrorCode.ENCRYPTION_FAILURE:
            raise SecretOperationError(f"Encryption failed during {operation}")
        elif error_code == AWSErrorCode.DECRYPTION_FAILURE:
            raise SecretOperationError(f"Decryption failed during {operation}")
        elif error_code == AWSErrorCode.INTERNAL_SERVICE_ERROR:
            raise SecretOperationError(
                f"AWS service error during {operation}. Please retry."
            )
        elif error_code == AWSErrorCode.INVALID_SECURITY_TOKEN:
            raise SecretAccessDeniedError(f"Invalid security token during {operation}")
        else:
            # Don't expose internal AWS error details
            raise SecretOperationError(f"Operation failed: {operation}")

    def store_secret(
        self, name: str, secret: str, description: str | None = None
    ) -> str:
        """Store a secret in AWS Secrets Manager (create or update).

        Args:
            name: Name of the secret
            secret: The secret value to store
            description: Optional description for the secret

        Returns:
            The ARN of the created/updated secret

        Raises:
            SecretValidationError: If validation fails
            SecretOperationError: If the operation fails
        """
        # Validate inputs
        self._validate_secret_value(secret)
        secret_name = self._get_secret_name(name)

        if self._metrics:
            with self._metrics.measure_operation(OperationType.CREATE):
                return self._store_secret_internal(
                    secret_name, secret, description, name
                )
        else:
            return self._store_secret_internal(secret_name, secret, description, name)

    def _store_secret_internal(
        self, secret_name: str, secret: str, description: str | None, original_name: str
    ) -> str:
        """Internal method to store secret with atomic create-or-update."""
        # Try to create first (avoids race condition)
        try:
            create_params = {
                "Name": secret_name,
                "SecretString": secret,
                "Description": description or f"API key for {original_name}",
            }

            # Add KMS key if configured
            if self.config.kms_key_id:
                create_params["KmsKeyId"] = self.config.kms_key_id

            response = self.client.create_secret(**create_params)
            logger.debug("Created new secret")
            return response["ARN"]

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")

            if error_code == AWSErrorCode.RESOURCE_EXISTS:
                # Secret exists, update it
                try:
                    # Get the ARN first
                    describe_response = self.client.describe_secret(
                        SecretId=secret_name
                    )
                    secret_arn = describe_response["ARN"]

                    # Update the secret
                    update_params = {
                        "SecretId": secret_arn,
                        "SecretString": secret,
                    }

                    if description:
                        update_params["Description"] = description

                    self.client.update_secret(**update_params)
                    logger.debug("Updated existing secret")
                    return secret_arn

                except ClientError as update_error:
                    self._handle_client_error(update_error, "update")
            else:
                self._handle_client_error(e, "create")

    def get_secret(self, secret_id: str) -> str | None:
        """Retrieve a secret from AWS Secrets Manager.

        Args:
            secret_id: The ARN or name of the secret

        Returns:
            The secret value or None if not found
        """
        if self._metrics:
            with self._metrics.measure_operation(OperationType.READ):
                return self._get_secret_internal(secret_id)
        else:
            return self._get_secret_internal(secret_id)

    def _get_secret_internal(self, secret_id: str) -> str | None:
        """Internal method to retrieve secret."""
        try:
            response = self.client.get_secret_value(SecretId=secret_id)

            # Handle both string and binary secrets
            if "SecretString" in response:
                return response["SecretString"]
            else:
                # Binary secrets are not supported for API keys
                logger.warning(
                    "Binary secret not supported", extra={"secret_id": secret_id}
                )
                raise BinarySecretError(
                    f"Secret '{secret_id}' is in binary format, which is not supported"
                )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == AWSErrorCode.RESOURCE_NOT_FOUND:
                logger.debug("Secret not found")
                return None
            else:
                self._handle_client_error(e, "retrieve")

    def update_secret(self, secret_id: str, secret: str) -> bool:
        """Update an existing secret in AWS Secrets Manager.

        Args:
            secret_id: The ARN or name of the secret
            secret: The new secret value

        Returns:
            True if successful, False otherwise
        """
        self._validate_secret_value(secret)

        if self._metrics:
            with self._metrics.measure_operation(OperationType.UPDATE):
                return self._update_secret_internal(secret_id, secret)
        else:
            return self._update_secret_internal(secret_id, secret)

    def _update_secret_internal(self, secret_id: str, secret: str) -> bool:
        """Internal method to update secret."""
        try:
            self.client.update_secret(
                SecretId=secret_id,
                SecretString=secret,
            )
            logger.debug("Updated secret")
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == AWSErrorCode.RESOURCE_NOT_FOUND:
                logger.debug("Secret not found for update")
                return False
            else:
                self._handle_client_error(e, "update")

    def delete_secret(self, secret_id: str) -> bool:
        """Delete a secret from AWS Secrets Manager.

        Args:
            secret_id: The ARN or name of the secret

        Returns:
            True if successful, False otherwise
        """
        if self._metrics:
            with self._metrics.measure_operation(OperationType.DELETE):
                return self._delete_secret_internal(secret_id)
        else:
            return self._delete_secret_internal(secret_id)

    def _delete_secret_internal(self, secret_id: str) -> bool:
        """Internal method to delete secret."""
        try:
            delete_params = {"SecretId": secret_id}

            if self.config.force_delete:
                delete_params["ForceDeleteWithoutRecovery"] = True
                logger.warning("Force deleting secret without recovery")
            else:
                delete_params["RecoveryWindowInDays"] = (
                    self.config.DEFAULT_RECOVERY_WINDOW_DAYS
                )
                logger.info(
                    f"Scheduling secret deletion with {self.config.DEFAULT_RECOVERY_WINDOW_DAYS}-day recovery window"
                )

            self.client.delete_secret(**delete_params)
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == AWSErrorCode.RESOURCE_NOT_FOUND:
                logger.debug("Secret not found for deletion")
                return False
            else:
                self._handle_client_error(e, "delete")

    def get_secret_id_by_name(self, name: str) -> str | None:
        """Retrieve the secret ID (ARN) by name.

        Args:
            name: The name of the secret

        Returns:
            The ARN of the secret or None if not found
        """
        secret_name = self._get_secret_name(name)

        if self._metrics:
            with self._metrics.measure_operation(OperationType.DESCRIBE):
                return self._get_secret_id_by_name_internal(secret_name)
        else:
            return self._get_secret_id_by_name_internal(secret_name)

    def _get_secret_id_by_name_internal(self, secret_name: str) -> str | None:
        """Internal method to get secret ID by name."""
        try:
            response = self.client.describe_secret(SecretId=secret_name)
            return response["ARN"]
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == AWSErrorCode.RESOURCE_NOT_FOUND:
                logger.debug("Secret not found by name")
                return None
            else:
                self._handle_client_error(e, "get_secret_id")

    # Production-ready batch operations with parallel processing
    def get_secrets_batch(self, secret_ids: list[str]) -> dict[str, str | None]:
        """Retrieve multiple secrets in batch with parallel processing.

        Args:
            secret_ids: List of secret IDs to retrieve

        Returns:
            Dictionary mapping secret_id to secret value (or None if not found)
        """
        results = {}

        def get_single_secret(secret_id: str) -> tuple[str, str | None]:
            """Helper function for parallel processing."""
            try:
                return secret_id, self.get_secret(secret_id)
            except Exception as e:
                logger.error("Error retrieving secret in batch", exc_info=e)
                return secret_id, None

        # Process in parallel with limited workers
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(len(secret_ids), self.config.MAX_CONCURRENT_WORKERS)
        ) as executor:
            # Submit all tasks
            future_to_id = {
                executor.submit(get_single_secret, secret_id): secret_id
                for secret_id in secret_ids
            }

            # Collect results
            for future in concurrent.futures.as_completed(future_to_id):
                secret_id, value = future.result()
                results[secret_id] = value

        return results

    def delete_secrets_batch(self, secret_ids: list[str]) -> dict[str, bool]:
        """Delete multiple secrets in batch with parallel processing.

        Args:
            secret_ids: List of secret IDs to delete

        Returns:
            Dictionary mapping secret_id to success status
        """
        results = {}

        def delete_single_secret(secret_id: str) -> tuple[str, bool]:
            """Helper function for parallel processing."""
            try:
                return secret_id, self.delete_secret(secret_id)
            except Exception as e:
                logger.error("Error deleting secret in batch", exc_info=e)
                return secret_id, False

        # Process in parallel with limited workers
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(len(secret_ids), self.config.MAX_CONCURRENT_WORKERS)
        ) as executor:
            # Submit all tasks
            future_to_id = {
                executor.submit(delete_single_secret, secret_id): secret_id
                for secret_id in secret_ids
            }

            # Collect results
            for future in concurrent.futures.as_completed(future_to_id):
                secret_id, success = future.result()
                results[secret_id] = success

        return results

    def get_metrics_summary(self) -> dict[str, Any] | None:
        """Get metrics summary if metrics are enabled.

        Returns:
            Metrics summary or None if metrics are disabled
        """
        if self._metrics:
            return self._metrics.get_summary()
        return None

    def reset_metrics(self) -> None:
        """Reset metrics if enabled."""
        if self._metrics:
            self._metrics.reset()
            logger.info("Metrics reset")
