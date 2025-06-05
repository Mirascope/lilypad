"""Logging configuration for Lilypad server."""

import logging
import os
import sys


def setup_logging():
    """Configure logging for the application."""
    # Get log level from environment variable
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Create a handler that flushes immediately
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level, logging.INFO))
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    )
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        handlers=[handler],
        force=True  # Override any existing configuration
    )
    
    # Force flush after each log message
    class FlushHandler(logging.StreamHandler):
        def emit(self, record):
            super().emit(record)
            self.flush()
    
    # Replace handler with flush handler
    logging.root.handlers = [FlushHandler(sys.stdout)]
    logging.root.handlers[0].setFormatter(handler.formatter)
    
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