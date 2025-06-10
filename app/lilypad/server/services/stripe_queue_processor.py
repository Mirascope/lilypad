"""Stripe Queue Processor service for consuming span_counts from Kafka."""

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from ..settings import get_settings

logger = logging.getLogger(__name__)


class StripeQueueProcessor:
    """Service for processing span_counts from Kafka queue"""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.consumer: AIOKafkaConsumer | None = None
        self._running = False
        self._cleanup_task: asyncio.Task | None = None
        self._process_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()  # Async lock for thread-safe access
        # Thread pool for synchronous database operations
        self._executor = ThreadPoolExecutor(
            max_workers=self.settings.kafka_db_thread_pool_size,
            thread_name_prefix="kafka-span-db-worker",
        )
        logger.info(
            f"Initialized Kafka processor thread pool with {self.settings.kafka_db_thread_pool_size} workers "
            f"for non-blocking DB operations"
        )

    async def initialize(self) -> bool:
        """Initialize Kafka consumer with retry logic."""
        logger.info("[INIT] Starting Kafka consumer initialization")
        logger.info(
            f"[INIT] Bootstrap servers: {self.settings.kafka_bootstrap_servers}"
        )
        logger.info(f"[INIT] Topic: {self.settings.kafka_topic_span_ingestion}")
        logger.info(f"[INIT] Consumer group: {self.settings.kafka_consumer_group}")

        if not self.settings.kafka_bootstrap_servers:
            logger.warning(
                "Kafka not configured (kafka_bootstrap_servers is None), queue processor disabled"
            )
            return False

        # Retry logic for Kafka initialization
        max_retries = 5
        retry_delay = 2  # Start with 2 seconds

        for attempt in range(max_retries):
            try:
                self.consumer = AIOKafkaConsumer(
                    self.settings.kafka_topic_span_ingestion,
                    bootstrap_servers=self.settings.kafka_bootstrap_servers,
                    group_id=self.settings.kafka_consumer_group,
                    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                    key_deserializer=lambda k: k.decode("utf-8") if k else None,
                    enable_auto_commit=True,
                    auto_offset_reset="earliest",
                    max_poll_records=100,
                    session_timeout_ms=30000,
                    heartbeat_interval_ms=10000,
                    retry_backoff_ms=100,
                    request_timeout_ms=40000,  # Increased timeout
                    connections_max_idle_ms=540000,
                )
                logger.info(f"[INIT] Attempt {attempt + 1}: Starting consumer...")
                await self.consumer.start()
                logger.info("[INIT] Consumer started successfully")
                logger.info(
                    f"✅ Kafka consumer initialized - Topic: {self.settings.kafka_topic_span_ingestion}, Group: {self.settings.kafka_consumer_group}"
                )
                return True

            except Exception as e:
                if (
                    "GroupCoordinatorNotAvailableError" in str(e)
                    and attempt < max_retries - 1
                ):
                    logger.warning(
                        f"Kafka not ready yet (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {retry_delay} seconds: {e}"
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(
                        f"Failed to initialize Kafka consumer after {attempt + 1} attempts: {e}"
                    )
                    return False

        return False

    async def start(self) -> None:
        """Start the queue processor."""
        logger.info("[START] Beginning span queue processor startup")
        logger.info("🚀 Starting span queue processor - checking for messages...")

        logger.info("[START] Calling initialize()")
        init_result = await self.initialize()
        logger.info(f"[START] Initialize result: {init_result}")

        if not init_result:
            logger.warning(
                "[START] Queue processor not started due to initialization failure"
            )
            return

        logger.info("[START] Setting _running to True")
        self._running = True

        # Start processing task
        logger.info("[START] Creating processing task")
        self._process_task = asyncio.create_task(self._process_queue())
        logger.info("🔄 Processing task started")

        logger.info("[START] All tasks created")
        logger.info("✅ Queue processor fully started - waiting for messages")

    async def stop(self) -> None:
        """Stop the queue processor."""
        logger.info("Stopping queue processor...")
        self._running = False

        # Cancel and wait for cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            logger.info("Cancelling cleanup task...")
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                logger.info("Cleanup task cancelled successfully")
                pass

        # Cancel and wait for process task
        if self._process_task and not self._process_task.done():
            logger.info("Cancelling process task...")
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                logger.info("Process task cancelled successfully")
                pass

        # Stop the consumer
        if self.consumer:
            logger.info("Stopping Kafka consumer...")
            try:
                await self.consumer.stop()
                logger.info("Kafka consumer stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping Kafka consumer: {e}")

        # Shutdown thread pool executor
        logger.info("Shutting down thread pool executor...")
        self._executor.shutdown(wait=True, cancel_futures=False)

        logger.info("Queue processor stopped - processed messages until shutdown")

    async def _process_queue(self) -> None:
        """Main queue processing loop."""
        logger.info("[QUEUE] Entering _process_queue method")
        logger.info("🔄 Starting queue processing loop - polling for messages...")
        poll_count = 0
        logger.info(f"[QUEUE] _running status: {self._running}")
        while self._running:
            try:
                # Fetch messages with timeout
                if poll_count == 0:
                    logger.info("[QUEUE] First poll - calling getmany()")
                records = await self.consumer.getmany(timeout_ms=1000, max_records=100)  # pyright: ignore [reportOptionalMemberAccess]

                poll_count += 1
                if records:
                    msg_count = sum(len(msgs) for msgs in records.values())
                    logger.info(f"📦 Received {msg_count} messages from Kafka queue")
                else:
                    # Log every 10th poll to show it's alive
                    if poll_count % 10 == 0:
                        logger.info(
                            f"🔍 Polling for messages... (poll #{poll_count}, no messages yet)"
                        )

            except KafkaError as e:
                logger.debug(f"Kafka error in processing loop: {e}")
                await asyncio.sleep(5)  # Back off on error
            except Exception as e:
                logger.debug(f"Unexpected error in processing loop: {e}")
                await asyncio.sleep(5)


# Singleton instance
_stripe_processor_instance: StripeQueueProcessor | None = None


def get_stripe_queue_processor() -> StripeQueueProcessor:
    """Get or create the singleton StripeQueueProcessor instance."""
    global _stripe_processor_instance
    if _stripe_processor_instance is None:
        _stripe_processor_instance = StripeQueueProcessor()
    return _stripe_processor_instance
