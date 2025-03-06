# Lilypad

An open-source LLM engineering platform built on these principles:

- Building with LLMs introduces non-determinisim to your code, which requires...
- Tracking all input/output pairs and the exact version of the code that produced them so you can...
- Continuously evaluate and optimize your code, which requires...
- Involving business users and domain experts.

> [!IMPORTANT]
> __Lilypad is still in beta__
>
> This means that things like the user interface, database schemas, etc. are still subject to change. We do not yet recommend fully relying on this project in production, but we've found it works quite well in its current stage.
>
> If you're interested in participating in the closed beta of Lilypad Pro, [join our community](https://join.slack.com/t/mirascope-community/shared_invite/zt-2ilqhvmki-FB6LWluInUCkkjYD3oSjNA) and DM William Bakst :)
>
> We also welcome contributions with open arms! If you're interested in [contributing](https://github.com/Mirascope/lilypad/tree/main/CONTRIBUTING.md), just do it! We're here to help.

## Quickstart

To get started with Lilypad:

1. Create an account at <https://app.lilypad.so>. You can also [run Lilypad locally](https://lilypad.so/self-hosting) if you'd prefer.
2. Navigate to [your organization settings](https://app.lilypad.so/settings/org)
3. Create a project, and then create an API key for that project.
    a. Save your `LILYPAD_PROJECT_ID` and `LILYPAD_API_KEY` (e.g. in a `.env` file).
4. Install Lilypad: `uv add "python-lilypad[openai]"  # specify your provider of choice`
5. Run your first generation:

```python
import os

import lilypad
from openai import OpenAI  # use your provider of choice

os.environ["LILYPAD_PROJECT_ID"] = "..."
os.environ["LILYPAD_API_KEY"] = "..."
os.environ["OPENAI_API_KEY"] = "..."

lilypad.configure()    # Automatically trace LLM API calls
client = OpenAI()


@lilypad.generation()  # Automatically version non-deterministic functions
def answer_question(question: str) -> str | None:
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Answer this question: {question}"},
        ],
    )
    return completion.choices[0].message.content


answer = answer_question("What is the capital of France?")
print(answer)
# > The capital of France is Paris.
```

And that's it! Now you've versioned and traced your first non-deterministic function with Lilypad.

## Usage

We are actively working on this library and it's documentation, which you can find [here](https://lilypad.so/docs)

## Versioning

Lilypad uses [Semantic Versioning](https://semver.org/)

## License

This project uses a dual-license model:

### Open-Source License (MIT)

Except for the contents and code contained in any `ee` directory or sub-directory of this repository, which is covered by a commercial license (see below), all code in this repository is licensed under the terms of the [MIT License](https://github.com/Mirascope/lilypad/tree/main/LICENSE).

### Enterprise Edition (EE) License

The contents and code of any `ee` directory or sub-directory of this repository are licensed under the Enterprise Edition (EE) License. This content and code is only available to users using the Lilypad App or those with a valid Enterprise Edition (EE) License. See [ee/LICENSE](https://github.com/Mirascope/lilypad/tree/main/ee/LICENSE) for the full terms.

__Self-Hosting:__

For those looking to self-host the Enterprise Edition (EE) of Lilypad, please reach out to <sales@mirascope.com>.

You can find more information about self-hosting [here](https://lilypad.so/self-hosting).
