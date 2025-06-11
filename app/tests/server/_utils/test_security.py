"""Tests for security utility functions."""

from lilypad.server._utils.security import mask_secret, sanitize_secret_data


def test_mask_secret_basic():
    """Test basic secret masking."""
    assert mask_secret("mysecretpassword") == "myse************"
    assert mask_secret("short") == "shor*"
    assert mask_secret("abc") == "ab*"  # Always mask at least 1 char
    assert mask_secret("") == ""
    assert mask_secret(None) == ""


def test_mask_secret_custom_visible_chars():
    """Test secret masking with custom visible characters."""
    secret = "verysecrettoken"

    assert mask_secret(secret, visible_chars=0) == "*" * len(secret)
    assert mask_secret(secret, visible_chars=1) == "v" + "*" * (len(secret) - 1)
    assert mask_secret(secret, visible_chars=8) == "verysecr" + "*" * 7
    assert (
        mask_secret(secret, visible_chars=100) == "verysecrettoke*"
    )  # More than length but still masks 1


def test_mask_secret_edge_cases():
    """Test edge cases for secret masking."""
    # Single character
    assert mask_secret("a") == "*"
    assert mask_secret("a", visible_chars=0) == "*"

    # Exact length as visible_chars (still masks at least 1 char)
    assert mask_secret("test", visible_chars=4) == "tes*"

    # Unicode
    assert mask_secret("🔐secret", visible_chars=2) == "🔐s*****"


def test_sanitize_secret_data_basic():
    """Test basic secret data sanitization."""
    data = {
        "username": "john",
        "password": "mysecret123",
        "api_key": "sk_test_12345",
        "normal_field": "visible_data",
    }

    sanitized = sanitize_secret_data(data)

    assert sanitized["username"] == "john"
    assert sanitized["password"] == "myse*******"
    assert sanitized["api_key"] == "sk_t*********"
    assert sanitized["normal_field"] == "visible_data"


def test_sanitize_secret_data_nested():
    """Test sanitization of nested dictionaries."""
    data = {
        "config": {
            "database_url": "postgresql://user:pass@host",
            "secret_key": "verysecretkey",
            "debug": True,
        },
        "user": {"name": "John", "auth_token": "token12345"},
    }

    sanitized = sanitize_secret_data(data)

    assert sanitized["config"]["database_url"] == "postgresql://user:pass@host"
    assert sanitized["config"]["secret_key"] == "very*********"
    assert sanitized["config"]["debug"] is True
    assert sanitized["user"]["name"] == "John"
    assert sanitized["user"]["auth_token"] == "toke******"


def test_sanitize_secret_data_case_insensitive():
    """Test that sanitization is case insensitive."""
    data = {
        "PASSWORD": "uppercase_secret",
        "Secret": "titlecase_secret",
        "api_KEY": "mixed_case_secret",
        "AUTHTOKEN": "auth_secret",
        "credential_info": "cred_secret",
    }

    sanitized = sanitize_secret_data(data)

    assert sanitized["PASSWORD"] == "uppe************"
    assert sanitized["Secret"] == "titl************"
    assert sanitized["api_KEY"] == "mixe*************"
    assert sanitized["AUTHTOKEN"] == "auth*******"
    assert sanitized["credential_info"] == "cred*******"


def test_sanitize_secret_data_patterns():
    """Test various sensitive field patterns."""
    data = {
        # Password variations
        "password": "pass1",
        "user_password": "pass2",
        "password_hash": "pass3",
        # Secret variations
        "secret": "sec1",
        "client_secret": "sec2",
        "secret_value": "sec3",
        # Key variations
        "key": "key1",
        "api_key": "key2",
        "private_key": "key3",
        # Token variations
        "token": "tok1",
        "access_token": "tok2",
        "refresh_token": "tok3",
        # Auth variations
        "auth": "auth1",
        "authorization": "auth2",
        "auth_header": "auth3",
        # Credential variations
        "credential": "cred1",
        "credentials": "cred2",
        "user_credentials": "cred3",
    }

    sanitized = sanitize_secret_data(data)

    # All should be masked
    for key, value in sanitized.items():
        if isinstance(value, str):
            assert "*" in value, f"Field {key} should be masked"


def test_sanitize_secret_data_non_string_values():
    """Test sanitization with non-string sensitive values."""
    data = {
        "password": 12345,  # Number
        "secret_list": ["secret1", "secret2"],  # List
        "auth_bool": True,  # Boolean
        "token_none": None,  # None
    }

    sanitized = sanitize_secret_data(data)

    # Non-string sensitive values should not be masked
    assert sanitized["password"] == 12345
    assert sanitized["secret_list"] == ["secret1", "secret2"]
    assert sanitized["auth_bool"] is True
    assert sanitized["token_none"] is None


def test_sanitize_secret_data_empty():
    """Test sanitization with empty data."""
    assert sanitize_secret_data({}) == {}

    data = {"password": "", "secret": None, "nested": {}}

    sanitized = sanitize_secret_data(data)
    assert sanitized["password"] == ""
    assert sanitized["secret"] is None
    assert sanitized["nested"] == {}


def test_sanitize_secret_data_deep_nesting():
    """Test sanitization with deeply nested structures."""
    data = {
        "level1": {
            "level2": {
                "level3": {"secret_key": "deep_secret", "public_data": "visible"}
            }
        }
    }

    sanitized = sanitize_secret_data(data)

    assert sanitized["level1"]["level2"]["level3"]["secret_key"] == "deep*******"
    assert sanitized["level1"]["level2"]["level3"]["public_data"] == "visible"


def test_sanitize_secret_data_partial_matches():
    """Test fields that partially match sensitive patterns."""
    data = {
        "my_password_field": "should_mask",
        "secretive_data": "should_mask",
        "keychain": "should_mask",
        "token_bucket": "should_mask",
        "authentic": "should_mask",
        "accredential": "should_mask",
        # Should not mask
        "passage": "should_not_mask",
        "keyboard": "should_not_mask",
        "toking": "should_not_mask",
    }

    sanitized = sanitize_secret_data(data)

    # Fields containing sensitive patterns should be masked
    assert "*" in sanitized["my_password_field"]
    assert "*" in sanitized["secretive_data"]
    assert "*" in sanitized["keychain"]
    assert "*" in sanitized["token_bucket"]
    assert "*" in sanitized["authentic"]
    assert "*" in sanitized["accredential"]

    # Fields not containing patterns should not be masked
    assert "*" not in sanitized["passage"]
    assert "*" not in sanitized["keyboard"]
    assert "*" not in sanitized["toking"]
