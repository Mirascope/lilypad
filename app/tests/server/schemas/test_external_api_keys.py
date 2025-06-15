"""Test cases for external API keys schemas."""

import pytest

from lilypad.server.schemas.external_api_keys import ExternalAPIKeyPublic


def test_external_api_key_public_masked_key_validation():
    """Test ExternalAPIKeyPublic masked_api_key field validation (line 30)."""
    # Test the make_masked_key validator
    api_key = ExternalAPIKeyPublic(
        service_name="openai",
        masked_api_key="sk-1234567890abcdef1234567890abcdef"
    )
    
    # The validator should mask the key, showing first 4 characters + asterisks for the rest
    # Original: "sk-1234567890abcdef1234567890abcdef" (35 chars)
    # Masked:   "sk-1" + 31 asterisks = "sk-1*******************************"
    assert api_key.masked_api_key == "sk-1*******************************"


def test_external_api_key_public_short_key():
    """Test masked_api_key with short key."""
    api_key = ExternalAPIKeyPublic(
        service_name="test",
        masked_api_key="abc"
    )
    
    # For short keys, visible_chars is limited to len-1, so "ab*"
    assert api_key.masked_api_key == "ab*"