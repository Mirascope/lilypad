"""License validation module for LilyPad Enterprise Edition"""

import base64
import functools
import json
import os
import time
from collections.abc import Callable
from datetime import datetime
from importlib import resources
from typing import ParamSpec, TypeVar

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from pydantic import BaseModel, ValidationError, field_validator

_P = ParamSpec("_P")
_R = TypeVar("_R")


class LicenseError(Exception):
    """Custom exception for license-related errors"""

    pass


class LicenseInfo(BaseModel):
    """Pydantic model for license validation"""

    customer: str
    license_id: str
    expires_at: datetime

    @field_validator("expires_at")
    def must_not_be_expired(cls, expires_at: datetime) -> datetime:
        """Validate that the license hasn't expired"""
        if expires_at <= datetime.now():
            raise ValueError("License has expired")
        return expires_at


class LicenseValidator:
    """Class for validating licenses"""

    public_key: rsa.RSAPublicKey

    def __init__(self) -> None:
        """Initialize the validator with a public key for license verification"""
        try:
            with resources.files("lilypad.ee").joinpath("key.pub.pem").open("r") as f:
                public_key_data = f.read()
                key = serialization.load_pem_public_key(
                    public_key_data.encode(), backend=default_backend()
                )
                if not isinstance(key, rsa.RSAPublicKey):
                    raise LicenseError("Public key must be an RSA key")
                self.public_key = key
        except Exception as e:
            raise LicenseError(f"Failed to load public key: {str(e)}")
        self._license_cache: LicenseInfo | None = None
        self._cache_timestamp: float | None = None
        self.cache_duration = 3600  # Cache duration in seconds

    def _verify_license(self, license_key: str) -> LicenseInfo:
        """Verify the license signature and return decoded contents"""
        try:
            data_b64, sig_b64 = license_key.split(".")
            data_bytes = base64.urlsafe_b64decode(data_b64 + "=" * (-len(data_b64) % 4))
            sig_bytes = base64.urlsafe_b64decode(sig_b64 + "=" * (-len(sig_b64) % 4))
            try:
                self.public_key.verify(
                    sig_bytes,
                    data_bytes,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH,
                    ),
                    hashes.SHA256(),
                )
            except Exception as e:
                raise LicenseError(f"Invalid license signature: {str(e)}")

            try:
                data = json.loads(data_bytes.decode("utf-8"))

                # Convert timestamp to datetime
                if "exp" in data:
                    data["expires_at"] = datetime.fromtimestamp(data["exp"])
                    del data["exp"]

                return LicenseInfo(**data)

            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                raise LicenseError(f"Invalid license format: {str(e)}")
            except ValidationError as e:
                raise LicenseError(f"Invalid license data: {str(e)}")

        except ValueError as e:
            raise LicenseError(f"Invalid license key format: {str(e)}")

    def _read_license_key(self) -> str:
        """Read license from standard location or environment variable"""
        license_key = os.getenv("LILYPAD_EE_LICENSE_KEY")
        if license_key:
            return license_key

        env_path = os.getenv("LILYPAD_EE_LICENSE_PATH")
        if env_path and os.path.exists(env_path):
            with open(env_path) as f:
                return f.read().strip()

        project_license_path = os.path.join(os.getcwd(), ".lilypad", "license.key")
        if os.path.exists(project_license_path):
            with open(project_license_path) as f:
                return f.read().strip()

        raise LicenseError(
            "No valid enterprise license found. Please set LILYPAD_EE_LICENSE_KEY, "
            "LILYPAD_EE_LICENSE_PATH, or add a license.key file to your .lilypad directory."
        )

    def validate_license(self, refresh: bool = False) -> LicenseInfo:
        """Get license information, using cache unless refresh is requested"""
        current_time = time.time()

        if (
            not refresh
            and self._license_cache
            and self._cache_timestamp
            and current_time - self._cache_timestamp < self.cache_duration
        ):
            return self._license_cache

        license_key = self._read_license_key()
        license_info = self._verify_license(license_key)
        self._license_cache = license_info
        self._cache_timestamp = current_time
        return license_info


def require_license() -> Callable:
    """Decorator to require a valid enterprise license"""

    def decorator(func: Callable[_P, _R]) -> Callable[_P, _R]:
        @functools.wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            LicenseValidator().validate_license()
            return func(*args, **kwargs)

        return wrapper

    return decorator


def generate_license(
    private_key_path: str,
    password: bytes,
    customer: str,
    license_id: str,
    expires_at: datetime,
) -> str:
    """Generate a license key"""
    with open(private_key_path) as key_file:
        key = serialization.load_pem_private_key(
            key_file.read().encode(), password=password, backend=default_backend()
        )
        if not isinstance(key, rsa.RSAPrivateKey):
            raise LicenseError("Private key must be an RSA key")
        private_key = key
    data = {
        "customer": customer,
        "license_id": license_id,
        "exp": expires_at.timestamp(),
    }
    data_bytes = json.dumps(data).encode("utf-8")
    signature = private_key.sign(
        data_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )
    data_b64 = base64.urlsafe_b64encode(data_bytes).rstrip(b"=").decode("ascii")
    sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
    return f"{data_b64}.{sig_b64}"