.PHONY: setup dev build build-notypescript build-local lint typecheck preview prettier generate-api storybook build-storybook clean

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

generate-api:
	bun run generate:api:v0

storybook:
	bun run storybook

build-storybook:
	bun run build-storybook

clean:
	rm -rf dist/ build/ node_modules/.cache/ || true