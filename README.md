# Lilypad

Hopefully something cool and useful lol

## For the demo

### Create DB (One time only)

cd lilypad/server
`uv run db/setup.py` 

### Run backend

`fastapi dev`

### Run example

cd lilypad/example
`uv run synced.py`
or any example w/ `synced.prompt`

### The traces url

http://127.0.0.1:8000/lilypad/traces

### Edit the prompt template

Replace `LLM_FUNCTION_ID` with number (most likely 1)
http://127.0.0.1:8000/lilypad/llmFunctions/{LLM_FUNCTION_ID}/providerCallParams

### Install VSCode extension

SQLite3 Editor by yy0931

When you open `database.db` you can view the SQL tables, easier.
