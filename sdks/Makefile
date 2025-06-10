.PHONY: setup generate-sdk clean

setup:
	bun install

generate-sdk:
	bun run fern generate --group python-sdk --local && rm -fr python/src/lilypad/.git

clean:
	rm -rf python/src/lilypad/.git || true