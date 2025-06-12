"""Simple tests for EE license validation to improve coverage."""

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from ee.validate import (
    LicenseError,
    LicenseInfo,
    LicenseValidator,
    Tier,
    _ensure_utc,
)


class TestTier:
    """Test Tier enum."""

    def test_tier_values(self):
        """Test tier enum values."""
        assert Tier.FREE == 0
        assert Tier.PRO == 1
        assert Tier.TEAM == 2
        assert Tier.ENTERPRISE == 3

    def test_tier_from_string_valid(self):
        """Test creating tier from valid string."""
        assert Tier._missing_("FREE") == Tier.FREE
        assert Tier._missing_("PRO") == Tier.PRO
        assert Tier._missing_("TEAM") == Tier.TEAM
        assert Tier._missing_("ENTERPRISE") == Tier.ENTERPRISE

    def test_tier_invalid_type(self):
        """Test creating tier from invalid type."""
        with pytest.raises(ValueError):
            Tier._missing_(3.14)

    def test_tier_json_schema(self):
        """Test tier JSON schema generation."""
        # Mock core schema and handler
        mock_core_schema = Mock()
        mock_handler = Mock()
        mock_handler.return_value = {"type": "integer"}
        mock_handler.resolve_ref_schema.return_value = {"type": "integer"}

        result = Tier.__get_pydantic_json_schema__(mock_core_schema, mock_handler)

        assert "x-enum-varnames" in result
        assert result["x-enum-varnames"] == ["FREE", "PRO", "TEAM", "ENTERPRISE"]


class TestEnsureUtc:
    """Test _ensure_utc utility function."""

    def test_ensure_utc_naive_datetime(self):
        """Test ensuring UTC with naive datetime."""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = _ensure_utc(dt)
        assert result.tzinfo == timezone.utc
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1

    def test_ensure_utc_aware_datetime(self):
        """Test ensuring UTC with timezone-aware datetime."""
        # Create datetime in EST (UTC-5)
        est = timezone(timedelta(hours=-5))
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=est)

        result = _ensure_utc(dt)
        assert result.tzinfo == timezone.utc
        # Should be converted to 17:00 UTC
        assert result.hour == 17

    def test_ensure_utc_already_utc(self):
        """Test ensuring UTC with already UTC datetime."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = _ensure_utc(dt)
        assert result.tzinfo == timezone.utc
        assert result == dt


class TestLicenseInfo:
    """Test LicenseInfo model."""

    def test_license_info_creation(self):
        """Test creating LicenseInfo."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        org_uuid = uuid4()

        license_info = LicenseInfo(
            customer="Test Customer",
            license_id="test-license-123",
            expires_at=expires_at,
            tier=Tier.ENTERPRISE,
            organization_uuid=org_uuid,
        )

        assert license_info.customer == "Test Customer"
        assert license_info.license_id == "test-license-123"
        assert license_info.expires_at == expires_at
        assert license_info.tier == Tier.ENTERPRISE
        assert license_info.organization_uuid == org_uuid

    def test_license_info_is_expired_false(self):
        """Test license that is not expired."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        license_info = LicenseInfo(
            customer="Test Customer",
            license_id="test-license-123",
            expires_at=expires_at,
            tier=Tier.ENTERPRISE,
            organization_uuid=uuid4(),
        )

        assert not license_info.is_expired

    def test_license_info_is_expired_true(self):
        """Test license that is expired."""
        expires_at = datetime.now(timezone.utc) - timedelta(days=1)

        license_info = LicenseInfo(
            customer="Test Customer",
            license_id="test-license-123",
            expires_at=expires_at,
            tier=Tier.ENTERPRISE,
            organization_uuid=uuid4(),
        )

        assert license_info.is_expired

    def test_license_info_none_organization_uuid(self):
        """Test license with None organization UUID."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        license_info = LicenseInfo(
            customer="Test Customer",
            license_id="test-license-123",
            expires_at=expires_at,
            tier=Tier.ENTERPRISE,
            organization_uuid=None,
        )

        assert license_info.organization_uuid is None


