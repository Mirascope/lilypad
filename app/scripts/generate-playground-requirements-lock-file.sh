#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

uv pip compile playground-requirements.txt -o playground-requirements.lock  --python-version 3.10 --python-platform x86_64-manylinux2014

if [ $? -ne 0 ]; then
    echo "Error generating lock file for playground requirements"
    exit 1
fi
