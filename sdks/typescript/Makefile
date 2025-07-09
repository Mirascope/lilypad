# All targets
.PHONY: help setup build dev test test-coverage test-watch lint typecheck format fix check clean update-deps

help:
	@echo "Available targets:"
	@echo "  setup         - Install dependencies"
	@echo "  build         - Build the TypeScript SDK"
	@echo "  dev           - Build in watch mode"
	@echo "  test          - Run tests"
	@echo "  test-coverage - Run tests with coverage"
	@echo "  test-watch    - Run tests in watch mode"
	@echo "  lint          - Run ESLint"
	@echo "  typecheck     - Run TypeScript type checker"
	@echo "  format        - Format code with Prettier"
	@echo "  fix           - Auto-fix linting and formatting issues"
	@echo "  check         - Run all checks (lint, typecheck, format check)"
	@echo "  clean         - Clean build artifacts"
	@echo "  update-deps   - Update dependencies"

setup:
	bun install

build:
	bun run build

dev:
	bun run dev

test:
	bun run test

test-coverage:
	bun run test:coverage

test-watch:
	bun run test --watch

lint:
	bun run lint

typecheck:
	bun run typecheck

format:
	bun run format

format-check:
	bun run format:check

fix:
	bun run fix

check: lint typecheck format-check
	@echo "All checks passed!"

clean:
	rm -rf dist coverage node_modules .turbo
	rm -rf lilypad/generated/.git || true

update-deps:
	bun update --latest
	@echo "Dependencies updated. Don't forget to test the changes!"