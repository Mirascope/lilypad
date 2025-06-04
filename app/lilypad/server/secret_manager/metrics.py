"""Metrics collection for secret manager operations (non-singleton version)."""

import logging
import time
from collections.abc import Generator, Iterator
from contextlib import contextmanager, _GeneratorContextManager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from typing import Any

logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Types of secret manager operations."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    DESCRIBE = "describe"


@dataclass
class OperationMetrics:
    """Metrics for a single operation type."""

    count: int = 0
    errors: int = 0
    total_duration_ms: float = 0
    last_error: str | None = None
    last_error_time: datetime | None = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.count == 0:
            return 100.0
        return ((self.count - self.errors) / self.count) * 100

    @property
    def average_duration_ms(self) -> float:
        """Calculate average operation duration."""
        if self.count == 0:
            return 0
        return self.total_duration_ms / self.count


@dataclass
class SecretMetrics:
    """Aggregate metrics for secret manager operations."""

    operations: dict[OperationType, OperationMetrics] = field(default_factory=dict)
    total_api_calls: int = 0
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    _lock: RLock = field(default_factory=RLock)  # Use RLock for better performance

    def __post_init__(self) -> None:
        """Initialize operation metrics."""
        for op_type in OperationType:
            self.operations[op_type] = OperationMetrics()

    @contextmanager
    def measure_operation(
        self, operation: OperationType
    ) -> Generator[None, None, None]:
        """Context manager to measure operation duration and track metrics."""
        start_time = time.time()
        error_occurred = False
        error_message = None

        try:
            yield
        except Exception as e:
            error_occurred = True
            error_message = str(e)
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000

            with self._lock:
                self.total_api_calls += 1
                metrics = self.operations[operation]
                metrics.count += 1
                metrics.total_duration_ms += duration_ms

                if error_occurred:
                    metrics.errors += 1
                    metrics.last_error = error_message
                    metrics.last_error_time = datetime.now(timezone.utc)

                # Log slow operations
                from .config import AWSSecretManagerConfig

                config = AWSSecretManagerConfig()
                if duration_ms > config.SLOW_OPERATION_THRESHOLD_MS:
                    logger.warning(
                        f"Slow {operation.value} operation",
                        extra={
                            "duration_ms": duration_ms,
                            "operation": operation.value,
                        },
                    )

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of all metrics."""
        current_time = datetime.now(timezone.utc)
        uptime_seconds = (current_time - self.start_time).total_seconds()

        with self._lock:
            summary = {
                "uptime_seconds": uptime_seconds,
                "total_api_calls": self.total_api_calls,
                "api_calls_per_minute": (self.total_api_calls / uptime_seconds) * 60
                if uptime_seconds > 0
                else 0,
                "operations": {},
                "timestamp": current_time.isoformat(),
            }

            for op_type, metrics in self.operations.items():
                if metrics.count > 0:
                    summary["operations"][op_type.value] = {
                        "count": metrics.count,
                        "errors": metrics.errors,
                        "success_rate": f"{metrics.success_rate:.2f}%",
                        "average_duration_ms": f"{metrics.average_duration_ms:.2f}",
                        "last_error": metrics.last_error,
                        "last_error_time": metrics.last_error_time.isoformat()
                        if metrics.last_error_time
                        else None,
                    }

            # Calculate estimated monthly cost (AWS pricing: $0.05 per 10,000 API calls)
            estimated_monthly_cost = (
                (self.total_api_calls * 30 * 24 * 60 * 60 / uptime_seconds)
                * 0.05
                / 10000
                if uptime_seconds > 0
                else 0
            )
            summary["estimated_monthly_cost_usd"] = f"${estimated_monthly_cost:.2f}"

            return summary

    def reset(self) -> None:
        """Reset all metrics safely."""
        with self._lock:
            # Create new instances instead of calling __init__
            self.operations.clear()
            for op_type in OperationType:
                self.operations[op_type] = OperationMetrics()
            self.total_api_calls = 0
            self.start_time = datetime.now(timezone.utc)


class MetricsCollector:
    """Non-singleton metrics collector for the application."""

    def __init__(self) -> None:
        """Initialize a new metrics collector instance."""
        self.metrics = SecretMetrics()

    def measure_operation(
        self, operation: OperationType
    ) -> _GeneratorContextManager[None, None, None]:
        """Delegate to metrics instance for backward compatibility."""
        return self.metrics.measure_operation(operation)

    def get_summary(self) -> dict[str, Any]:
        """Get metrics summary."""
        return self.metrics.get_summary()

    def reset(self) -> None:
        """Reset metrics."""
        self.metrics.reset()

    def log_summary(self) -> None:
        """Log current metrics summary."""
        summary = self.metrics.get_summary()
        logger.info("Secret Manager Metrics", extra={"metrics": summary})
