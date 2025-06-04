# LocalStack Setup for AWS Secrets Manager

This guide explains how to use LocalStack for local development with AWS Secrets Manager.

## Overview

LocalStack provides a local AWS cloud stack for development and testing. We use it to simulate AWS Secrets Manager without needing real AWS credentials or incurring costs.

## Setup

### 1. Start LocalStack with Docker Compose

```bash
# From the app directory
docker-compose -f docker-compose.dev.yml up -d

# Or using make from the project root
make dev
```

This will start:
- LocalStack on port 4566
- PostgreSQL, Kafka, OpenSearch, and other services
- The Lilypad application configured to use LocalStack

### 2. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.dev.example .env.dev
```

Key environment variables for LocalStack:
- `AWS_ENDPOINT_URL=http://localstack:4566` - Points to LocalStack instead of real AWS
- `SECRET_MANAGER_TYPE=AWS_SECRET_MANAGER` - Use AWS Secret Manager (via LocalStack)
- `AWS_ACCESS_KEY_ID=test` - Dummy credentials for LocalStack
- `AWS_SECRET_ACCESS_KEY=test` - Dummy credentials for LocalStack

### 3. Initialize Test Secrets

After LocalStack is running, create some test secrets:

```bash
cd app
python scripts/setup_localstack_secrets.py
```

This creates test secrets like:
- `lilypad/test-api-key`
- `lilypad/openai-key`
- `lilypad/anthropic-key`
- `lilypad/database/password`

### 4. Test the Integration

Run the test script to verify everything is working:

```bash
python scripts/localstack_integration_test.py
```

## Using LocalStack in Development

### Automatic Detection

The AWS Secret Manager automatically detects LocalStack when `AWS_ENDPOINT_URL` is set:

```python
from lilypad.server.secret_manager.aws_secret_manager import AWSSecretManager
from lilypad.server.secret_manager.config import AWSSecretManagerConfig

# Will use LocalStack if AWS_ENDPOINT_URL is set
config = AWSSecretManagerConfig()
manager = AWSSecretManager(config)

# Store a secret
arn = manager.store_secret("my-key", "my-value")

# Retrieve it
value = manager.get_secret(arn)
```

The implementation automatically checks the `AWS_ENDPOINT_URL` environment variable and uses it if present. This allows seamless switching between LocalStack and real AWS without code changes.

## Switching Between LocalStack and Real AWS

### Use LocalStack (Development)
```bash
# In .env.dev
AWS_ENDPOINT_URL=http://localstack:4566
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
SECRET_MANAGER_TYPE=AWS_SECRET_MANAGER
```

### Use Real AWS (Production)
```bash
# In .env.dev (or production env)
# AWS_ENDPOINT_URL=  # Comment out or remove
AWS_ACCESS_KEY_ID=your-real-access-key
AWS_SECRET_ACCESS_KEY=your-real-secret-key
AWS_DEFAULT_REGION=us-east-1
SECRET_MANAGER_TYPE=AWS_SECRET_MANAGER
```

### Use Supabase Vault (Alternative)
```bash
# In .env.dev
SECRET_MANAGER_TYPE=SUPABASE_VAULT
# No AWS configuration needed
```

## LocalStack Dashboard

You can view LocalStack resources at:
- Health check: http://localhost:4566/_localstack/health
- Dashboard: http://localhost:4566/_localstack/dashboard (if enabled)

## Troubleshooting

### LocalStack not starting
- Check Docker logs: `docker-compose -f docker-compose.dev.yml logs localstack`
- Ensure port 4566 is not in use: `lsof -i :4566`

### Connection refused errors
- Wait for LocalStack to fully start (can take 30-60 seconds)
- Check if LocalStack is healthy: `curl http://localhost:4566/_localstack/health`

### Secrets not persisting
- LocalStack data is stored in a Docker volume
- To reset: `docker-compose -f docker-compose.dev.yml down -v`

### Authentication errors
- Ensure `AWS_ENDPOINT_URL` is set correctly
- LocalStack accepts any credentials, but they must be present

## Benefits of Using LocalStack

1. **No AWS Costs**: Test as much as you want without charges
2. **Offline Development**: Works without internet connection
3. **Fast**: No network latency to AWS
4. **Safe**: No risk of affecting production resources
5. **Consistent**: Same environment for all developers

## Additional Resources

- [LocalStack Documentation](https://docs.localstack.cloud/)
- [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager.html)