#!/usr/bin/env python3
"""Set up LocalStack with test secrets for development."""

import os
import sys
import time

import boto3
from botocore.exceptions import ClientError

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Ensure LocalStack endpoint is set
if not os.getenv("AWS_ENDPOINT_URL"):
    os.environ["AWS_ENDPOINT_URL"] = "http://localhost:4566"
    os.environ["AWS_ACCESS_KEY_ID"] = "test"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "test"


def wait_for_localstack(max_retries: int = 30, retry_delay: int = 2) -> bool:
    """Wait for LocalStack to be ready.

    Args:
        max_retries: Maximum number of retries
        retry_delay: Delay between retries in seconds

    Returns:
        True if LocalStack is ready, False otherwise
    """
    print("Waiting for LocalStack to be ready...")

    for i in range(max_retries):
        try:
            client = boto3.client(
                "secretsmanager",
                endpoint_url=os.getenv("AWS_ENDPOINT_URL"),
                region_name="us-east-1",
            )
            # Try to list secrets - this will fail if LocalStack isn't ready
            client.list_secrets(MaxResults=1)
            print("LocalStack is ready!")
            return True
        except Exception as e:
            if i < max_retries - 1:
                print(f"LocalStack not ready yet, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"LocalStack failed to start: {e}")
                return False

    return False


def create_test_secrets() -> None:
    """Create test secrets in LocalStack."""
    if not wait_for_localstack():
        print(
            "Failed to connect to LocalStack. Make sure it's running with docker-compose."
        )
        sys.exit(1)

    client = boto3.client(
        "secretsmanager",
        endpoint_url=os.getenv("AWS_ENDPOINT_URL"),
        region_name="us-east-1",
    )

    # Test secrets to create
    test_secrets = [
        {
            "name": "lilypad/test-api-key",
            "value": "test-api-key-value-12345",
            "description": "Test API key for development",
        },
        {
            "name": "lilypad/openai-key",
            "value": "sk-test-localstack-openai-key",
            "description": "Mock OpenAI API key for testing",
        },
        {
            "name": "lilypad/anthropic-key",
            "value": "test-anthropic-api-key",
            "description": "Mock Anthropic API key for testing",
        },
        {
            "name": "lilypad/database/password",
            "value": "secure-test-password",
            "description": "Test database password",
        },
    ]

    print("\nCreating test secrets in LocalStack...")

    for secret_data in test_secrets:
        try:
            # Try to create the secret
            response = client.create_secret(
                Name=secret_data["name"],
                SecretString=secret_data["value"],
                Description=secret_data["description"],
            )
            print(f"✓ Created secret: {secret_data['name']} (ARN: {response['ARN']})")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceExistsException":
                # Secret already exists, update it
                try:
                    client.update_secret(
                        SecretId=secret_data["name"],
                        SecretString=secret_data["value"],
                        Description=secret_data["description"],
                    )
                    print(f"✓ Updated existing secret: {secret_data['name']}")
                except Exception as update_error:
                    print(
                        f"✗ Failed to update secret {secret_data['name']}: {update_error}"
                    )
            else:
                print(f"✗ Failed to create secret {secret_data['name']}: {e}")

    # List all secrets to verify
    print("\nListing all secrets in LocalStack:")
    try:
        response = client.list_secrets()
        for secret in response.get("SecretList", []):
            print(f"  - {secret['Name']} (ARN: {secret['ARN']})")

        if not response.get("SecretList"):
            print("  No secrets found.")
    except Exception as e:
        print(f"Failed to list secrets: {e}")


if __name__ == "__main__":
    # Ensure we're using LocalStack
    if not os.getenv("AWS_ENDPOINT_URL"):
        os.environ["AWS_ENDPOINT_URL"] = "http://localhost:4566"

    create_test_secrets()
