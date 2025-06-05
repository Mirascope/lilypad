"""Logging configuration for Lilypad server."""

import logging
import os
import sys


def setup_logging():
    """Configure logging for the application."""
    # Get log level from environment variable
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,  # Ensure output goes to stdout
        force=True  # Override any existing configuration
    )
    
    # Set specific loggers to INFO level to ensure our logs are visible
    loggers_to_configure = [
        "lilypad",
        "lilypad.server.services.kafka",
        "lilypad.server.services.kafka_setup",
        "lilypad.server.services.span_queue_processor",
        "lilypad.server.api.v0.traces_api",
    ]
    
    for logger_name in loggers_to_configure:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        
    # Reduce noise from other loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {log_level}")
    logger.info(f"Python unbuffered: {os.getenv('PYTHONUNBUFFERED', 'Not set')}")