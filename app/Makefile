.PHONY: help setup dev prod dev-down prod-down setup-kafka setup-kafka-prod test-kafka test lint typecheck format fix generate-openapi clean dev-build-backend

help:
	@echo "Available targets:"
	@echo "  setup             - Install dependencies"
	@echo "  dev               - Start development environment"
	@echo "  dev-build-backend - Start backend services with watch mode"
	@echo "  prod              - Start production environment"
	@echo "  dev-down          - Stop development environment"
	@echo "  prod-down         - Stop production environment"
	@echo "  setup-kafka       - Set up Kafka topics for development"
	@echo "  setup-kafka-prod  - Set up Kafka topics for production"
	@echo "  test-kafka        - Test Kafka connection"
	@echo "  test              - Run tests"
	@echo "  lint              - Run linter"
	@echo "  typecheck         - Run type checker"
	@echo "  format            - Format code"
	@echo "  fix               - Auto-fix linting issues"
	@echo "  generate-openapi  - Generate OpenAPI schema"
	@echo "  clean             - Clean build artifacts"

setup:
	uv sync --all-extras --dev

dev:
	docker compose --env-file .env.dev -f docker-compose.dev.yml up -d

prod:
	docker compose up -d

dev-down:
	docker compose --env-file .env.dev -f docker-compose.dev.yml down

prod-down:
	docker compose down

setup-kafka:
	./scripts/setup_kafka_topics.sh

setup-kafka-prod:
	./scripts/setup_kafka_topics_production.sh

test-kafka:
	uv run python scripts/test_kafka_connection.py

dev-build-backend:
	docker compose --env-file .env.dev -f docker-compose.dev.yml up postgres lilypad opensearch --watch --build

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
