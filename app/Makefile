# Development
.PHONY: help setup dev dev-services dev-local dev-local-app dev-local-client
.PHONY: dev-build-backend prod dev-down prod-down

# Kafka
.PHONY: setup-kafka setup-kafka-prod test-kafka

# Testing & Quality
.PHONY: test test-watch lint typecheck format fix

# Database
.PHONY: db-migrate db-rollback db-reset db-revision

# Maintenance
.PHONY: generate-openapi clean logs logs-app logs-services update-deps

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
	@echo "  db-migrate        - Run database migrations"
	@echo "  db-rollback       - Rollback last database migration"
	@echo "  db-reset          - Reset database (CAUTION: drops all data)"
	@echo "  db-revision       - Create new database migration"
	@echo "  logs              - Show logs for all Docker services"
	@echo "  logs-app          - Show logs for app service"
	@echo "  logs-services     - Show logs for dependency services"
	@echo "  test-watch        - Run tests in watch mode"
	@echo "  update-deps       - Update Python dependencies"

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
	@if [ ! -f .env.dev ]; then \
		echo "Error: .env.dev file not found!"; \
		echo "Please copy .env.dev.example to .env.dev and configure it"; \
		exit 1; \
	fi
	@echo "Starting backend app locally..."
	@echo "Make sure dependency services are running (make dev-services)"
	@export LILYPAD_DB_HOST=localhost && \
	export LILYPAD_OPENSEARCH_HOST=localhost && \
	export LILYPAD_KAFKA_BOOTSTRAP_SERVERS=localhost:9092 && \
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
	docker compose --env-file .env.dev -f docker-compose.dev.yml up postgres lilypad opensearch kafka kafka-ui --watch --build

test:
	uv run pytest

test-watch:
	@command -v pytest-watch >/dev/null 2>&1 || uv add --dev pytest-watch
	uv run pytest-watch

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

# Database operations
db-migrate:
	uv run alembic upgrade head

db-rollback:
	uv run alembic downgrade -1

db-reset:
	@echo "WARNING: This will drop all data in the database!"
	@echo "Press Ctrl+C to cancel, or wait 3 seconds to continue..."
	@sleep 3
	uv run alembic downgrade base
	uv run alembic upgrade head

db-revision:
	@echo "Enter migration message: " && \
	read msg && \
	uv run alembic revision -m "$$msg"

# Logging
logs:
	docker compose --env-file .env.dev -f docker-compose.dev.yml logs -f

logs-app:
	docker compose --env-file .env.dev -f docker-compose.dev.yml logs -f lilypad

logs-services:
	docker compose --env-file .env.dev -f docker-compose.dev.yml logs -f postgres kafka opensearch zookeeper localstack kafka-ui opensearch-dashboards

# Dependency management
update-deps:
	uv lock --upgrade
	uv sync --all-extras --dev
