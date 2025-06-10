.PHONY: help setup generate-sdk clean

help:
	@echo "Available targets:"
	@echo "  setup        - Install dependencies"
	@echo "  generate-sdk - Generate Python SDK from OpenAPI"
	@echo "  clean        - Clean generated artifacts"

setup:
	bun install

generate-sdk:
	bun run fern generate --group python-sdk --local && rm -fr python/src/lilypad/.git

clean:
	rm -rf python/src/lilypad/.git || true
