# Basic Operations
.PHONY: help setup

# Testing
.PHONY: test test-watch test-coverage

# Code Quality
.PHONY: lint typecheck format fix

# Build & Release
.PHONY: build publish

# Maintenance
.PHONY: clean update-deps

help:
	@echo "Available targets:"
	@echo "  setup     - Install dependencies"
	@echo "  test          - Run tests"
	@echo "  test-watch    - Run tests in watch mode"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  lint          - Run linter"
	@echo "  typecheck - Run type checker"
	@echo "  format    - Format code"
	@echo "  fix           - Auto-fix linting issues"
	@echo "  clean         - Clean build artifacts"
	@echo "  update-deps   - Update Python dependencies"
	@echo "  build         - Build distribution packages"
	@echo "  publish       - Publish to PyPI (requires auth)"

setup:
	uv sync --all-extras --dev --group examples --locked

test:
	uv run pytest

test-watch:
	@command -v pytest-watch >/dev/null 2>&1 || uv add --dev pytest-watch
	uv run pytest-watch

test-coverage:
	uv run pytest --cov=lilypad --cov-report=html --cov-report=term

lint:
	uv run ruff check .

typecheck-examples:
	uv run --group examples -- pyright examples

typecheck-sdk:
	uv run pyright src/lilypad tests

typecheck: typecheck-sdk typecheck-examples

format:
	uv run ruff format .

fix:
	uv run ruff check --fix --unsafe-fixes .

clean:
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ *.egg-info/ htmlcov/ .coverage || true

update-deps:
	uv lock --upgrade
	uv sync --all-extras --dev

build:
	uv build

publish: build
	@echo "Publishing to PyPI..."
	uv publish
