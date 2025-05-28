"""Mock OpenAI API key for testing purposes."""

import os

os.environ["OPENAI_API_KEY"] = "test"
os.environ["LILYPAD_VERSIONING_INCLUDE_DOCSTRINGS"] = "false"
