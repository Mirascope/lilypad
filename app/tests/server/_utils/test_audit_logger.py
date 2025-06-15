"""Tests for audit logger utility."""

from unittest.mock import Mock, patch

from lilypad.server._utils.audit_logger import AuditAction, AuditLogger


def test_audit_action_enum():
    """Test AuditAction enum values."""
    assert AuditAction.CREATE.value == "create"
    assert AuditAction.READ.value == "read"
    assert AuditAction.UPDATE.value == "update"
    assert AuditAction.DELETE.value == "delete"

    # All enum members
    assert len(AuditAction) == 4


def test_audit_logger_initialization():
    """Test AuditLogger initialization."""
    # Without session
    logger = AuditLogger()
    assert logger.session is None

    # With session
    mock_session = Mock()
    logger = AuditLogger(session=mock_session)
    assert logger.session == mock_session


@patch("lilypad.server._utils.audit_logger.audit_logger")
@patch("lilypad.server._utils.audit_logger.datetime")
def test_log_secret_access_basic(mock_datetime, mock_audit_logger):
    """Test basic secret access logging."""
    # Mock datetime
    mock_datetime.datetime.utcnow.return_value.isoformat.return_value = (
        "2024-01-01T00:00:00"
    )

    # Create logger and log access
    logger = AuditLogger()
    logger.log_secret_access(
        user_id="user123",
        action=AuditAction.READ,
        service_name="test_service",
        secret_id="secret456",
        success=True,
    )

    # Verify logging
    mock_audit_logger.info.assert_called_once()
    call_args = mock_audit_logger.info.call_args[0][0]

    assert "AUDIT:" in call_args
    assert '"timestamp": "2024-01-01T00:00:00"' in call_args
    assert '"user_id": "user123"' in call_args
    assert '"action": "read"' in call_args
    assert '"service_name": "test_service"' in call_args
    assert '"secret_id": "secret456"' in call_args
    assert '"success": true' in call_args.lower()


@patch("lilypad.server._utils.audit_logger.audit_logger")
def test_log_secret_access_with_additional_info(mock_audit_logger):
    """Test logging with additional info."""
    logger = AuditLogger()

    additional_info = {
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0",
        "request_id": "req123",
    }

    logger.log_secret_access(
        user_id="user123",
        action=AuditAction.CREATE,
        service_name="api",
        secret_id="new_secret",
        success=True,
        additional_info=additional_info,
    )

    # Verify additional info is included
    call_args = mock_audit_logger.info.call_args[0][0]
    assert '"ip_address": "192.168.1.1"' in call_args
    assert '"user_agent": "Mozilla/5.0"' in call_args
    assert '"request_id": "req123"' in call_args


@patch("lilypad.server._utils.audit_logger.audit_logger")
def test_log_secret_access_filters_sensitive_info(mock_audit_logger):
    """Test that sensitive fields are filtered from additional info."""
    logger = AuditLogger()

    additional_info = {
        "ip_address": "192.168.1.1",
        "secret": "should_not_log",
        "api_key": "should_not_log",
        "token": "should_not_log",
        "password": "should_not_log",
        "key": "should_not_log",
        "safe_field": "should_log",
    }

    logger.log_secret_access(
        user_id="user123",
        action=AuditAction.UPDATE,
        service_name="api",
        secret_id="secret789",
        success=False,
        additional_info=additional_info,
    )

    # Verify sensitive fields are filtered
    call_args = mock_audit_logger.info.call_args[0][0]
    assert "should_not_log" not in call_args
    assert '"safe_field": "should_log"' in call_args
    assert '"ip_address": "192.168.1.1"' in call_args


@patch("lilypad.server._utils.audit_logger.audit_logger")
def test_log_secret_access_failed_attempt(mock_audit_logger):
    """Test logging failed secret access."""
    logger = AuditLogger()

    logger.log_secret_access(
        user_id="attacker123",
        action=AuditAction.DELETE,
        service_name="admin_api",
        secret_id="critical_secret",
        success=False,
        additional_info={"reason": "unauthorized"},
    )

    # Verify failure is logged
    call_args = mock_audit_logger.info.call_args[0][0]
    assert '"success": false' in call_args.lower()
    assert '"reason": "unauthorized"' in call_args


def test_log_secret_access_all_actions():
    """Test logging with all action types."""
    logger = AuditLogger()

    with patch("lilypad.server._utils.audit_logger.audit_logger") as mock_audit_logger:
        # Test each action type
        for action in AuditAction:
            logger.log_secret_access(
                user_id="user123",
                action=action,
                service_name="test",
                secret_id="secret123",
                success=True,
            )

        # Should have logged 4 times
        assert mock_audit_logger.info.call_count == 4

        # Check each action was logged
        all_calls = " ".join(
            call[0][0] for call in mock_audit_logger.info.call_args_list
        )
        assert '"action": "create"' in all_calls
        assert '"action": "read"' in all_calls
        assert '"action": "update"' in all_calls
        assert '"action": "delete"' in all_calls


@patch("lilypad.server._utils.audit_logger.audit_logger")
def test_log_secret_access_empty_additional_info(mock_audit_logger):
    """Test logging with empty additional info."""
    logger = AuditLogger()

    logger.log_secret_access(
        user_id="user123",
        action=AuditAction.READ,
        service_name="api",
        secret_id="secret123",
        success=True,
        additional_info={},
    )

    # Should not include additional_info in log
    call_args = mock_audit_logger.info.call_args[0][0]
    # The log should still be valid even with empty additional_info
    assert '"user_id": "user123"' in call_args


@patch("lilypad.server._utils.audit_logger.audit_logger")
def test_log_secret_access_none_additional_info(mock_audit_logger):
    """Test logging with None additional info."""
    logger = AuditLogger()

    logger.log_secret_access(
        user_id="user123",
        action=AuditAction.READ,
        service_name="api",
        secret_id="secret123",
        success=True,
        additional_info=None,
    )

    # Should work fine without additional_info
    mock_audit_logger.info.assert_called_once()


def test_audit_logger_with_session():
    """Test that audit logger can be initialized with a session."""
    mock_session = Mock()
    logger = AuditLogger(session=mock_session)

    # Session should be stored but not used in current implementation
    assert logger.session == mock_session

    # Should still work normally
    with patch("lilypad.server._utils.audit_logger.audit_logger") as mock_audit_logger:
        logger.log_secret_access(
            user_id="user123",
            action=AuditAction.READ,
            service_name="api",
            secret_id="secret123",
            success=True,
        )

        mock_audit_logger.info.assert_called_once()
