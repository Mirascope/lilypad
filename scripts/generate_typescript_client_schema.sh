#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "Generating TypeScript types for both v0 endpoints..."

mkdir -p "client/src/types"

echo "Processing v0 endpoint..."
uv run scripts/generate_python_client_schema.py generate-openapi --endpoint v0 | \
    node client/scripts/generate-api-types.js generate --stdin --output client/src/types

if [ $? -ne 0 ]; then
    echo "Error generating TypeScript types for v0 endpoint"
    exit 1
fi

echo "TypeScript types successfully generated for both endpoints:"
echo "   - v0:    client/src/types/types.ts"
