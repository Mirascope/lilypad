[![Lilypad Logo & Wordmark](https://github.com/user-attachments/assets/c8ba44ca-3e6c-40b1-af3b-4ecf9b69ebc5)](https://mirascope.com/#lilypad)

<p align="center">
    <a href="https://github.com/Mirascope/lilypad/actions/workflows/tests.yml" target="_blank"><img src="https://github.com/Mirascope/lilypad/actions/workflows/tests.yml/badge.svg?branch=main" alt="Tests"/></a>
    <a href="https://mirascope.com/docs/lilypad" target="_blank"><img src="https://img.shields.io/badge/docs-available-brightgreen" alt="Docs"/></a>
    <a href="https://github.com/Mirascope/lilypad/stargazers" target="_blank"><img src="https://img.shields.io/github/stars/Mirascope/lilypad.svg" alt="Stars"/></a>
</p>

---

An open-source LLM engineering platform built on these principles:

- Building with LLMs introduces non-determinisim to your code, which requires...
- Tracking all input/output pairs and the exact version of the code that produced them so you can...
- Continuously evaluate and optimize your code.

> [!IMPORTANT]
> __Lilypad is still in beta__
>
> If you're interested in participating in the closed beta of Lilypad Pro+, [join our community](https://join.slack.com/t/mirascope-community/shared_invite/zt-2ilqhvmki-FB6LWluInUCkkjYD3oSjNA) and DM William Bakst :)
>
> We also welcome contributions with open arms! If you're interested in [contributing](https://github.com/Mirascope/lilypad/tree/main/CONTRIBUTING.md), just do it! We're here to help.

## Quickstart

To get started with Lilypad:

1. Create an account at <https://lilypad.mirascope.com>. You can also [run Lilypad locally](https://lilypad.so/self-hosting) if you'd prefer.
2. Navigate to [your organization settings](https://lilypad.mirascope.com/settings/org)
3. Create a project, and then create an API key for that project.
    a. Save your `LILYPAD_PROJECT_ID` and `LILYPAD_API_KEY` (e.g. in a `.env` file).
4. Install Lilypad: `uv add "lilypad-sdk[openai]"  # specify your provider of choice`
5. Run and trace your first versioned function:

```python
import os

import lilypad
from openai import OpenAI  # use your provider of choice

lilypad.configure(
    project_id=os.environ["LILYPAD_PROJECT_ID"],
    api_key=os.environ["LILYPAD_API_KEY"],
    auto_llm=True,
)
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


@lilypad.trace(versioning="automatic")  # Automatically version (non-deterministic) functions
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

We are actively working on this library and it's documentation, which you can find [here](https://mirascope.com/docs/lilypad)

## Versioning

Lilypad uses [Semantic Versioning](https://semver.org/)

## License

This project uses a dual-license model:

### Open-Source License (MIT)

Except for the contents and code contained in any `ee` directory or sub-directory of this repository, which is covered by a commercial license (see below), all code in this repository is licensed under the terms of the [MIT License](https://github.com/Mirascope/lilypad/tree/main/LICENSE).

### Enterprise Edition (EE) License

The contents and code of any `ee` directory or sub-directory of this repository are licensed under the Enterprise Edition (EE) License. This content and code is only available to users using Lilypad Cloud or those with a valid Enterprise Edition (EE) License. See [ee/LICENSE](https://github.com/Mirascope/lilypad/tree/main/ee/LICENSE) for the full terms.

__Self-Hosting:__

For those looking to self-host the Enterprise Edition (EE) of Lilypad, please reach out to <sales@mirascope.com>.

You can find more information about self-hosting [here](https://mirascope.com/docs/lilypad/getting-started/self-hosting).
