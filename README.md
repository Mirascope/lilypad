# Lilypad

> [!WARNING]
> __Project is in alpha phase__
> 
> This means that things like the user interface, database schemas, etc. are still subject to change. We do not yet recommend fully relying on this project in production, but we've found it works quite well for local development in its current stage.

An open-source prompt engineering framework built on these principles:

- Prompt engineering is an optimization process, which requires...
- Automatic versioning and tracing
- Developer-centric prompt template editor
- Proper syncing between prompts and code

> [!IMPORTANT]
> __We're looking for early design partners!__
> 
> We are also working on tooling for improved collaboration between technical and non-technical team members. This is particularly important for involving domain experts who may not have the technical chops to contribute to a code base.
>
> If you're interested, [join our community](https://join.slack.com/t/mirascope-community/shared_invite/zt-2ilqhvmki-FB6LWluInUCkkjYD3oSjNA) and DM William Bakst :)
>
> There are limited spots.

## 30 Second Quickstart

Install Lilypad, specifying the provider(s) you intend to use, and set your API key:

```bash
pip install "python-lilypad[openai]"

export OPENAI_API_KEY=XXXXX
```

Create your first synced prompt to recommend a book.

For example, you could use the prompt `Recommend a fantasy book`:

```bash
lilypad start                  # initialize local project
lilypad create recommend_book  # creates a synced LLM function
lilypad run recommend_book     # runs the function (and opens editor)
```

Once you hit "Submit" you'll see the function run in your shell. Follow the link to see the version and trace in an interactive UI.

Next, try editing the function signature to take a `genre: str` argument. When you run the function again it will open the editor and give you access to the `{genre}` template variable (with autocomplete).

## Usage

We are actively working on this library and it's documentation, which you can find [here](https://lilypad.mirascope.com/docs)

## Versioning

Lilypad uses [Semantic Versioning](https://semver.org/)

## License

This project uses a dual-license model:

### Open-Source License (MIT)

Except for the contents and code contained in any `/ee` directory, which is covered by a commercial license (see below), all code in this repository is licensed under the terms of the [MIT License](https://github.com/Mirascope/lilypad/blob/main/LICENSE).

### Enterprise Edition License

The contents of any `/ee` directory are licensed under the Enterprise Edition License. This code is only available to users with a valid enterprise license. See [`lilypad/ee/LICENSE`](https://github.com/Mirascope/lilypad/blob/main/lilypad/ee/LICENSE) for the full terms.

__Enterprise Features:__

Stay tuned...

__Obtaining An Enterprise License:__

To purchase an enterprise license, please contact william@mirascope.io

__License Validation:__

Enterprise features require a valid license key for activation. Self-hosted installations will validate licenses against using offline activation.
