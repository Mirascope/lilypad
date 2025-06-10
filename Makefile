.PHONY: setup dev dev-build-backend stripe-webhook prod dev-down prod-down setup-kafka setup-kafka-prod test-kafka test test-app test-sdk lint lint-app lint-sdk format format-app format-sdk fix fix-app fix-sdk generate generate-openapi generate-sdk generate-client clean

setup:
	command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
	command -v bun >/dev/null || curl -fsSL https://bun.sh/install | bash
	cd app/client && bun install
	cd app && uv sync --all-extras --dev
	cd sdks/python && uv sync --all-extras --dev
	cd sdks && bun install

dev:
	cd app && docker-compose -f docker-compose.dev.yml up -d

prod:
	cd app && docker-compose up -d

dev-down:
	cd app && docker-compose -f docker-compose.dev.yml down

stripe-webhook:
	stripe listen --forward-to localhost:8000/v0/webhooks/stripe

prod-down:
	cd app && docker-compose down

setup-kafka:
	cd app && ./scripts/setup_kafka_topics.sh

setup-kafka-prod:
	cd app && ./scripts/setup_kafka_topics_production.sh

test-kafka:
	cd app && uv run python scripts/test_kafka_connection.py

dev-build-backend:
	docker compose --env-file app/.env.dev -f app/docker-compose.dev.yml up postgres lilypad opensearch --watch --build

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

typecheck: typecheck-app typecheck-sdk

typecheck-app:
	cd app && uv run pyright lilypad tests
typecheck-sdk:
	cd sdks/python && uv run pyright src/lilypad tests

format: format-app format-sdk

format-app:
	cd app && uv run ruff format .

format-sdk:
	cd sdks/python && uv run ruff format .

fix: fix-app fix-sdk

fix-app:
	cd app && uv run ruff check --fix --unsafe-fixes .

fix-sdk:
	cd sdks/python && uv run ruff check --fix --unsafe-fixes .

generate: generate-openapi generate-sdk generate-client

generate-openapi:
	cd app && uv run python scripts/generate_python_client_schema.py generate-openapi --output ../sdks/fern/lilypad-api.json

generate-sdk:
	cd sdks && bun run fern generate --group python-sdk --local && rm -fr python/src/lilypad/.git

generate-client:
	cd app/client && bun generate:api:v0

clean:
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	cd app/client && rm -rf dist/ build/ node_modules/.cache/ || true