class TestLicenseValidator:
    """Test LicenseValidator class."""

    @patch("ee.validate.resources.files")
    def test_license_validator_init_file_not_found(self, mock_resources):
        """Test LicenseValidator initialization with missing file."""
        mock_resources.return_value.joinpath.return_value.open.side_effect = (
            FileNotFoundError("File not found")
        )

        with pytest.raises(LicenseError, match="Failed to load public key"):
            LicenseValidator()

    @patch("ee.validate.resources.files")
    def test_license_validator_init_invalid_key(self, mock_resources):
        """Test LicenseValidator initialization with invalid key."""
        # Mock file reading with invalid key data
        from unittest.mock import mock_open

        mock_file = mock_open(read_data="invalid key data")
        mock_path = Mock()
        mock_path.open.return_value.__enter__ = mock_file
        mock_path.open.return_value.__exit__ = Mock(return_value=None)
        mock_resources.return_value.joinpath.return_value = mock_path

        with pytest.raises(LicenseError, match="Failed to load public key"):
            LicenseValidator()

    @patch("ee.validate.resources.files")
    def test_license_validator_cache_properties(self, mock_resources):
        """Test LicenseValidator cache properties."""
        # Mock successful initialization
        from unittest.mock import mock_open

        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        # Create a real RSA key for testing
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        public_key = private_key.public_key()

        # Use private_bytes_raw for public key serialization
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        mock_file = mock_open(read_data=public_key_pem.decode())
        mock_path = Mock()
        mock_path.open.return_value.__enter__ = mock_file
        mock_path.open.return_value.__exit__ = Mock(return_value=None)
        mock_resources.return_value.joinpath.return_value = mock_path

        validator = LicenseValidator()

        # Test cache properties
        assert validator._license_cache is None
        assert validator._cache_timestamp is None
        assert validator.cache_duration == 3600

    @patch("ee.validate.resources.files")
    def test_validate_license_no_license_key(self, mock_resources):
        """Test license validation when no license key is found."""
        # Mock successful validator initialization
        from unittest.mock import mock_open

        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        mock_file = mock_open(read_data=public_key_pem.decode())
        mock_path = Mock()
        mock_path.open.return_value.__enter__ = mock_file
        mock_path.open.return_value.__exit__ = Mock(return_value=None)
        mock_resources.return_value.joinpath.return_value = mock_path

        validator = LicenseValidator()

        # Mock organization service returning no license
        org_uuid = uuid4()
        mock_org_service = Mock()
        mock_org_service.get_organization_license.return_value = None

        result = validator.validate_license(org_uuid, mock_org_service)
        assert result is None
        assert validator._license_cache is None

    @patch("ee.validate.resources.files")
    def test_validate_license_cached(self, mock_resources):
        """Test license validation with cached result."""
        # Mock successful validator initialization
        from unittest.mock import mock_open

        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        mock_file = mock_open(read_data=public_key_pem.decode())
        mock_path = Mock()
        mock_path.open.return_value.__enter__ = mock_file
        mock_path.open.return_value.__exit__ = Mock(return_value=None)
        mock_resources.return_value.joinpath.return_value = mock_path

        validator = LicenseValidator()

        # Create cached license info
        cached_license = LicenseInfo(
            customer="Test Customer",
            license_id="test-123",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            tier=Tier.ENTERPRISE,
            organization_uuid=uuid4(),
        )
        validator._license_cache = cached_license
        validator._cache_timestamp = time.time()

        # Mock organization service
        org_uuid = uuid4()
        mock_org_service = Mock()

        # Should return cached result
        result = validator.validate_license(org_uuid, mock_org_service)
        assert result == cached_license
        mock_org_service.get_organization_license.assert_not_called()

    def test_verify_license_invalid_format(self):
        """Test verifying license with invalid format."""
        # Create a mock validator without proper initialization
        validator = LicenseValidator.__new__(LicenseValidator)
        validator.public_key = Mock()

        with pytest.raises(LicenseError, match="Invalid license key format"):
            validator.verify_license("invalid_format")

    def test_verify_license_malformed_key(self):
        """Test verifying license with malformed key parts."""
        validator = LicenseValidator.__new__(LicenseValidator)
        validator.public_key = Mock()

        # Key with correct format but invalid base64
        with pytest.raises(LicenseError, match="Invalid license key format"):
            validator.verify_license("invalid_base64!.also_invalid!")


