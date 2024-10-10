# Lilypad

!!! warning "Project is in alpha phase"

    This means that things like the user interface, database schemas, etc. are still subject to change. We do not yet recommend fully relying on this project in production, but we've found it works quite well for local development in its current stage.

An open-source prompt engineering framework built on these principles:

- Prompt engineering is an optimization process, which requires...
- Automatic versioning and tracing
- Developer-centric prompt template editor
- Proper syncing between prompts and code

!!! info "We're looking for early design partners!"

    We are also working on tooling for improved collaboration between technical and non-technical team members. This is particularly important for involving domain experts who may not have the technical chops to contribute to a code base.

    If you're interested, [join our community](https://join.slack.com/t/mirascope-community/shared_invite/zt-2ilqhvmki-FB6LWluInUCkkjYD3oSjNA) and DM William Bakst :)

    There are limited spots.

## 30 Second Quickstart

Install Lilypad, specifying the provider(s) you intend to use, and set your API key:

!!! lily ""

    {% set operating_systems = ["MacOS / Linux", "Windows"] %}
    {% for os in operating_systems %}
    === "{{ os }}"

        {% for provider in supported_llm_providers %}
        === "{{ provider }}"

            ```bash
            pip install "python-lilypad[{{ provider | provider_dir }}]==0.0.1"
            {% if os == "Windows" %}set {{ upper(provider | provider_dir) }}_API_KEY=XXXXX
            {% else %}export {{ upper(provider | provider_dir) }}_API_KEY=XXXXX
            {% endif %}
            ```
        {% endfor %}

    {% endfor %}

Create your first synced prompt to recommend a book.

For example, you could use the prompt `Recommend a fantasy book`:

!!! lily ""

    ```bash
    lilypad start                  # initialize local project
    lilypad create recommend_book  # creates a synced LLM function
    lilypad run recommend_book     # runs the function (and opens editor)
    ```

Once you hit "Submit" you'll see the function run in your shell. Follow the link to see the version and trace in an interactive UI.

Next, try editing the function signature to take a `genre: str` argument. When you run the function again it will open the editor and give you access to the `{genre}` template variable (with autocomplete).

## Features

!!! note ""

    <div align="center">We are working on updating this section, which covers the basics for now</div>

### Official SDK Usage

You can use the `lilypad.llm_fn` decorator on any function that uses an LLM API to generate it's response. This function will then be versioned and traced automatically for you, all the way through the entire lexical closure:

!!! lily ""

    {% for provider in supported_llm_providers %}
    === "{{ provider }}"

        ```python hl_lines="7"
        --8<-- "examples/features/official_sdk/{{ provider | provider_dir }}_function.py"
        ```
    {% endfor %}

### Synced LLM Function Usage

Setting `synced=True` in the `lilypad.llm_fn` decorator indicates that the decorated function should be synced. The result is that only the function definition / signature will be used and everything else that goes into calling the LLM API (i.e. the prompt) lives in the database.

!!! lily ""

    ```python hl_lines="4"
    --8<-- "examples/features/synced_function/basic_call.py"
    ```

Note that this is truly just a shim where _everything_ lives externally -- down to the provider and model to be used.

You can also change the return type of the shim and it will be automatically handled:

!!! lily ""

    ```python hl_lines="11"
    --8<-- "examples/features/synced_function/response_model.py"
    ```
