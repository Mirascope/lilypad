"""The main FastAPI app for `lilypad`.

For development: Run fastapi dev lilypad/server/main.py
"""

import asyncio
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
from lilypad.server.services.stripe_queue_processor import get_stripe_queue_processor

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

    # Start stripe queue processor if Kafka is configured
    stripe_processor = None
    if settings.kafka_bootstrap_servers:
        log.info("Starting stripe queue processor")
        try:
            stripe_processor = get_stripe_queue_processor()
            await stripe_processor.start()
            log.info("Stripe queue processor started successfully")
        except Exception as e:  # pragma: no cover
            log.error(
                f"Failed to start stripe queue processor (non-fatal): {e}"
            )  # pragma: no cover
            # Continue startup even if processor fails

    yield

    # Cleanup on shutdown
    log.info("Starting graceful shutdown...")

    # First stop the queue processors to prevent new messages
    if queue_processor:
        log.info("Stopping span queue processor")
        try:
            await queue_processor.stop()
            log.info("Span queue processor stopped successfully")
        except Exception as e:
            log.error(f"Error stopping span queue processor: {e}")

    if stripe_processor:
        log.info("Stopping stripe queue processor")
        try:
            await stripe_processor.stop()
            log.info("Stripe queue processor stopped successfully")
        except Exception as e:  # pragma: no cover
            log.error(f"Error stopping stripe queue processor: {e}")  # pragma: no cover

    # Give more time for pending tasks to complete
    log.info("Waiting for pending tasks to complete...")
    await asyncio.sleep(1.0)

    # Then close Kafka producer
    log.info("Closing Kafka producer")
    try:
        await close_kafka_producer()
        log.info("Kafka producer closed successfully")
    except Exception as e:
        log.error(f"Error closing Kafka producer: {e}")

    # Final delay to ensure all internal tasks are cleaned up
    await asyncio.sleep(0.5)

    # Collect any remaining tasks
    try:
        pending_tasks = [
            task
            for task in asyncio.all_tasks()
            if not task.done() and task != asyncio.current_task()
        ]
    except AttributeError:
        # For Python 3.9+
        pending_tasks = [
            task
            for task in asyncio.all_tasks(asyncio.get_running_loop())
            if not task.done() and task != asyncio.current_task()
        ]

    if pending_tasks:
        log.warning(f"Found {len(pending_tasks)} pending tasks during shutdown")
        # Cancel them
        for task in pending_tasks:
            task.cancel()
        # Wait for them to complete cancellation
        await asyncio.gather(*pending_tasks, return_exceptions=True)

    log.info("Graceful shutdown completed")


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


if settings.environment == "local" or settings.serve_frontend:  # pragma: no cover
    app.mount(
        "/", SPAStaticFiles(directory="lilypad/server/static", html=True), name="app"
    )
    app.mount(
        "/assets",
        SPAStaticFiles(directory="lilypad/server/static/assets", html=True),
        name="app_assets",
    )
