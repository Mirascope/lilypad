# Lilypad

An open-source prompt engineering framework.

> [!IMPORTANT]
> We're looking for early design partners!
> If you're interested, [join our community](https://join.slack.com/t/mirascope-community/shared_invite/zt-2ilqhvmki-FB6LWluInUCkkjYD3oSjNA) and DM William Bakst :)

> [!WARNING]  
> This project is in its alpha phase of development.
> This means that things like the user interface, database schemas, etc. are subject to change.

## Installation

> [!NOTE]
> We currently only support OpenAI. If there are particular providers you would like us to support, let us know!

```bash
pip install "python-lilypad[openai]"
lilypad --install-completion  # auto-complete for the CLI
```

Once installed, navigate to the root directory where you'll be developing your application and run:

```bash
lilypad start
```

This will initialize your project, create a local SQLite database, and spin up a local server.

## Quickstart: Synced LLM Functions

The core feature `lilypad` has to offer is what we called Synced LLM Functions.

First, create a new prompt:

```bash
lilypad create recommend_book
```

This will create the following shim:

```python
# lily/recommend_book.py
import lilypad


@lilypad.synced.llm_fn()
def recommend_book() -> str: ...


if __name__ == "__main__":
    output = recommend_book()
    print(output)
```

Next, edit the shim to take any template variables you want to use. For example, we can add genre:

```python
# lily/recommend_book.py
import lilypad


@lilypad.synced.llm_fn()
def recommend_book(genre: str) -> str: ...


if __name__ == "__main__":
    output = recommend_book("fantasy")
    print(output)
```

Now you can run the function, which will open the editor:

```bash
lilypad run recommend_book
```

Once you hit submit, this will run the function, automatically versioning and tracing everything.

Run running an LLM function, any changes to the shim will get detected automatically and always open the editor. If you want to edit the prompt without changing the shim, simply use the `--edit` flag:

```bash
lilypad run --edit recommend_book
```

## Coming Soon

There are a lot of things on our roadmap, so if there are particular features you want to see, raise an issue and let us know!

Top of mind are:
1. Automatic versioning/tracing of non-synced functions (i.e. using OpenAI directly). We had an early version of this, but it's currently broken
2. More support for API interactions through synced functions (such as computed fields).
3. Evaluations
