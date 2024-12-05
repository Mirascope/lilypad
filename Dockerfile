FROM node:20-slim as frontend
WORKDIR /app/client

# Install pnpm
RUN npm install -g pnpm

# Copy client files
COPY client/. .

# Install dependencies and build
RUN pnpm install
RUN pnpm run build:notypescript


# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim

# Install the project into `/app
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

COPY . /app

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,id=s/f10d6a1b-8979-434f-addc-9ac197d051b2-/root/.cache/uv,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev --all-extras

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
ADD . /app
RUN --mount=type=cache,id=s/f10d6a1b-8979-434f-addc-9ac197d051b2-/root/.cache/uv,target=/root/.cache/uv \
    uv sync --frozen --no-dev --all-extras

WORKDIR /app/lilypad/server

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Run the FastAPI application by default
CMD ["fastapi", "run"]
