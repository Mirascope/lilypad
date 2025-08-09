# Development commands
.PHONY: help setup dev dev-services dev-local dev-local-app dev-local-client
.PHONY: dev-build-backend prod dev-down prod-down

# Kafka commands
.PHONY: setup-kafka setup-kafka-prod test-kafka

# Stripe commands
.PHONY: dev-stripe-webhook

# Testing
.PHONY: test test-app test-sdk test-sdk-python test-sdk-typescript test-watch test-coverage test-coverage-app test-coverage-sdk test-coverage-sdk-python test-coverage-sdk-typescript

# Code quality
.PHONY: lint lint-app lint-sdk lint-sdk-python lint-sdk-typescript lint-client
.PHONY: format format-app format-sdk format-sdk-python format-sdk-typescript
.PHONY: typecheck typecheck-app typecheck-sdk typecheck-sdk-python typecheck-sdk-typescript typecheck-client
.PHONY: fix fix-app fix-sdk fix-sdk-python fix-sdk-typescript

# Code generation
.PHONY: generate generate-openapi generate-sdk generate-sdk-python generate-sdk-typescript generate-client

# Maintenance
.PHONY: clean clean-all db-migrate db-rollback db-reset db-revision
.PHONY: logs logs-app logs-services check update-deps

help:
	@echo "Available targets:"
	@echo "  setup             - Install all dependencies (uv, bun, packages)"
	@echo "  dev               - Start development environment (all in Docker)"
	@echo "  dev-services      - Start only dependency services in Docker"
	@echo "  dev-local         - Start services in Docker, app/client locally"
	@echo "  dev-local-app     - Start backend app locally (requires dev-services)"
	@echo "  dev-local-client  - Start frontend client locally (requires dev-services)"
	@echo "  dev-build-backend - Start backend services with watch mode"
	@echo "  dev-stripe-webhook - Start Stripe webhook listener"
	@echo "  prod              - Start production environment"
	@echo "  dev-down          - Stop development environment"
	@echo "  prod-down         - Stop production environment"
	@echo "  setup-kafka       - Set up Kafka topics for development"
	@echo "  setup-kafka-prod  - Set up Kafka topics for production"
	@echo "  test-kafka        - Test Kafka connection"
	@echo "  test              - Run all tests"
	@echo "  test-coverage     - Run all tests with coverage report"
	@echo "  test-app          - Run app tests only"
	@echo "  test-coverage-app - Run app tests with coverage report"
	@echo "  test-sdk          - Run all SDK tests (Python and TypeScript)"
	@echo "  test-sdk-python   - Run Python SDK tests only"
	@echo "  test-sdk-typescript - Run TypeScript SDK tests only"
	@echo "  test-coverage-sdk - Run all SDK tests with coverage report"
	@echo "  test-coverage-sdk-python - Run Python SDK tests with coverage report"
	@echo "  test-coverage-sdk-typescript - Run TypeScript SDK tests with coverage report"
	@echo "  lint              - Run all linters"
	@echo "  lint-app          - Run app linter"
	@echo "  lint-sdk          - Run all SDK linters"
	@echo "  lint-sdk-python   - Run Python SDK linter"
	@echo "  lint-sdk-typescript - Run TypeScript SDK linter"
	@echo "  lint-client       - Run client linter (ESLint)"
	@echo "  typecheck         - Run all type checkers"
	@echo "  typecheck-app     - Run app type checker"
	@echo "  typecheck-sdk     - Run all SDK type checkers"
	@echo "  typecheck-sdk-python - Run Python SDK type checker"
	@echo "  typecheck-sdk-typescript - Run TypeScript SDK type checker"
	@echo "  typecheck-client  - Run client type checker (TypeScript)"
	@echo "  format            - Format all code"
	@echo "  format-app        - Format app code"
	@echo "  format-sdk        - Format all SDK code"
	@echo "  format-sdk-python - Format Python SDK code"
	@echo "  format-sdk-typescript - Format TypeScript SDK code"
	@echo "  fix               - Auto-fix all linting issues"
	@echo "  fix-app           - Auto-fix app linting issues"
	@echo "  fix-sdk           - Auto-fix all SDK linting issues"
	@echo "  fix-sdk-python    - Auto-fix Python SDK linting issues"
	@echo "  fix-sdk-typescript - Auto-fix TypeScript SDK linting issues"
	@echo "  generate          - Generate all code (OpenAPI, SDK, client)"
	@echo "  generate-openapi  - Generate OpenAPI schema"
	@echo "  generate-sdk      - Generate all SDKs (Python and TypeScript)"
	@echo "  generate-sdk-python - Generate Python SDK only"
	@echo "  generate-sdk-typescript - Generate TypeScript SDK only"
	@echo "  generate-client   - Generate TypeScript client"
	@echo "  clean             - Clean build artifacts"
	@echo "  clean-all         - Clean all artifacts including caches"
	@echo "  db-migrate        - Run database migrations"
	@echo "  db-revision       - Make a database revision"
	@echo "  db-rollback       - Rollback last database migration"
	@echo "  db-reset          - Reset database (CAUTION: drops all data)"
	@echo "  logs              - Show logs for all services"
	@echo "  logs-app          - Show logs for app service"
	@echo "  logs-services     - Show logs for dependency services"
	@echo "  check             - Run all checks (lint, typecheck, test)"
	@echo "  test-watch        - Run backend tests in watch mode"
	@echo "  update-deps       - Update all dependencies"

