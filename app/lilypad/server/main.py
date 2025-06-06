"""The main FastAPI app for `lilypad`.

For development: Run fastapi dev lilypad/server/main.py
"""

import logging
import subprocess
import traceback
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response
from starlette.types import Scope as StarletteScope

from lilypad.server._utils.posthog import setup_posthog_middleware
from lilypad.server.logging_config import setup_logging
from lilypad.server.services.kafka_producer import (
    close_kafka_producer,
    get_kafka_producer,
)
from lilypad.server.services.kafka_setup import KafkaSetupService
from lilypad.server.services.span_queue_processor import get_span_queue_processor

from .api import v0_api
from .settings import get_settings

# Setup logging configuration
setup_logging()

log = logging.getLogger("lilypad")
settings = get_settings()


def run_migrations() -> None:
    """Run the migrations in a separate process."""
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True,
        )
        log.info(f"Migration output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        log.error(f"Migration failed: {e.stderr}")


@asynccontextmanager
async def lifespan(app_: FastAPI) -> AsyncGenerator[None, None]:
    """Run the migrations and optional setup on startup."""
    log.info("Running migrations")
    run_migrations()

    # Optional Kafka topic setup
    if settings.kafka_auto_setup_topics:
        log.info("Running Kafka topic setup")
        try:
            kafka_setup = KafkaSetupService(settings)
            # We're already in an async context, so just await directly
            setup_result = await kafka_setup.setup_topics()
            log.info(f"Kafka topic setup completed: {setup_result}")
        except Exception as e:
            log.error(f"Kafka setup failed (non-fatal): {e}")
            # Continue startup even if Kafka setup fails

    # Initialize Kafka producer if configured
    if settings.kafka_bootstrap_servers:
        log.info("Initializing Kafka producer")
        try:
            producer = await get_kafka_producer()
            if producer:
                log.info("Kafka producer initialized successfully")
            else:
                log.warning("Kafka producer initialization returned None")
        except Exception as e:
            log.error(f"Failed to initialize Kafka producer (non-fatal): {e}")
            # Continue startup even if Kafka fails

    # Start span queue processor if Kafka is configured
    queue_processor = None
    if settings.kafka_bootstrap_servers:
        log.info("Starting span queue processor")
        try:
            queue_processor = get_span_queue_processor()
            await queue_processor.start()
            log.info("Span queue processor started successfully")
        except Exception as e:
            log.error(f"Failed to start span queue processor (non-fatal): {e}")
            # Continue startup even if processor fails

    yield

    # Cleanup on shutdown
    if queue_processor:
        log.info("Stopping span queue processor")
        try:
            await queue_processor.stop()
        except Exception as e:
            log.error(f"Error stopping queue processor: {e}")

    # Close Kafka producer
    log.info("Closing Kafka producer")
    try:
        await close_kafka_producer()
    except Exception as e:
        log.error(f"Error closing Kafka producer: {e}")


origins = [
    "http://localhost:5173",
    "http://localhost:8000/*",
    "http://127.0.0.1:8000",
    f"http://localhost:{settings.port}/*",
    f"http://127.0.0.1:{settings.port}",
    settings.client_url,
    f"{settings.client_url}/*",
    settings.api_url,
    f"{settings.api_url}/*",
]

app = FastAPI(lifespan=lifespan, debug=settings.environment == "local")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_exceptions(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Log exceptions."""
    try:
        return await call_next(request)
    except Exception as e:
        log.error(f"Exception in request: {e}")
        log.error(traceback.format_exc())
        raise  # Re-raise to let FastAPI handle the response


setup_posthog_middleware(app, exclude_paths=[], should_capture=lambda _: True)

app.mount("/v0", v0_api)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation exceptions."""
    log.error(request, exc)  # noqa: T201
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


class SPAStaticFiles(StaticFiles):
    """Serve the index.html file for all routes."""

    async def get_response(self, path: str, scope: StarletteScope) -> Response:
        """Get the response for the given path."""
        try:
            return await super().get_response(path, scope)
        except (HTTPException, StarletteHTTPException) as ex:
            if ex.status_code == 404:
                return await super().get_response("index.html", scope)
            else:
                raise ex


if settings.environment == "local" or settings.serve_frontend:
    app.mount(
        "/", SPAStaticFiles(directory="lilypad/server/static", html=True), name="app"
    )
    app.mount(
        "/assets",
        SPAStaticFiles(directory="lilypad/server/static/assets", html=True),
        name="app_assets",
    )
