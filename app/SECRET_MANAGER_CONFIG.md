# Secret Manager Configuration Guide

Lilypad supports two secret management backends for storing API keys and other sensitive data:

1. **Supabase Vault** (default) - Uses PostgreSQL's built-in encryption
2. **AWS Secrets Manager** - Uses AWS's managed secret storage service

## Configuration Options

### Using Supabase Vault (Default)

This is the default option and requires no additional configuration. Secrets are stored encrypted in your PostgreSQL database.

```yaml
environment:
  - LILYPAD_SECRET_MANAGER_TYPE=SUPABASE_VAULT
```

### Using AWS Secrets Manager

To use AWS Secrets Manager, update your `docker-compose.yml`:

```yaml
environment:
  - LILYPAD_SECRET_MANAGER_TYPE=AWS_SECRET_MANAGER
  - LILYPAD_AWS_REGION=us-east-1  # Change to your preferred region
  - AWS_ACCESS_KEY_ID=your-access-key-id
  - AWS_SECRET_ACCESS_KEY=your-secret-access-key
```

#### AWS Authentication Methods

1. **Using Access Keys** (shown above):
   - Create an IAM user with `SecretsManagerReadWrite` policy
   - Generate access keys and add them to your environment

2. **Using IAM Roles** (recommended for AWS deployments):
   - Attach an IAM role with `SecretsManagerReadWrite` policy to your EC2/ECS instance
   - Omit `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` from the configuration

#### Required AWS IAM Permissions

Create an IAM policy with these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:CreateSecret",
        "secretsmanager:GetSecretValue",
        "secretsmanager:UpdateSecret",
        "secretsmanager:DeleteSecret",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:lilypad/*"
    }
  ]
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LILYPAD_SECRET_MANAGER_TYPE` | Type of secret manager to use | `SUPABASE_VAULT` |
| `LILYPAD_AWS_REGION` | AWS region for Secrets Manager | `us-east-1` |
| `LILYPAD_AWS_SECRET_MANAGER_FORCE_DELETE` | Force immediate deletion without recovery | `false` |
| `LILYPAD_AWS_SECRET_MANAGER_MAX_RETRIES` | Max retry attempts for API calls | `3` |
| `AWS_ACCESS_KEY_ID` | AWS access key (optional with IAM roles) | - |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key (optional with IAM roles) | - |

## Security Considerations

- **Supabase Vault**: Secrets are encrypted at rest in PostgreSQL. Ensure your database is properly secured.
- **AWS Secrets Manager**: 
  - Provides automatic encryption, rotation capabilities, and fine-grained access control through IAM
  - Input validation prevents injection attacks
  - Configurable deletion behavior (immediate vs recovery window)
  - Built-in retry mechanism for resilience
  - Audit logging for all operations

## Migration Between Secret Managers

Currently, there's no automated migration tool. To switch between secret managers:

1. Export all API keys from the current system
2. Update the configuration to use the new secret manager
3. Re-import the API keys through the Lilypad UI

## Cost Considerations

- **Supabase Vault**: No additional cost (uses your existing PostgreSQL database)
- **AWS Secrets Manager**: $0.40 per secret per month + API call charges (see [AWS pricing](https://aws.amazon.com/secrets-manager/pricing/))