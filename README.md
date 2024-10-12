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

This project is currently licensed under the terms of the [MIT License](https://github.com/Mirascope/mirascope/blob/main/LICENSE); however, we expect certain future features to be licensed separately, which we will make extremely clear and evident.
