"""Tests for AWS Secret Manager implementation."""

import contextlib
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, PropertyMock, patch

import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from lilypad.server.secret_manager.aws_secret_manager import AWSSecretManager
from lilypad.server.secret_manager.config import AWSSecretManagerConfig
from lilypad.server.secret_manager.exceptions import (
    SecretAccessDeniedError,
    SecretOperationError,
    SecretValidationError,
)
from lilypad.server.secret_manager.metrics import OperationType


class TestAWSSecretManagerProduction:
    """Production-ready tests for AWS Secret Manager."""

    @pytest.fixture
    def manager_with_metrics(self):
        """Create manager with metrics enabled."""
        with mock_aws():
            config = AWSSecretManagerConfig(
                region_name="us-east-1",
                force_delete=True,
                enable_metrics=True,
            )
            yield AWSSecretManager(config)

    @pytest.fixture
    def manager_without_metrics(self):
        """Create manager with metrics disabled."""
        with mock_aws():
            config = AWSSecretManagerConfig(
                region_name="us-east-1",
                force_delete=True,
                enable_metrics=False,
            )
            yield AWSSecretManager(config)

    # Error handling tests
    @mock_aws
    def test_access_denied_error_handling(self, manager_with_metrics):
        """Test handling of access denied errors."""
        # Mock client to raise AccessDeniedException
        mock_client = Mock()
        mock_client.describe_secret.side_effect = ClientError(
            error_response={
                "Error": {
                    "Code": "AccessDeniedException",
                    "Message": "User is not authorized",
                }
            },
            operation_name="DescribeSecret",
        )

        with patch.object(
            type(manager_with_metrics),
            "client",
            new_callable=PropertyMock,
            return_value=mock_client,
        ):
            with pytest.raises(SecretAccessDeniedError) as exc_info:
                manager_with_metrics.get_secret_id_by_name("test")

            assert "Access denied" in str(exc_info.value)

    @mock_aws
    def test_throttling_error_handling(self, manager_with_metrics):
        """Test handling of throttling errors."""
        mock_client = Mock()
        mock_client.get_secret_value.side_effect = ClientError(
            error_response={
                "Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}
            },
            operation_name="GetSecretValue",
        )

        with patch.object(
            type(manager_with_metrics),
            "client",
            new_callable=PropertyMock,
            return_value=mock_client,
        ):
            with pytest.raises(SecretOperationError) as exc_info:
                manager_with_metrics.get_secret("test-arn")

            assert "Rate limit exceeded" in str(exc_info.value)

    @mock_aws
    def test_invalid_parameter_error_handling(self, manager_with_metrics):
        """Test handling of invalid parameter errors."""
        mock_client = Mock()
        # First mock describe_secret to raise ResourceNotFoundException (secret doesn't exist)
        mock_client.describe_secret.side_effect = ClientError(
            error_response={"Error": {"Code": "ResourceNotFoundException"}},
            operation_name="DescribeSecret",
        )
        # Then mock create_secret to raise InvalidParameterException
        mock_client.create_secret.side_effect = ClientError(
            error_response={
                "Error": {
                    "Code": "InvalidParameterException",
                    "Message": "Invalid parameter",
                }
            },
            operation_name="CreateSecret",
        )

        with patch.object(
            type(manager_with_metrics),
            "client",
            new_callable=PropertyMock,
            return_value=mock_client,
        ):
            with pytest.raises(SecretValidationError) as exc_info:
                manager_with_metrics.store_secret("test", "value")

            assert "Invalid request" in str(exc_info.value)

    # Size limit tests
    @mock_aws
    def test_secret_size_validation(self, manager_with_metrics):
        """Test secret size validation."""
        # Test max size (64KB)
        large_secret = "x" * 65536  # Exactly 64KB
        manager_with_metrics.store_secret("test", large_secret)  # Should succeed

        # Test over limit
        too_large_secret = "x" * 65537  # 64KB + 1 byte
        with pytest.raises(SecretValidationError) as exc_info:
            manager_with_metrics.store_secret("test", too_large_secret)

        assert "Secret too large" in str(exc_info.value)
        assert "65537 bytes" in str(exc_info.value)

    @mock_aws
    def test_unicode_secret_size_validation(self, manager_with_metrics):
        """Test size validation with unicode characters."""
        # Each emoji is 4 bytes in UTF-8
        emoji_secret = "🔐" * 16384  # Exactly 64KB
        manager_with_metrics.store_secret("test", emoji_secret)  # Should succeed

        # Over limit
        too_many_emojis = "🔐" * 16385  # 64KB + 4 bytes
        with pytest.raises(SecretValidationError) as exc_info:
            manager_with_metrics.store_secret("test", too_many_emojis)

        assert "Secret too large" in str(exc_info.value)

    # Thread safety tests
    @mock_aws
    def test_thread_safe_client_initialization(self):
        """Test that client initialization is thread-safe."""
        config = AWSSecretManagerConfig(enable_metrics=False)
        manager = AWSSecretManager(config)
        clients = []

        def get_client():
            clients.append(manager.client)

        # Create multiple threads trying to access client simultaneously
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_client) for _ in range(10)]
            for future in as_completed(futures):
                future.result()

        # All clients should be the same instance
        assert all(client is clients[0] for client in clients)

    @mock_aws
    def test_concurrent_operations(self, manager_with_metrics):
        """Test concurrent secret operations."""
        num_threads = 10
        secrets_per_thread = 5

        def create_secrets(thread_id):
            results = []
            for i in range(secrets_per_thread):
                name = f"thread_{thread_id}_secret_{i}"
                value = f"value_{thread_id}_{i}"
                try:
                    arn = manager_with_metrics.store_secret(name, value)
                    retrieved = manager_with_metrics.get_secret(arn)
                    results.append(retrieved == value)
                except Exception:
                    results.append(False)
            return results

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(create_secrets, i) for i in range(num_threads)]
            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())

        # All operations should succeed
        assert all(all_results)
        assert len(all_results) == num_threads * secrets_per_thread

    # Metrics tests
    @mock_aws
    def test_metrics_collection(self, manager_with_metrics):
        """Test that metrics are collected correctly."""
        # Reset metrics
        manager_with_metrics.reset_metrics()

        # Perform operations
        arn = manager_with_metrics.store_secret("test", "value")
        manager_with_metrics.get_secret(arn)
        manager_with_metrics.update_secret(arn, "new_value")
        manager_with_metrics.delete_secret(arn)

        # Get metrics
        summary = manager_with_metrics.get_metrics_summary()

        assert summary is not None
        assert (
            summary["total_api_calls"] >= 4
        )  # 4 operations (create, read, update, delete)
        assert "operations" in summary

        # Check specific operations
        operations = summary["operations"]
        assert OperationType.CREATE.value in operations
        assert OperationType.READ.value in operations
        assert OperationType.UPDATE.value in operations
        assert OperationType.DELETE.value in operations

    @mock_aws
    def test_metrics_disabled(self, manager_without_metrics):
        """Test behavior when metrics are disabled."""
        # Perform operations
        arn = manager_without_metrics.store_secret("test", "value")
        manager_without_metrics.get_secret(arn)

        # Metrics should be None
        summary = manager_without_metrics.get_metrics_summary()
        assert summary is None

    @mock_aws
    def test_error_metrics(self, manager_with_metrics):
        """Test that errors are tracked in metrics."""
        manager_with_metrics.reset_metrics()

        # Cause some errors
        mock_client = Mock()
        mock_client.get_secret_value.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalServiceError"}},
            operation_name="GetSecretValue",
        )

        with patch.object(
            type(manager_with_metrics),
            "client",
            new_callable=PropertyMock,
            return_value=mock_client,
        ):
            # Try to get secret multiple times
            for _ in range(3):
                with contextlib.suppress(Exception):
                    manager_with_metrics.get_secret("test-arn")

        summary = manager_with_metrics.get_metrics_summary()
        read_ops = summary["operations"].get(OperationType.READ.value, {})

        assert read_ops.get("errors", 0) == 3
        assert float(read_ops.get("success_rate", "100").rstrip("%")) < 100

    # Batch operations tests
    @mock_aws
    def test_batch_get_secrets(self, manager_with_metrics):
        """Test batch secret retrieval."""
        # Create multiple secrets
        secret_ids = []
        for i in range(25):  # More than MAX_BATCH_SIZE
            arn = manager_with_metrics.store_secret(f"test_{i}", f"value_{i}")
            secret_ids.append(arn)

        # Get all secrets in batch
        results = manager_with_metrics.get_secrets_batch(secret_ids)

        assert len(results) == 25
        assert all(results[arn] == f"value_{i}" for i, arn in enumerate(secret_ids))

    @mock_aws
    def test_batch_delete_secrets(self, manager_with_metrics):
        """Test batch secret deletion."""
        # Create multiple secrets
        secret_ids = []
        for i in range(10):
            arn = manager_with_metrics.store_secret(f"test_{i}", f"value_{i}")
            secret_ids.append(arn)

        # Delete all secrets in batch
        results = manager_with_metrics.delete_secrets_batch(secret_ids)

        assert len(results) == 10
        assert all(results.values())  # All deletions should succeed

        # Verify they're deleted
        for arn in secret_ids:
            assert manager_with_metrics.get_secret(arn) is None

    # Performance tests
    @mock_aws
    def test_performance_metrics(self, manager_with_metrics):
        """Test performance metric collection."""
        manager_with_metrics.reset_metrics()

        # Perform operations with artificial delay
        with patch.object(manager_with_metrics, "_store_secret_internal") as mock_store:
            mock_store.return_value = (
                "arn:aws:secretsmanager:us-east-1:123456:secret:test"
            )

            # Simulate slow operation
            def slow_store(*args, **kwargs):
                time.sleep(0.1)  # 100ms delay
                return "arn:aws:secretsmanager:us-east-1:123456:secret:test"

            mock_store.side_effect = slow_store

            for i in range(5):
                manager_with_metrics.store_secret(f"test_{i}", "value")

        summary = manager_with_metrics.get_metrics_summary()
        create_ops = summary["operations"][OperationType.CREATE.value]
        avg_duration = float(create_ops["average_duration_ms"])

        assert avg_duration >= 100  # At least 100ms due to our delay

    # Resource cleanup tests
    @mock_aws
    def test_cleanup_on_exit(self):
        """Test that resources are cleaned up on exit."""
        config = AWSSecretManagerConfig(enable_metrics=False)
        manager = AWSSecretManager(config)

        # Access client to initialize it
        client = manager.client
        assert client is not None

        # Manually trigger cleanup
        manager._cleanup()

        # Client should be None after cleanup
        assert manager._client is None

    # Edge cases
    @mock_aws
    def test_empty_secret_name_validation(self, manager_with_metrics):
        """Test validation of empty secret names."""
        with pytest.raises(SecretValidationError) as exc_info:
            manager_with_metrics.store_secret("", "value")

        assert "Secret name cannot be empty" in str(exc_info.value)

    @mock_aws
    def test_special_characters_in_secret_name(self, manager_with_metrics):
        """Test validation of special characters in secret names."""
        invalid_names = ["test@email", "test space", "test#hash", "test!exclaim"]

        for name in invalid_names:
            with pytest.raises(SecretValidationError) as exc_info:
                manager_with_metrics.store_secret(name, "value")

            assert "Invalid secret name" in str(exc_info.value)

    @mock_aws
    def test_long_secret_name_validation(self, manager_with_metrics):
        """Test validation of long secret names."""
        long_name = "x" * 513  # Over the limit (max is 512)

        with pytest.raises(SecretValidationError) as exc_info:
            manager_with_metrics.store_secret(long_name, "value")

        assert "Secret name too long" in str(exc_info.value)
        assert "513 characters" in str(exc_info.value)
