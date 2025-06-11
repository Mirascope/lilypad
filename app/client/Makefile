# Development & Build
.PHONY: help setup dev build build-notypescript build-local preview

# Code Quality
.PHONY: lint typecheck prettier


# Tools
.PHONY: generate-api-v0 storybook build-storybook analyze

# Maintenance
.PHONY: clean update-deps

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

update-deps:
	bun update --latest
	@echo "Dependencies updated. Don't forget to test the changes!"

analyze:
	@echo "Note: Bundle analysis requires rollup-plugin-visualizer"
	@echo "Install with: bun add -d rollup-plugin-visualizer"
	@echo "Then add the plugin to vite.config.ts"
	bun run build
