# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim

# Install the project into `/app
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# First copy only the dependency files for better layer caching
COPY pyproject.toml uv.lock playground-requirements.lock /app/

# For Test
RUN apt update && apt install git -y

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,id=s/f10d6a1b-8979-434f-addc-9ac197d051b2-/root/.cache/uv,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev --all-extras

# Pre-install playground dependencies and cache them
RUN uv venv --no-project /opt/playground-venv
RUN VIRTUAL_ENV=/opt/playground-venv uv pip sync playground-requirements.lock

# Now copy the full application code
COPY . /app

# Install the project itself
RUN --mount=type=cache,id=s/f10d6a1b-8979-434f-addc-9ac197d051b2-/root/.cache/uv,target=/root/.cache/uv \
    uv sync --frozen --no-dev --all-extras

WORKDIR /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"
# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Run the FastAPI application by default
CMD ["fastapi", "run", "--workers", "32", "lilypad/server/main.py"]
