"""Tests for the EE license validation module."""

import base64
import json
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, mock_open, patch
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from ee.validate import (
    LicenseError,
    LicenseInfo,
    LicenseValidator,
    Tier,
    _ensure_utc,
    generate_license,
)


class TestTier:
    """Test Tier enum."""

    def test_tier_values(self):
        """Test tier enum values."""
        assert Tier.FREE == 0
        assert Tier.PRO == 1
        assert Tier.TEAM == 2
        assert Tier.ENTERPRISE == 3

    def test_tier_from_string(self):
        """Test creating tier from string."""
        assert Tier._missing_("FREE") == Tier.FREE
        assert Tier._missing_("PRO") == Tier.PRO
        assert Tier._missing_("TEAM") == Tier.TEAM
        assert Tier._missing_("ENTERPRISE") == Tier.ENTERPRISE

    def test_tier_invalid_string(self):
        """Test creating tier from invalid string."""
        with pytest.raises(KeyError):
            Tier._missing_("INVALID")

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
    def test_license_validator_init_success(self, mock_resources):
        """Test successful LicenseValidator initialization."""
        # Create a test RSA key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        public_key = private_key.public_key()
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        # Mock file reading
        mock_file = mock_open(read_data=public_key_pem.decode())
        mock_path = Mock()
        mock_path.open.return_value.__enter__ = mock_file
        mock_path.open.return_value.__exit__ = Mock(return_value=None)
        mock_resources.return_value.joinpath.return_value = mock_path

        validator = LicenseValidator()
        assert validator.public_key is not None
        assert validator.cache_duration == 3600

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
        mock_file = mock_open(read_data="invalid key data")
        mock_path = Mock()
        mock_path.open.return_value.__enter__ = mock_file
        mock_path.open.return_value.__exit__ = Mock(return_value=None)
        mock_resources.return_value.joinpath.return_value = mock_path

        with pytest.raises(LicenseError, match="Failed to load public key"):
            LicenseValidator()

    @patch("ee.validate.resources.files")
    def test_license_validator_init_non_rsa_key(self, mock_resources):
        """Test LicenseValidator initialization with non-RSA key."""
        # Create an EC key instead of RSA
        from cryptography.hazmat.primitives.asymmetric import ec

        private_key = ec.generate_private_key(ec.SECP256R1())
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

        with pytest.raises(LicenseError, match="Public key must be an RSA key"):
            LicenseValidator()

    @patch("ee.validate.resources.files")
    def test_validate_license_cached(self, mock_resources):
        """Test license validation with cached result."""
        # Setup validator
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

    @patch("ee.validate.resources.files")
    def test_validate_license_no_license_key(self, mock_resources):
        """Test license validation when no license key is found."""
        # Setup validator
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
    def test_validate_license_refresh(self, mock_resources):
        """Test license validation with refresh=True."""
        # Setup validator
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
            customer="Old Customer",
            license_id="old-123",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            tier=Tier.PRO,
            organization_uuid=uuid4(),
        )
        validator._license_cache = cached_license
        validator._cache_timestamp = time.time()

        # Mock organization service with new license
        org_uuid = uuid4()
        mock_org_service = Mock()
        mock_org_service.get_organization_license.return_value = "new.license.key"

        # Mock verify_license to return new license
        new_license = LicenseInfo(
            customer="New Customer",
            license_id="new-123",
            expires_at=datetime.now(timezone.utc) + timedelta(days=60),
            tier=Tier.ENTERPRISE,
            organization_uuid=org_uuid,
        )

        with patch.object(validator, "verify_license", return_value=new_license):
            result = validator.validate_license(
                org_uuid, mock_org_service, refresh=True
            )
            assert result == new_license
            assert validator._license_cache == new_license


