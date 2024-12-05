# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim

# Install the project into `/app/lilypad/server`
WORKDIR /app/lilypad/server

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

ARG RAILWAY_SERVICE_ID
# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,id=$RAILWAY_SERVICE_ID-/root/.cache/uv,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --all-extras

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
ADD . /app
RUN --mount=type=cache,id=$RAILWAY_SERVICE_ID-/root/.cache/uv,target=/root/.cache/uv \
    uv sync --frozen --no-dev --all-extras

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Run the FastAPI application by default
CMD ["fastapi", "run"]
