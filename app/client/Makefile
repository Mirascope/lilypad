.PHONY: help setup dev build build-notypescript build-local lint typecheck preview prettier generate-api-v0 storybook build-storybook clean test test-watch test-coverage update-deps analyze

help:
	@echo "Available targets:"
	@echo "  setup              - Install dependencies"
	@echo "  dev                - Start development server"
	@echo "  build              - Build for production"
	@echo "  build-notypescript - Build without TypeScript checking"
	@echo "  build-local        - Build for local environment"
	@echo "  lint               - Run linter"
	@echo "  typecheck          - Run type checker"
	@echo "  preview            - Preview production build"
	@echo "  prettier           - Format code with Prettier"
	@echo "  generate-api-v0    - Generate API v0 types"
	@echo "  storybook          - Start Storybook"
	@echo "  build-storybook    - Build Storybook"
	@echo "  clean              - Clean build artifacts"
	@echo "  test               - Run tests"
	@echo "  test-watch         - Run tests in watch mode"
	@echo "  test-coverage      - Run tests with coverage"
	@echo "  update-deps        - Update JavaScript dependencies"
	@echo "  analyze            - Analyze bundle size"

setup:
	bun install

dev:
	bun run dev

build:
	bun run build

build-notypescript:
	bun run build:notypescript

build-local:
	bun run build:local

lint:
	bun run lint

typecheck:
	bun run typecheck

preview:
	bun run preview

prettier:
	bun run prettier

generate-api-v0:
	bun run generate:api:v0

storybook:
	bun run storybook

build-storybook:
	bun run build-storybook

clean:
	rm -rf dist/ build/ node_modules/.cache/ || true

test:
	bun run test

test-watch:
	bun run test:watch

test-coverage:
	bun run test:coverage

update-deps:
	bun update

analyze:
	bun run build --mode analyze