class TestVerifyLicense:
    """Test license verification functionality."""

    def _create_test_validator(self):
        """Helper to create a test validator with mock setup."""
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        with patch("ee.validate.resources.files") as mock_resources:
            mock_file = mock_open(read_data=public_key_pem.decode())
            mock_path = Mock()
            mock_path.open.return_value.__enter__ = mock_file
            mock_path.open.return_value.__exit__ = Mock(return_value=None)
            mock_resources.return_value.joinpath.return_value = mock_path

            validator = LicenseValidator()
            return validator, private_key

    def _create_valid_license_key(
        self, private_key, organization_uuid=None, expired=False
    ):
        """Helper to create a valid license key."""
        org_uuid = organization_uuid or uuid4()
        expires_at = datetime.now(timezone.utc)
        if not expired:
            expires_at += timedelta(days=30)
        else:
            expires_at -= timedelta(days=1)

        data = {
            "customer": "Test Customer",
            "license_id": "test-license-123",
            "exp": expires_at.timestamp(),
            "tier": Tier.ENTERPRISE.value,
            "organization_uuid": str(org_uuid),
        }

        data_bytes = json.dumps(data).encode("utf-8")
        signature = private_key.sign(
            data_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )

        data_b64 = base64.urlsafe_b64encode(data_bytes).rstrip(b"=").decode("ascii")
        sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")

        return f"{data_b64}.{sig_b64}", org_uuid

    def test_verify_license_valid(self):
        """Test verifying a valid license."""
        validator, private_key = self._create_test_validator()
        license_key, org_uuid = self._create_valid_license_key(private_key)

        result = validator.verify_license(license_key, org_uuid)

        assert isinstance(result, LicenseInfo)
        assert result.customer == "Test Customer"
        assert result.license_id == "test-license-123"
        assert result.tier == Tier.ENTERPRISE
        assert result.organization_uuid == org_uuid

    def test_verify_license_invalid_format(self):
        """Test verifying license with invalid format."""
        validator, _ = self._create_test_validator()

        with pytest.raises(LicenseError, match="Invalid license key format"):
            validator.verify_license("invalid_format")

    def test_verify_license_invalid_signature(self):
        """Test verifying license with invalid signature."""
        validator, private_key = self._create_test_validator()
        # Clear any cached license data
        validator._license_cache = None
        validator._cache_timestamp = None

        license_key, _ = self._create_valid_license_key(private_key)

        # Corrupt the signature by modifying it significantly
        data_part, sig_part = license_key.split(".")
        # Create a completely invalid signature instead of just changing one character
        corrupted_license = f"{data_part}.invalid_signature_that_should_never_verify"

        with pytest.raises(LicenseError):
            validator.verify_license(corrupted_license)

    def test_verify_license_invalid_json(self):
        """Test verifying license with invalid JSON data."""
        validator, private_key = self._create_test_validator()

        # Create license with invalid JSON
        invalid_data = b"invalid json data"
        signature = private_key.sign(
            invalid_data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )

        data_b64 = base64.urlsafe_b64encode(invalid_data).rstrip(b"=").decode("ascii")
        sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
        license_key = f"{data_b64}.{sig_b64}"

        with pytest.raises(LicenseError, match="Invalid license format"):
            validator.verify_license(license_key)

    def test_verify_license_organization_mismatch(self):
        """Test verifying license with organization UUID mismatch."""
        validator, private_key = self._create_test_validator()
        license_key, org_uuid = self._create_valid_license_key(private_key)

        different_org_uuid = uuid4()

        with pytest.raises(
            LicenseError, match="License key does not match organization"
        ):
            validator.verify_license(license_key, different_org_uuid)

    def test_verify_license_invalid_data_fields(self):
        """Test verifying license with invalid data fields."""
        validator, private_key = self._create_test_validator()

        # Create license with missing required fields
        data = {
            "customer": "Test Customer",
            # Missing license_id, exp, tier, organization_uuid
        }

        data_bytes = json.dumps(data).encode("utf-8")
        signature = private_key.sign(
            data_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )

        data_b64 = base64.urlsafe_b64encode(data_bytes).rstrip(b"=").decode("ascii")
        sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
        license_key = f"{data_b64}.{sig_b64}"

        with pytest.raises(LicenseError, match="Invalid license data"):
            validator.verify_license(license_key)


class TestGenerateLicense:
    """Test license generation functionality."""

    def test_generate_license_valid(self):
        """Test generating a valid license."""
        # Create a temporary private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        org_uuid = str(uuid4())

        with patch("builtins.open", mock_open(read_data=private_key_pem.decode())):
            license_key = generate_license(
                private_key_path="/fake/path/private.pem",
                password=None,
                customer="Test Customer",
                license_id="test-license-123",
                expires_at=expires_at,
                tier=Tier.ENTERPRISE,
                organization_uuid=org_uuid,
            )

        # Verify the generated license has correct format
        assert "." in license_key
        data_part, sig_part = license_key.split(".")
        assert len(data_part) > 0
        assert len(sig_part) > 0

    def test_generate_license_invalid_key_file(self):
        """Test generating license with invalid private key file."""
        with (
            patch("builtins.open", mock_open(read_data="invalid key data")),
            pytest.raises(Exception),  # Could be various crypto exceptions
        ):
            generate_license(
                private_key_path="/fake/path/private.pem",
                password=b"",
                customer="Test Customer",
                license_id="test-license-123",
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                tier=Tier.ENTERPRISE,
                organization_uuid=str(uuid4()),
            )

    def test_generate_license_non_rsa_key(self):
        """Test generating license with non-RSA private key."""
        from cryptography.hazmat.primitives.asymmetric import ec

        # Create an EC key instead of RSA
        private_key = ec.generate_private_key(ec.SECP256R1())
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        with (
            patch("builtins.open", mock_open(read_data=private_key_pem.decode())),
            pytest.raises(LicenseError, match="Private key must be an RSA key"),
        ):
            generate_license(
                private_key_path="/fake/path/private.pem",
                password=None,
                customer="Test Customer",
                license_id="test-license-123",
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                tier=Tier.ENTERPRISE,
                organization_uuid=str(uuid4()),
            )


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

    def test_cache_expiry(self):
        """Test license cache expiry."""
        with patch("ee.validate.resources.files") as mock_resources:
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

            # Create cached license info
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

    def test_verify_license_no_organization_check(self):
        """Test verifying license without organization UUID check."""
        with patch("ee.validate.resources.files") as mock_resources:
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

            # Create valid license
            org_uuid = uuid4()
            data = {
                "customer": "Test Customer",
                "license_id": "test-license-123",
                "exp": (datetime.now(timezone.utc) + timedelta(days=30)).timestamp(),
                "tier": Tier.ENTERPRISE.value,
                "organization_uuid": str(org_uuid),
            }

            data_bytes = json.dumps(data).encode("utf-8")
            signature = private_key.sign(
                data_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )

            data_b64 = base64.urlsafe_b64encode(data_bytes).rstrip(b"=").decode("ascii")
            sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
            license_key = f"{data_b64}.{sig_b64}"

            # Verify without organization check (expected_organization_uuid=None)
            result = validator.verify_license(license_key, None)
            assert isinstance(result, LicenseInfo)
            assert result.organization_uuid == org_uuid
