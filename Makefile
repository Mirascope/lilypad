.PHONY: setup dev dev-build-backend prod dev-down prod-down setup-kafka setup-kafka-prod test-kafka test test-app test-sdk lint lint-app lint-sdk lint-client format format-app format-sdk typecheck typecheck-app typecheck-sdk typecheck-client fix fix-app fix-sdk generate generate-openapi generate-sdk generate-client clean clean-all

# Global setup
setup:
	command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
	command -v bun >/dev/null || curl -fsSL https://bun.sh/install | bash
	$(MAKE) -C app/client setup
	$(MAKE) -C app setup
	$(MAKE) -C sdks/python setup
	$(MAKE) -C sdks setup

# Development commands
dev:
	$(MAKE) -C app dev

dev-build-backend:
	$(MAKE) -C app dev-build-backend

prod:
	$(MAKE) -C app prod

dev-down:
	$(MAKE) -C app dev-down

prod-down:
	$(MAKE) -C app prod-down

# Kafka commands
setup-kafka:
	$(MAKE) -C app setup-kafka

setup-kafka-prod:
	$(MAKE) -C app setup-kafka-prod

test-kafka:
	$(MAKE) -C app test-kafka

# Testing
test: test-app test-sdk

test-app:
	$(MAKE) -C app test

test-sdk:
	$(MAKE) -C sdks/python test

# Linting
lint: lint-app lint-sdk lint-client

lint-app:
	$(MAKE) -C app lint

lint-sdk:
	$(MAKE) -C sdks/python lint

lint-client:
	$(MAKE) -C app/client lint

# Type checking
typecheck: typecheck-app typecheck-sdk typecheck-client

typecheck-app:
	$(MAKE) -C app typecheck

typecheck-sdk:
	$(MAKE) -C sdks/python typecheck

typecheck-client:
	$(MAKE) -C app/client typecheck

# Formatting
format: format-app format-sdk

format-app:
	$(MAKE) -C app format

format-sdk:
	$(MAKE) -C sdks/python format

# Auto-fix
fix: fix-app fix-sdk

fix-app:
	$(MAKE) -C app fix

fix-sdk:
	$(MAKE) -C sdks/python fix

# Code generation
generate: generate-openapi generate-sdk generate-client

generate-openapi:
	$(MAKE) -C app generate-openapi

generate-sdk:
	$(MAKE) -C sdks generate-sdk

generate-client:
	$(MAKE) -C app/client generate-api

# Cleaning
clean:
	$(MAKE) -C app clean
	$(MAKE) -C app/client clean
	$(MAKE) -C sdks/python clean
	$(MAKE) -C sdks clean

clean-all: clean
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name '.ruff_cache' -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name '.pytest_cache' -type d -exec rm -rf {} + 2>/dev/null || true