# Global setup
setup:
	command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
	command -v bun >/dev/null || curl -fsSL https://bun.sh/install | bash
	+$(MAKE) -C app/client setup
	+$(MAKE) -C app setup
	+$(MAKE) -C sdks/python setup
	+$(MAKE) -C sdks/typescript setup || true
	+$(MAKE) -C sdks setup

# Development commands
dev:
	+$(MAKE) -C app dev

dev-services:
	+$(MAKE) -C app dev-services

dev-local:
	+$(MAKE) -C app dev-local

dev-stripe-webhook:
	+$(MAKE) -C app dev-stripe-webhook

dev-local-app:
	+$(MAKE) -C app dev-local-app

dev-local-client:
	+$(MAKE) -C app dev-local-client

dev-build-backend:
	+$(MAKE) -C app dev-build-backend

prod:
	+$(MAKE) -C app prod

dev-down:
	+$(MAKE) -C app dev-down

prod-down:
	+$(MAKE) -C app prod-down

# Kafka commands
setup-kafka:
	+$(MAKE) -C app setup-kafka

setup-kafka-prod:
	+$(MAKE) -C app setup-kafka-prod

test-kafka:
	+$(MAKE) -C app test-kafka

# Testing
test: test-app test-sdk

test-coverage: test-coverage-app test-coverage-sdk

test-app:
	+$(MAKE) -C app test

test-coverage-app:
	+$(MAKE) -C app test-coverage

test-sdk: test-sdk-python test-sdk-typescript

test-sdk-python:
	+$(MAKE) -C sdks/python test

test-sdk-typescript:
	+$(MAKE) -C sdks/typescript test || true

test-coverage-sdk: test-coverage-sdk-python test-coverage-sdk-typescript

test-coverage-sdk-python:
	+$(MAKE) -C sdks/python test-coverage

test-coverage-sdk-typescript:
	+$(MAKE) -C sdks/typescript test-coverage || true

test-watch:
	+$(MAKE) -C app test-watch

# Linting
lint: lint-app lint-sdk lint-client

lint-app:
	+$(MAKE) -C app lint

lint-sdk: lint-sdk-python lint-sdk-typescript

lint-sdk-python:
	+$(MAKE) -C sdks/python lint

lint-sdk-typescript:
	+$(MAKE) -C sdks/typescript lint || true

lint-client:
	+$(MAKE) -C app/client lint

# Type checking
typecheck: typecheck-app typecheck-sdk typecheck-client

typecheck-app:
	+$(MAKE) -C app typecheck

typecheck-sdk: typecheck-sdk-python typecheck-sdk-typescript

typecheck-sdk-python:
	+$(MAKE) -C sdks/python typecheck

typecheck-sdk-typescript:
	+$(MAKE) -C sdks/typescript typecheck || true

typecheck-client:
	+$(MAKE) -C app/client typecheck

# Formatting
format: format-app format-sdk

format-app:
	+$(MAKE) -C app format

format-sdk: format-sdk-python format-sdk-typescript

format-sdk-python:
	+$(MAKE) -C sdks/python format

format-sdk-typescript:
	+$(MAKE) -C sdks/typescript format || true

# Auto-fix
fix: fix-app fix-sdk

fix-app:
	+$(MAKE) -C app fix

fix-sdk: fix-sdk-python fix-sdk-typescript

fix-sdk-python:
	+$(MAKE) -C sdks/python fix

fix-sdk-typescript:
	+$(MAKE) -C sdks/typescript fix || true

# Code generation
# Note: Order matters - OpenAPI must be generated before SDKs
generate: generate-openapi
	@echo "OpenAPI schema generated, now generating SDKs..."
	+$(MAKE) generate-sdk
	+$(MAKE) generate-client

generate-openapi:
	+$(MAKE) -C app generate-openapi

generate-sdk: generate-openapi
	+$(MAKE) -C sdks generate-sdk

generate-sdk-python: generate-openapi
	+$(MAKE) -C sdks generate-sdk-python

generate-sdk-typescript: generate-openapi
	+$(MAKE) -C sdks generate-sdk-typescript

generate-client:
	+$(MAKE) -C app/client generate-api-v0

# Cleaning
clean:
	+$(MAKE) -C app clean
	+$(MAKE) -C app/client clean
	+$(MAKE) -C sdks/python clean
	+$(MAKE) -C sdks/typescript clean || true
	+$(MAKE) -C sdks clean

clean-all: clean
	find . -name '.ruff_cache' -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name '.pytest_cache' -type d -exec rm -rf {} + 2>/dev/null || true

# Database operations
db-migrate:
	+$(MAKE) -C app db-migrate

db-revision:
	+$(MAKE) -C app db-revision

db-rollback:
	+$(MAKE) -C app db-rollback

db-reset:
	+$(MAKE) -C app db-reset

# Logging
logs:
	+$(MAKE) -C app logs

logs-app:
	+$(MAKE) -C app logs-app

logs-services:
	+$(MAKE) -C app logs-services

# Combined checks
check: lint typecheck test-coverage
	@echo "All checks passed!"

# Dependency management
update-deps:
	@echo "Updating Python dependencies..."
	+$(MAKE) -C app update-deps
	+$(MAKE) -C sdks/python update-deps
	@echo "Updating JavaScript dependencies..."
	+$(MAKE) -C app/client update-deps
	+$(MAKE) -C sdks/typescript update-deps || true
	+$(MAKE) -C sdks update-deps

