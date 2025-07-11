# All targets
.PHONY: help setup generate-sdk generate-sdk-python generate-sdk-typescript clean update-deps

help:
	@echo "Available targets:"
	@echo "  setup                - Install dependencies"
	@echo "  generate-sdk         - Generate all SDKs (Python and TypeScript) from OpenAPI"
	@echo "  generate-sdk-python  - Generate Python SDK from OpenAPI"
	@echo "  generate-sdk-typescript - Generate TypeScript SDK from OpenAPI"
	@echo "  clean                - Clean generated artifacts"
	@echo "  update-deps          - Update Bun dependencies"

setup:
	bun install

generate-sdk: generate-sdk-python generate-sdk-typescript

generate-sdk-python:
	bun run fern generate --group python-sdk --local && rm -fr python/src/lilypad/.git

generate-sdk-typescript:
	bun run fern generate --group typescript-sdk --local && rm -fr typescript/lilypad/generated/.git
	cd typescript && bun run prettier --write lilypad/generated --log-level=error || true
	@echo "Fixing generated TypeScript exports..."
	@sed -i.bak 's/export { BinaryResponse }/export type { BinaryResponse }/g' typescript/lilypad/generated/core/fetcher/index.ts && rm typescript/lilypad/generated/core/fetcher/index.ts.bak
	@sed -i.bak '/export type { BinaryResponse }/a\
export { getBinaryResponse } from "./BinaryResponse.js";' typescript/lilypad/generated/core/fetcher/index.ts && rm typescript/lilypad/generated/core/fetcher/index.ts.bak
	@echo "Building TypeScript SDK after generation..."
	cd typescript && bun run build

clean:
	rm -rf python/src/lilypad/.git || true
	rm -rf typescript/lilypad/generated/.git || true

update-deps:
	bun update --latest
	@echo "Dependencies updated. Don't forget to test the changes!"
