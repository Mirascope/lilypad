.PHONY: setup dev test test-app test-sdk lint lint-app lint-sdk generate generate-openapi generate-sdk generate-client clean

setup:
	command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
	command -v bun >/dev/null || curl -fsSL https://bun.sh/install | bash
	cd app/client && pnpm install
	cd app && uv sync --all-extras --dev
	cd sdks/python && uv sync --all-extras --dev
	cd sdks && bun install

dev:
	docker-compose up -d

test: test-app test-sdk

test-app:
	cd app && uv run pytest

test-sdk:
	cd sdks/python && uv run pytest

lint: lint-app lint-sdk

lint-app:
	cd app && uv run ruff check .

lint-sdk:
	cd sdks/python && uv run ruff check .

generate: generate-openapi generate-sdk generate-client

generate-openapi:
	cd app && uv run python scripts/generate_python_client_schema.py generate-openapi --output ../sdks/fern/lilypad-api.json

generate-sdk:
	cd sdks && bun run fern generate --group python-sdk --local && rm -fr python/src/lilypad/.git

generate-client:
	cd app/client && pnpm generate:api:v0

clean:
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	cd app/client && rm -rf dist/ build/ node_modules/.cache/ || true