class TestLicenseError:
    """Test LicenseError exception."""

    def test_license_error_creation(self):
        """Test creating LicenseError."""
        error = LicenseError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_license_error_inheritance(self):
        """Test LicenseError inheritance."""
        error = LicenseError("Test error")
        assert isinstance(error, Exception)

        # Can be caught as Exception
        try:
            raise error
        except Exception as e:
            assert isinstance(e, LicenseError)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_tier_int_enum_behavior(self):
        """Test Tier as integer enum."""
        # Test that Tier can be used as integer
        assert int(Tier.FREE) == 0
        assert int(Tier.PRO) == 1
        assert int(Tier.TEAM) == 2
        assert int(Tier.ENTERPRISE) == 3

        # Test comparison
        assert Tier.FREE < Tier.PRO
        assert Tier.ENTERPRISE > Tier.FREE

    def test_license_info_with_different_tiers(self):
        """Test LicenseInfo with different tier values."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        for tier in [Tier.FREE, Tier.PRO, Tier.TEAM, Tier.ENTERPRISE]:
            license_info = LicenseInfo(
                customer="Test Customer",
                license_id=f"test-{tier.name}",
                expires_at=expires_at,
                tier=tier,
                organization_uuid=uuid4(),
            )
            assert license_info.tier == tier

    def test_ensure_utc_edge_cases(self):
        """Test _ensure_utc with edge cases."""
        # Test with very old date
        old_dt = datetime(1970, 1, 1, 0, 0, 0)
        result = _ensure_utc(old_dt)
        assert result.tzinfo == timezone.utc

        # Test with future date
        future_dt = datetime(2100, 12, 31, 23, 59, 59)
        result = _ensure_utc(future_dt)
        assert result.tzinfo == timezone.utc

    @patch("ee.validate.resources.files")
    def test_license_validator_cache_expiry(self, mock_resources):
        """Test license cache expiry behavior."""
        # Mock successful validator initialization
        from unittest.mock import mock_open

        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        mock_file = mock_open(read_data=public_key_pem.decode())
        mock_path = Mock()
        mock_path.open.return_value.__enter__ = mock_file
        mock_path.open.return_value.__exit__ = Mock(return_value=None)
        mock_resources.return_value.joinpath.return_value = mock_path

        validator = LicenseValidator()
        validator.cache_duration = 1  # 1 second cache

        # Create cached license info with old timestamp
        cached_license = LicenseInfo(
            customer="Test Customer",
            license_id="test-123",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            tier=Tier.ENTERPRISE,
            organization_uuid=uuid4(),
        )
        validator._license_cache = cached_license
        validator._cache_timestamp = time.time() - 2  # 2 seconds ago (expired)

        # Mock organization service
        org_uuid = uuid4()
        mock_org_service = Mock()
        mock_org_service.get_organization_license.return_value = None

        # Should not use expired cache
        result = validator.validate_license(org_uuid, mock_org_service)
        assert result is None
        mock_org_service.get_organization_license.assert_called_once()

    def test_license_info_model_config(self):
        """Test LicenseInfo model configuration."""
        # Test that model_config is properly set
        config = LicenseInfo.model_config
        assert config.get("json_schema_mode_override") == "serialization"
