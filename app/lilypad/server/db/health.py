"""Database health check utilities."""

import time
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from .session import db, get_async_session, get_session


def check_sync_db_health() -> dict[str, Any]:
    """Check synchronous database health."""
    start_time = time.time()

    try:
        # Try to get a connection and execute a simple query
        for session in get_session():
            result = session.execute(text("SELECT 1"))
            result.scalar()
            break

        # Get pool status
        pool_status = db.get_pool_status()

        return {
            "status": "healthy",
            "latency_ms": (time.time() - start_time) * 1000,
            "pool": pool_status.get("sync", {}),
            "error": None,
        }

    except OperationalError as e:
        return {
            "status": "unhealthy",
            "latency_ms": (time.time() - start_time) * 1000,
            "pool": None,
            "error": f"Database connection failed: {str(e)}",
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "latency_ms": (time.time() - start_time) * 1000,
            "pool": None,
            "error": f"Unexpected error: {str(e)}",
        }


async def check_async_db_health() -> dict[str, Any]:
    """Check asynchronous database health."""
    start_time = time.time()

    try:
        # Try to get a connection and execute a simple query
        async for session in get_async_session():
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            break

        # Get pool status
        pool_status = db.get_pool_status()

        return {
            "status": "healthy",
            "latency_ms": (time.time() - start_time) * 1000,
            "pool": pool_status.get("async", {}),
            "error": None,
        }

    except OperationalError as e:
        return {
            "status": "unhealthy",
            "latency_ms": (time.time() - start_time) * 1000,
            "pool": None,
            "error": f"Database connection failed: {str(e)}",
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "latency_ms": (time.time() - start_time) * 1000,
            "pool": None,
            "error": f"Unexpected error: {str(e)}",
        }


def check_pool_health() -> dict[str, Any]:
    """Check connection pool health and usage."""
    from ..settings import get_settings

    settings = get_settings()
    pool_status = db.get_pool_status()

    warnings = []

    # Check sync pool
    if "sync" in pool_status and pool_status["sync"]:
        sync_pool = pool_status["sync"]
        if sync_pool.get("size") and sync_pool.get("overflow"):
            usage = sync_pool["size"] + sync_pool["overflow"]
            max_allowed = settings.db_pool_size + settings.db_max_overflow
            usage_percent = (usage / max_allowed) * 100

            if usage_percent > 80:
                warnings.append(f"Sync pool usage high: {usage_percent:.1f}%")

    # Check async pool
    if "async" in pool_status and pool_status["async"]:
        async_pool = pool_status["async"]
        if async_pool.get("size") and async_pool.get("overflow"):
            usage = async_pool["size"] + async_pool["overflow"]
            max_allowed = settings.db_pool_size + settings.db_max_overflow
            usage_percent = (usage / max_allowed) * 100

            if usage_percent > 80:
                warnings.append(f"Async pool usage high: {usage_percent:.1f}%")

    # Check total connections across all workers
    total_connections = settings.worker_count * (
        settings.db_pool_size + settings.db_max_overflow
    )
    if total_connections > settings.db_max_connections * 0.9:
        warnings.append(
            f"Total connections ({total_connections}) approaching database limit ({settings.db_max_connections})"
        )

    return {
        "pool_status": pool_status,
        "configuration": {
            "workers": settings.worker_count,
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
            "total_per_worker": settings.db_pool_size + settings.db_max_overflow,
            "total_all_workers": total_connections,
            "db_max_connections": settings.db_max_connections,
        },
        "warnings": warnings,
        "healthy": len(warnings) == 0,
    }
