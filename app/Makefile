.PHONY: help setup dev dev-services dev-local dev-local-app dev-local-client prod dev-down prod-down setup-kafka setup-kafka-prod test-kafka test lint typecheck format fix generate-openapi clean dev-build-backend

help:
	@echo "Available targets:"
	@echo "  setup             - Install dependencies"
	@echo "  dev               - Start development environment (all in Docker)"
	@echo "  dev-services      - Start only dependency services in Docker"
	@echo "  dev-local         - Start services in Docker, app/client locally"
	@echo "  dev-local-app     - Start backend app locally (requires dev-services)"
	@echo "  dev-local-client  - Start frontend client locally (requires dev-services)"
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

dev-services:
	docker compose --env-file .env.dev -f docker-compose.dev.yml up -d postgres opensearch opensearch-dashboards zookeeper kafka kafka-ui localstack

dev-local: dev-services
	@echo "Starting services in Docker and app/client locally..."
	@echo "Use 'make dev-local-app' in another terminal to start the backend"
	@echo "Use 'make dev-local-client' in another terminal to start the frontend"

dev-local-app:
	@echo "Starting backend app locally..."
	uv run python -m lilypad.server.main

dev-local-client:
	@echo "Starting frontend client locally..."
	$(MAKE) -C client dev

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
