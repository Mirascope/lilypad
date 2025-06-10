.PHONY: setup test lint typecheck format fix clean

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