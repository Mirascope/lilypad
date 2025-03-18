"""Audit logger for secret management operations."""

import datetime
import logging
from enum import Enum
from typing import Any

from sqlmodel import Session

# Setup dedicated audit logger
audit_logger = logging.getLogger("secrets.audit")


class AuditAction(Enum):
    """Audit action types for secret operations."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"


class AuditLogger:
    """Logger for security-sensitive operations."""

    def __init__(self, session: Session | None = None) -> None:
        """Initialize the audit logger."""
        self.session = session

    def log_secret_access(
        self,
        user_id: str,
        action: AuditAction,
        service_name: str,
        secret_id: str,
        success: bool,
        additional_info: dict[str, Any] | None = None,
    ) -> None:
        """Log access to secrets with masked values."""
        timestamp = datetime.datetime.utcnow().isoformat()

        # Never log the actual secret value
        log_data = {
            "timestamp": timestamp,
            "user_id": user_id,
            "action": action.value,
            "service_name": service_name,
            "secret_id": secret_id,
            "success": success,
        }

        if additional_info:
            # Ensure no sensitive data in additional info
            safe_info = {
                k: v
                for k, v in additional_info.items()
                if k not in ["secret", "api_key", "token", "password", "key"]
            }
            log_data["additional_info"] = safe_info

        # Log to file/stream
        audit_logger.info(f"AUDIT: {log_data}")
