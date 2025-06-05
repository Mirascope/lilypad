#!/usr/bin/env python3
"""Check current logging configuration."""

import logging
import os

# Show current logging configuration
print("=== Current Logging Configuration ===")
print(f"Root logger level: {logging.getLogger().level}")
print(f"Root logger level name: {logging.getLevelName(logging.getLogger().level)}")

# Check environment variables
print("\n=== Environment Variables ===")
print(f"LOG_LEVEL: {os.getenv('LOG_LEVEL', 'Not set')}")
print(f"LILYPAD_LOG_LEVEL: {os.getenv('LILYPAD_LOG_LEVEL', 'Not set')}")
print(f"PYTHONUNBUFFERED: {os.getenv('PYTHONUNBUFFERED', 'Not set')}")

# Check logger for specific modules
print("\n=== Module Logger Levels ===")
modules = [
    "lilypad.server.services.kafka",
    "lilypad.server.services.span_queue_processor",
    "lilypad.server.api.v0.traces_api",
    "uvicorn",
    "uvicorn.access"
]

for module in modules:
    logger = logging.getLogger(module)
    print(f"{module}: {logging.getLevelName(logger.level)}")