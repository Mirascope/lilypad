# All targets
.PHONY: help setup generate-sdk clean update-deps

help:
	@echo "Available targets:"
	@echo "  setup        - Install dependencies"
	@echo "  generate-sdk - Generate Python SDK from OpenAPI"
	@echo "  clean        - Clean generated artifacts"
	@echo "  update-deps  - Update Bun dependencies"

setup:
	bun install

generate-sdk:
	bun run fern generate --group python-sdk --local && rm -fr python/src/lilypad/.git

clean:
	rm -rf python/src/lilypad/.git || true

update-deps:
	bun update --latest
	@echo "Dependencies updated. Don't forget to test the changes!"
