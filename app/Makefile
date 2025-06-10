.PHONY: setup dev prod dev-down prod-down setup-kafka setup-kafka-prod test-kafka test lint typecheck format fix generate-openapi clean

setup:
	uv sync --all-extras --dev

dev:
	docker compose --env-file .env -f docker-compose.dev.yml up -d

prod:
	docker compose --env-file .env up -d

dev-down:
	docker compose --env-file .env -f docker-compose.dev.yml down

prod-down:
	docker compose --env-file .env down

setup-kafka:
	./scripts/setup_kafka_topics.sh

setup-kafka-prod:
	./scripts/setup_kafka_topics_production.sh

test-kafka:
	uv run python scripts/test_kafka_connection.py

dev-build-backend:
	docker compose --env-file .env -f docker-compose.dev.yml up postgres lilypad opensearch --watch --build

test:
	uv run pytest

lint:
	uv run ruff check .

typecheck:
	uv run pyright lilypad tests

format:
	uv run ruff format .

fix:
	uv run ruff check --fix --unsafe-fixes .

generate-openapi:
	uv run python scripts/generate_python_client_schema.py generate-openapi --output ../sdks/fern/lilypad-api.json

clean:
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true