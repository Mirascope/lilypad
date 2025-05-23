
all: generate-all-client

openapi-generator-cli.jar:
	curl -L https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/7.13.0/openapi-generator-cli-7.13.0.jar \
		-o openapi-generator-cli.jar

openapi.json:
	uv run scripts/generate_python_client_schema.py generate-openapi --output openapi.json


generate-all-client: generate-python-client generate-typescript-client

generate-python-client: openapi-generator-cli.jar openapi.json
	# Generate a python client using the OpenAPI Generator CLI
	rm -fr sdks/python && \
	java -jar openapi-generator-cli.jar generate \
  		-i openapi.json \
  		-g python \
  		-o sdks/python \
  		--additional-properties=packageName=lilypad,projectName=lilypad,useTags=true,removeOperationIdPrefix=true,generateSourceCodeOnly=true
