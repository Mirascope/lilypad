"""Tests for the Kafka setup service."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiokafka.errors import KafkaError, TopicAlreadyExistsError

from lilypad.server.services.kafka_setup import KafkaSetupService
from lilypad.server.settings import Settings


def create_mock_settings(**overrides):
    """Create a mock Settings object with required kafka attributes."""
    mock_settings = Mock(spec=Settings)
    mock_settings.kafka_topic_span_ingestion = "span-ingestion"
    mock_settings.kafka_topic_stripe_ingestion = "stripe-ingestion"
    mock_settings.kafka_bootstrap_servers = "localhost:9092"
    mock_settings.kafka_auto_setup_topics = True
    
    # Apply any overrides
    for key, value in overrides.items():
        setattr(mock_settings, key, value)
    
    return mock_settings


class TestKafkaSetupService:
    """Test KafkaSetupService class."""

    def test_init(self):
        """Test KafkaSetupService initialization."""
        mock_settings = create_mock_settings()
        service = KafkaSetupService(mock_settings)

        assert service.settings == mock_settings
        assert service.admin_client is None

    @pytest.mark.asyncio
    async def test_setup_topics_no_kafka_servers(self):
        """Test setup_topics returns True when Kafka not configured."""
        mock_settings = create_mock_settings(kafka_bootstrap_servers=None)

        service = KafkaSetupService(mock_settings)

        with patch("lilypad.server.services.kafka_setup.logger") as mock_logger:
            result = await service.setup_topics()

        assert result is True
        mock_logger.info.assert_called_once_with(
            "Kafka not configured, skipping topic setup"
        )

    @pytest.mark.asyncio
    async def test_setup_topics_auto_setup_disabled(self):
        """Test setup_topics returns True when auto-setup disabled."""
        mock_settings = create_mock_settings(kafka_auto_setup_topics=False)

        service = KafkaSetupService(mock_settings)

        with patch("lilypad.server.services.kafka_setup.logger") as mock_logger:
            result = await service.setup_topics()

        assert result is True
        mock_logger.info.assert_called_once_with(
            "Kafka auto-setup disabled, skipping topic setup"
        )

    @pytest.mark.asyncio
    @patch("lilypad.server.services.kafka_setup.AIOKafkaAdminClient")
    async def test_setup_topics_success_new_topic(self, mock_admin_client_class):
        """Test successful topic setup with new topic creation."""
        mock_settings = create_mock_settings()

        # Mock admin client
        mock_admin_client = AsyncMock()
        mock_admin_client_class.return_value = mock_admin_client

        # Mock successful topic creation and verification
        mock_admin_client.create_topics = AsyncMock()
        mock_admin_client.describe_topics = AsyncMock(
            return_value=[
                {"topic": "span-ingestion", "partitions": [{"id": i} for i in range(6)]},
                {"topic": "stripe-ingestion", "partitions": [{"id": i} for i in range(6)]}
            ]
        )

        service = KafkaSetupService(mock_settings)

        with patch("lilypad.server.services.kafka_setup.logger") as mock_logger:
            result = await service.setup_topics()

        assert result is True
        mock_admin_client.start.assert_called_once()
        assert mock_admin_client.create_topics.call_count == 2  # Two topics created
        mock_admin_client.describe_topics.assert_called_once_with(["span-ingestion", "stripe-ingestion"])
        mock_admin_client.close.assert_called_once()

        # Check topic creation log
        mock_logger.info.assert_any_call(
            "Creating topic 'span-ingestion' with 6 partitions..."
        )
        mock_logger.info.assert_any_call("Topic 'span-ingestion' created successfully")

    @pytest.mark.asyncio
    @patch("lilypad.server.services.kafka_setup.AIOKafkaAdminClient")
    async def test_setup_topics_topic_already_exists(self, mock_admin_client_class):
        """Test topic setup when topic already exists."""
        mock_settings = create_mock_settings()

        # Mock admin client
        mock_admin_client = AsyncMock()
        mock_admin_client_class.return_value = mock_admin_client

        # Mock TopicAlreadyExistsError
        mock_admin_client.create_topics = AsyncMock(
            side_effect=TopicAlreadyExistsError("Topic exists")
        )
        mock_admin_client.describe_topics = AsyncMock(
            return_value=[
                {"topic": "span-ingestion", "partitions": [{"id": i} for i in range(6)]},
                {"topic": "stripe-ingestion", "partitions": [{"id": i} for i in range(6)]}
            ]
        )

        service = KafkaSetupService(mock_settings)

        with patch("lilypad.server.services.kafka_setup.logger") as mock_logger:
            result = await service.setup_topics()

        assert result is True
        mock_logger.info.assert_any_call("Topic 'span-ingestion' already exists")
        mock_logger.info.assert_any_call("Topic 'stripe-ingestion' already exists")

    @pytest.mark.asyncio
    @patch("lilypad.server.services.kafka_setup.AIOKafkaAdminClient")
    async def test_setup_topics_generic_already_exists_error(
        self, mock_admin_client_class
    ):
        """Test topic setup handles generic 'already exists' error."""
        mock_settings = create_mock_settings()

        # Mock admin client
        mock_admin_client = AsyncMock()
        mock_admin_client_class.return_value = mock_admin_client

        # Mock generic error with "already exists" message
        mock_admin_client.create_topics = AsyncMock(
            side_effect=Exception("Topic already exists")
        )
        mock_admin_client.describe_topics = AsyncMock(
            return_value=[
                {"topic": "span-ingestion", "partitions": [{"id": i} for i in range(6)]},
                {"topic": "stripe-ingestion", "partitions": [{"id": i} for i in range(6)]}
            ]
        )

        service = KafkaSetupService(mock_settings)

        with patch("lilypad.server.services.kafka_setup.logger") as mock_logger:
            result = await service.setup_topics()

        assert result is True
        mock_logger.info.assert_any_call("Topic 'span-ingestion' already exists")
        mock_logger.info.assert_any_call("Topic 'stripe-ingestion' already exists")

    @pytest.mark.asyncio
    @patch("lilypad.server.services.kafka_setup.AIOKafkaAdminClient")
    async def test_setup_topics_create_topic_error(self, mock_admin_client_class):
        """Test topic setup handles topic creation error."""
        mock_settings = create_mock_settings()

        # Mock admin client
        mock_admin_client = AsyncMock()
        mock_admin_client_class.return_value = mock_admin_client

        # Mock topic creation error
        mock_admin_client.create_topics = AsyncMock(
            side_effect=Exception("Creation failed")
        )

        service = KafkaSetupService(mock_settings)

        with patch("lilypad.server.services.kafka_setup.logger") as mock_logger:
            result = await service.setup_topics()

        assert result is False  # Returns False when all topics fail to create
        mock_logger.error.assert_called()

    @pytest.mark.asyncio
    @patch("lilypad.server.services.kafka_setup.AIOKafkaAdminClient")
    async def test_setup_topics_connection_retry_success(self, mock_admin_client_class):
        """Test topic setup succeeds after connection retry."""
        mock_settings = create_mock_settings()

        # Mock admin client
        mock_admin_client = AsyncMock()
        # First start fails, second succeeds
        mock_admin_client.start.side_effect = [Exception("Connection failed"), None]
        mock_admin_client_class.return_value = mock_admin_client

        # Mock successful operations after connection
        mock_admin_client.create_topics = AsyncMock()
        mock_admin_client.describe_topics = AsyncMock(
            return_value=[
                {"topic": "span-ingestion", "partitions": [{"id": i} for i in range(6)]},
                {"topic": "stripe-ingestion", "partitions": [{"id": i} for i in range(6)]}
            ]
        )

        service = KafkaSetupService(mock_settings)

        with (
            patch("asyncio.sleep"),
            patch("lilypad.server.services.kafka_setup.logger") as mock_logger,
        ):
            result = await service.setup_topics()

        assert result is True
        assert mock_admin_client.start.call_count == 2
        mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    @patch("lilypad.server.services.kafka_setup.AIOKafkaAdminClient")
    async def test_setup_topics_connection_max_retries_exceeded(
        self, mock_admin_client_class
    ):
        """Test topic setup fails after max retries exceeded."""
        mock_settings = create_mock_settings()

        # Mock admin client
        mock_admin_client = AsyncMock()
        mock_admin_client.start.side_effect = Exception("Connection failed")
        mock_admin_client_class.return_value = mock_admin_client

        service = KafkaSetupService(mock_settings)

        with (
            patch("asyncio.sleep"),
            patch("lilypad.server.services.kafka_setup.logger") as mock_logger,
        ):
            result = await service.setup_topics()

        assert result is False
        assert mock_admin_client.start.call_count == 5  # Max retries
        mock_logger.error.assert_called()

    @pytest.mark.asyncio
    @patch("lilypad.server.services.kafka_setup.AIOKafkaAdminClient")
    async def test_setup_topics_admin_client_not_initialized(
        self, mock_admin_client_class
    ):
        """Test topic setup handles admin client not being initialized."""
        mock_settings = create_mock_settings()

        # Mock admin client that doesn't get set (causes AttributeError during start)
        mock_admin_client_class.return_value = None

        service = KafkaSetupService(mock_settings)

        with (
            patch("lilypad.server.services.kafka_setup.logger") as mock_logger,
            patch("asyncio.sleep")  # Mock sleep to prevent delays
        ):
            result = await service.setup_topics()

        assert result is False
        # The actual error message when admin client is None
        mock_logger.error.assert_called_with(
            "Failed to connect to Kafka after 5 attempts: 'NoneType' object has no attribute 'start'"
        )

    @pytest.mark.asyncio
    @patch("lilypad.server.services.kafka_setup.AIOKafkaAdminClient")
    async def test_setup_topics_describe_topics_failure(self, mock_admin_client_class):
        """Test topic setup handles describe_topics failure."""
        mock_settings = create_mock_settings()

        # Mock admin client
        mock_admin_client = AsyncMock()
        mock_admin_client_class.return_value = mock_admin_client

        # Mock successful creation but failed verification
        mock_admin_client.create_topics = AsyncMock()
        mock_admin_client.describe_topics = AsyncMock(
            side_effect=Exception("Describe failed")
        )

        service = KafkaSetupService(mock_settings)

        with patch("lilypad.server.services.kafka_setup.logger") as mock_logger:
            result = await service.setup_topics()

        assert result is True  # Still succeeds (verification is non-critical)
        mock_logger.warning.assert_called_with(
            "Failed to verify topics: Describe failed"
        )

    @pytest.mark.asyncio
    @patch("lilypad.server.services.kafka_setup.AIOKafkaAdminClient")
    async def test_setup_topics_object_based_topic_metadata(
        self, mock_admin_client_class
    ):
        """Test topic setup handles object-based topic metadata response."""
        mock_settings = create_mock_settings()

        # Mock admin client
        mock_admin_client = AsyncMock()
        mock_admin_client_class.return_value = mock_admin_client

        # Mock object-based topic metadata
        mock_topic_metadata = Mock()
        mock_topic_metadata.topic = "span-ingestion"
        mock_topic_metadata.partitions = [Mock() for _ in range(6)]
        
        mock_stripe_topic_metadata = Mock()
        mock_stripe_topic_metadata.topic = "stripe-ingestion"
        mock_stripe_topic_metadata.partitions = [Mock() for _ in range(6)]

        mock_admin_client.create_topics = AsyncMock()
        mock_admin_client.describe_topics = AsyncMock(
            return_value=[mock_topic_metadata, mock_stripe_topic_metadata]
        )

        service = KafkaSetupService(mock_settings)

        with patch("lilypad.server.services.kafka_setup.logger") as mock_logger:
            result = await service.setup_topics()

        assert result is True
        # Object-based metadata is no longer processed, only dict-based
        # So these topics will show as "not found in metadata"
        mock_logger.warning.assert_any_call(
            "⚠ Topic 'span-ingestion' verification failed - not found in metadata"
        )
        mock_logger.warning.assert_any_call(
            "⚠ Topic 'stripe-ingestion' verification failed - not found in metadata"
        )

    @pytest.mark.asyncio
    @patch("lilypad.server.services.kafka_setup.AIOKafkaAdminClient")
    async def test_setup_topics_no_metadata_returned(self, mock_admin_client_class):
        """Test topic setup handles no metadata returned."""
        mock_settings = create_mock_settings()

        # Mock admin client
        mock_admin_client = AsyncMock()
        mock_admin_client_class.return_value = mock_admin_client

        # Mock empty metadata response
        mock_admin_client.create_topics = AsyncMock()
        mock_admin_client.describe_topics = AsyncMock(return_value=[])

        service = KafkaSetupService(mock_settings)

        with patch("lilypad.server.services.kafka_setup.logger") as mock_logger:
            result = await service.setup_topics()

        assert result is True
        # When empty metadata is returned, the topics are logged as "not found in metadata"
        mock_logger.warning.assert_any_call(
            "⚠ Topic 'span-ingestion' verification failed - not found in metadata"
        )
        mock_logger.warning.assert_any_call(
            "⚠ Topic 'stripe-ingestion' verification failed - not found in metadata"
        )

    @pytest.mark.asyncio
    @patch("lilypad.server.services.kafka_setup.AIOKafkaAdminClient")
    async def test_setup_topics_dict_metadata_name_mismatch(
        self, mock_admin_client_class
    ):
        """Test topic setup handles dict metadata with name mismatch."""
        mock_settings = create_mock_settings()

        # Mock admin client
        mock_admin_client = AsyncMock()
        mock_admin_client_class.return_value = mock_admin_client

        # Mock dict metadata with wrong name
        mock_admin_client.create_topics = AsyncMock()
        mock_admin_client.describe_topics = AsyncMock(
            return_value=[
                {
                    "topic": "wrong-topic-name",
                    "partitions": [{"id": i} for i in range(6)],
                },
                {
                    "topic": "another-wrong-name",
                    "partitions": [{"id": i} for i in range(6)],
                }
            ]
        )

        service = KafkaSetupService(mock_settings)

        with patch("lilypad.server.services.kafka_setup.logger") as mock_logger:
            result = await service.setup_topics()

        assert result is True
        # The wrong topic names are logged as "Unexpected topic", then 
        # the expected topics are logged as "not found in metadata"
        mock_logger.warning.assert_any_call(
            "⚠ Unexpected topic 'wrong-topic-name' in metadata"
        )
        mock_logger.warning.assert_any_call(
            "⚠ Unexpected topic 'another-wrong-name' in metadata"
        )
        mock_logger.warning.assert_any_call(
            "⚠ Topic 'span-ingestion' verification failed - not found in metadata"
        )
        mock_logger.warning.assert_any_call(
            "⚠ Topic 'stripe-ingestion' verification failed - not found in metadata"
        )

    @pytest.mark.asyncio
    @patch("lilypad.server.services.kafka_setup.AIOKafkaAdminClient")
    async def test_setup_topics_object_metadata_format_mismatch(
        self, mock_admin_client_class
    ):
        """Test topic setup handles object metadata format mismatch."""
        mock_settings = create_mock_settings()

        # Mock admin client
        mock_admin_client = AsyncMock()
        mock_admin_client_class.return_value = mock_admin_client

        # Mock object without expected attributes
        mock_topic_metadata = Mock()
        del mock_topic_metadata.topic  # Remove attribute

        mock_admin_client.create_topics = AsyncMock()
        mock_admin_client.describe_topics = AsyncMock(
            return_value=[mock_topic_metadata]
        )

        service = KafkaSetupService(mock_settings)

        with patch("lilypad.server.services.kafka_setup.logger") as mock_logger:
            result = await service.setup_topics()

        assert result is True
        mock_logger.warning.assert_any_call(
            "⚠ Topic 'span-ingestion' verification failed - not found in metadata"
        )
        mock_logger.warning.assert_any_call(
            "⚠ Topic 'stripe-ingestion' verification failed - not found in metadata"
        )

    @pytest.mark.asyncio
    @patch("lilypad.server.services.kafka_setup.AIOKafkaAdminClient")
    async def test_setup_topics_kafka_error(self, mock_admin_client_class):
        """Test topic setup handles KafkaError gracefully."""
        mock_settings = create_mock_settings()

        # Mock admin client
        mock_admin_client = AsyncMock()
        mock_admin_client_class.return_value = mock_admin_client

        # Mock KafkaError in _create_all_topics method (after connection succeeds)
        # This is a different error path - the error occurs in _create_all_topics
        async def mock_create_all_topics():
            raise KafkaError("Kafka error")

        service = KafkaSetupService(mock_settings)
        service._create_all_topics = mock_create_all_topics

        with patch("lilypad.server.services.kafka_setup.logger") as mock_logger:
            result = await service.setup_topics()

        assert result is True  # Non-fatal error (exception caught)
        mock_logger.error.assert_called_with(
            "Kafka setup error (non-fatal): KafkaError: Kafka error"
        )

    @pytest.mark.asyncio
    @patch("lilypad.server.services.kafka_setup.AIOKafkaAdminClient")
    async def test_setup_topics_unexpected_error(self, mock_admin_client_class):
        """Test topic setup handles unexpected error gracefully."""
        mock_settings = create_mock_settings()

        # Mock admin client
        mock_admin_client = AsyncMock()
        mock_admin_client_class.return_value = mock_admin_client

        # Mock unexpected error in _create_all_topics method (after connection succeeds)
        async def mock_create_all_topics():
            raise RuntimeError("Unexpected error")

        service = KafkaSetupService(mock_settings)
        service._create_all_topics = mock_create_all_topics

        with patch("lilypad.server.services.kafka_setup.logger") as mock_logger:
            result = await service.setup_topics()

        assert result is True  # Non-fatal error (exception caught)
        mock_logger.error.assert_called_with(
            "Unexpected error during Kafka setup (non-fatal): Unexpected error",
            exc_info=True,
        )

    @pytest.mark.asyncio
    @patch("lilypad.server.services.kafka_setup.AIOKafkaAdminClient")
    async def test_setup_topics_admin_client_close_exception(
        self, mock_admin_client_class
    ):
        """Test topic setup handles admin client close exception gracefully."""
        mock_settings = create_mock_settings()

        # Mock admin client
        mock_admin_client = AsyncMock()
        mock_admin_client_class.return_value = mock_admin_client

        # Mock successful operations but close failure
        mock_admin_client.create_topics = AsyncMock()
        mock_admin_client.describe_topics = AsyncMock(
            return_value=[
                {"topic": "span-ingestion", "partitions": [{"id": i} for i in range(6)]},
                {"topic": "stripe-ingestion", "partitions": [{"id": i} for i in range(6)]}
            ]
        )
        mock_admin_client.close.side_effect = Exception("Close failed")

        service = KafkaSetupService(mock_settings)

        with patch("lilypad.server.services.kafka_setup.logger"):
            result = await service.setup_topics()

        # Should still succeed despite close failure (suppressed)
        assert result is True

    @pytest.mark.asyncio
    async def test_setup_topics_new_topic_configuration(self):
        """Test that NewTopic is created with correct configuration."""
        mock_settings = create_mock_settings()

        service = KafkaSetupService(mock_settings)

        with patch(
            "lilypad.server.services.kafka_setup.AIOKafkaAdminClient"
        ) as mock_admin_class:
            mock_admin_client = AsyncMock()
            mock_admin_class.return_value = mock_admin_client
            mock_admin_client.describe_topics = AsyncMock(
                return_value=[
                    {
                        "topic": "span-ingestion",
                        "partitions": [{"id": i} for i in range(6)],
                    },
                    {
                        "topic": "stripe-ingestion",
                        "partitions": [{"id": i} for i in range(6)],
                    }
                ]
            )

            with (
                patch("lilypad.server.services.kafka_setup.NewTopic") as mock_new_topic,
                patch("lilypad.server.services.kafka_setup.logger"),
            ):
                await service.setup_topics()

        # Verify NewTopic was called with correct parameters for both topics
        assert mock_new_topic.call_count == 2
        mock_new_topic.assert_any_call(
            name="span-ingestion",
            num_partitions=6,
            replication_factor=1,
            topic_configs={
                "retention.ms": "604800000",  # 7 days
                "retention.bytes": "1073741824",  # 1GB
            },
        )
        mock_new_topic.assert_any_call(
            name="stripe-ingestion",
            num_partitions=6,
            replication_factor=1,
            topic_configs={
                "retention.ms": "604800000",  # 7 days
                "retention.bytes": "1073741824",  # 1GB
            },
        )
    @pytest.mark.asyncio
    async def test_setup_topics_admin_client_unset_after_connect(self):
        """`setup_topics` should log and return False when admin_client is None after the retry loop."""
        mock_settings = create_mock_settings()

        service = KafkaSetupService(mock_settings)

        async def _start_and_unset() -> None:  # noqa: D401
            service.admin_client = None  # wipe out the reference created in the loop

        mock_admin_client = AsyncMock()
        mock_admin_client.start.side_effect = _start_and_unset

        with (
            patch(
                "lilypad.server.services.kafka_setup.AIOKafkaAdminClient",
                return_value=mock_admin_client,
            ),
            patch("lilypad.server.services.kafka_setup.logger") as mock_logger,
        ):
            result = await service.setup_topics()

        assert result is False
        mock_logger.error.assert_called_once_with("Admin client is not initialized")
