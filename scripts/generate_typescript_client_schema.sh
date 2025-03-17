#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "Generating TypeScript types for both v0 and ee-v0 endpoints..."

mkdir -p "client/src/types"
mkdir -p "client/src/ee/types"

echo "Processing v0 endpoint..."
uv run scripts/generate_python_client_schema.py generate-openapi --endpoint v0 | \
    node client/scripts/generate-api-types.js generate --stdin --output client/src/types

if [ $? -ne 0 ]; then
    echo "Error generating TypeScript types for v0 endpoint"
    exit 1
fi

echo "Processing ee-v0 endpoint..."
uv run scripts/generate_python_client_schema.py generate-openapi --endpoint ee-v0 | \
    node client/scripts/generate-api-types.js generate --stdin --output client/src/ee/types

if [ $? -ne 0 ]; then
    echo "Error generating TypeScript types for ee-v0 endpoint"
    exit 1
fi

echo "TypeScript types successfully generated for both endpoints:"
echo "   - v0:    client/src/types/types.ts"
echo "   - ee-v0: client/src/ee/types/types.ts"