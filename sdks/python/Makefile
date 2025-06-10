.PHONY: help setup test lint typecheck format fix clean

help:
	@echo "Available targets:"
	@echo "  setup     - Install dependencies"
	@echo "  test      - Run tests"
	@echo "  lint      - Run linter"
	@echo "  typecheck - Run type checker"
	@echo "  format    - Format code"
	@echo "  fix       - Auto-fix linting issues"
	@echo "  clean     - Clean build artifacts"

setup:
	uv sync --all-extras --dev

test:
	uv run pytest

lint:
	uv run ruff check .

typecheck:
	uv run pyright src/lilypad tests

format:
	uv run ruff format .

fix:
	uv run ruff check --fix --unsafe-fixes .

clean:
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
