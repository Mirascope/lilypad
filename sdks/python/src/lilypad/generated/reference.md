# Reference
<details><summary><code>client.<a href="src/mirascope/client.py">create_customer_portal_stripe_customer_portal_post</a>()</code></summary>
<dl>
<dd>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.create_customer_portal_stripe_customer_portal_post()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/mirascope/client.py">create_checkout_session_stripe_create_checkout_session_post</a>(...)</code></summary>
<dl>
<dd>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.create_checkout_session_stripe_create_checkout_session_post(
    tier=1,
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**tier:** `Tier` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/mirascope/client.py">get_event_summaries_stripe_event_summaries_get</a>()</code></summary>
<dl>
<dd>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.get_event_summaries_stripe_event_summaries_get()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/mirascope/client.py">get_span_projects_project_uuid_spans_span_identifier_get</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get span by uuid or span_id.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.get_span_projects_project_uuid_spans_span_identifier_get(
    project_uuid="project_uuid",
    span_identifier="span_identifier",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**span_identifier:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**environment_uuid:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.<a href="src/mirascope/client.py">get_spans_by_trace_id_projects_project_uuid_traces_by_trace_id_trace_id_get</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get all spans for a given trace ID.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.get_spans_by_trace_id_projects_project_uuid_traces_by_trace_id_trace_id_get(
    project_uuid="project_uuid",
    trace_id="trace_id",
    environment_uuid="environment_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**trace_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**environment_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Organizations
<details><summary><code>client.organizations.<a href="src/mirascope/organizations/client.py">update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update an organization.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.organizations.update()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**name:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**license:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.organizations.<a href="src/mirascope/organizations/client.py">create</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create an organization.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.organizations.create(
    name="name",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.organizations.<a href="src/mirascope/organizations/client.py">delete</a>()</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete an organization.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.organizations.delete()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## ApiKeys
<details><summary><code>client.api_keys.<a href="src/mirascope/api_keys/client.py">list</a>()</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get an API keys.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.api_keys.list()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.api_keys.<a href="src/mirascope/api_keys/client.py">create</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create an API key and returns the full key.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.api_keys.create(
    name="name",
    project_uuid="project_uuid",
    environment_uuid="environment_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**environment_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**expires_at:** `typing.Optional[dt.datetime]` 
    
</dd>
</dl>

<dl>
<dd>

**key_hash:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.api_keys.<a href="src/mirascope/api_keys/client.py">delete</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete an API key.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.api_keys.delete(
    api_key_uuid="api_key_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**api_key_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Webhooks
<details><summary><code>client.webhooks.<a href="src/mirascope/webhooks/client.py">handle_stripe</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Handle Stripe webhook events.

This endpoint receives webhook events from Stripe and updates the billing records.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.webhooks.handle_stripe()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**stripe_signature:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Projects
<details><summary><code>client.projects.<a href="src/mirascope/projects/client.py">list</a>()</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get all projects.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.list()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.<a href="src/mirascope/projects/client.py">create</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a project
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.create(
    name="name",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.<a href="src/mirascope/projects/client.py">get</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get a project.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.get(
    project_uuid="project_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.<a href="src/mirascope/projects/client.py">delete</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete a project
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.delete(
    project_uuid="project_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.<a href="src/mirascope/projects/client.py">update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update a project.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.update(
    project_uuid="project_uuid",
    name="name",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Spans
<details><summary><code>client.spans.<a href="src/mirascope/spans/client.py">get</a>(...)</code></summary>
<dl>
<dd>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.spans.get(
    span_uuid="span_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**span_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.spans.<a href="src/mirascope/spans/client.py">update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update span by uuid.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.spans.update(
    span_uuid="span_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**span_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**tags_by_uuid:** `typing.Optional[typing.Sequence[str]]` 
    
</dd>
</dl>

<dl>
<dd>

**tags_by_name:** `typing.Optional[typing.Sequence[str]]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Auth
<details><summary><code>client.auth.<a href="src/mirascope/auth/client.py">handle_github_callback</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Callback for GitHub OAuth.

Saves the user and organization or retrieves the user after authenticating
with GitHub.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.auth.handle_github_callback(
    code="code",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**code:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.auth.<a href="src/mirascope/auth/client.py">handle_google_callback</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Callback for Google OAuth.

Saves the user and organization or retrieves the user after authenticating
with Google.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.auth.handle_google_callback(
    code="code",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**code:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Users
<details><summary><code>client.users.<a href="src/mirascope/users/client.py">set_active_organization</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update users active organization uuid.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.users.set_active_organization(
    active_organization_uuid="activeOrganizationUuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**active_organization_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.users.<a href="src/mirascope/users/client.py">update_api_keys</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update users keys.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.users.update_api_keys(
    request={"key": "value"},
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request:** `typing.Dict[str, typing.Optional[typing.Any]]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.users.<a href="src/mirascope/users/client.py">get_current_user</a>()</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get user.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.users.get_current_user()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## ExternalApiKeys
<details><summary><code>client.external_api_keys.<a href="src/mirascope/external_api_keys/client.py">list</a>()</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List all external API keys for the user with masked values.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.external_api_keys.list()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.external_api_keys.<a href="src/mirascope/external_api_keys/client.py">create</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Store an external API key for a given service.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.external_api_keys.create(
    service_name="service_name",
    api_key="api_key",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**service_name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**api_key:** `str` — New API key
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.external_api_keys.<a href="src/mirascope/external_api_keys/client.py">get</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Retrieve an external API key for a given service.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.external_api_keys.get(
    service_name="service_name",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**service_name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.external_api_keys.<a href="src/mirascope/external_api_keys/client.py">delete</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete an external API key for a given service.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.external_api_keys.delete(
    service_name="service_name",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**service_name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.external_api_keys.<a href="src/mirascope/external_api_keys/client.py">update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update users keys.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.external_api_keys.update(
    service_name="service_name",
    api_key="api_key",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**service_name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**api_key:** `str` — New API key
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Environments
<details><summary><code>client.environments.<a href="src/mirascope/environments/client.py">list</a>()</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get all environments for a project.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.environments.list()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.environments.<a href="src/mirascope/environments/client.py">create</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a new environment.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.environments.create(
    name="name",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**description:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**is_development:** `typing.Optional[bool]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.environments.<a href="src/mirascope/environments/client.py">get</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get environment by UUID.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.environments.get(
    environment_uuid="environment_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**environment_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.environments.<a href="src/mirascope/environments/client.py">delete</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete an environment.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.environments.delete(
    environment_uuid="environment_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**environment_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## UserConsents
<details><summary><code>client.user_consents.<a href="src/mirascope/user_consents/client.py">create</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Store user consent.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.user_consents.create(
    privacy_policy_version="privacy_policy_version",
    tos_version="tos_version",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**privacy_policy_version:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**tos_version:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**privacy_policy_accepted_at:** `typing.Optional[dt.datetime]` 
    
</dd>
</dl>

<dl>
<dd>

**tos_accepted_at:** `typing.Optional[dt.datetime]` 
    
</dd>
</dl>

<dl>
<dd>

**user_uuid:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.user_consents.<a href="src/mirascope/user_consents/client.py">update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update user consent.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.user_consents.update(
    user_consent_uuid="user_consent_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**user_consent_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**privacy_policy_version:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**privacy_policy_accepted_at:** `typing.Optional[dt.datetime]` 
    
</dd>
</dl>

<dl>
<dd>

**tos_version:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**tos_accepted_at:** `typing.Optional[dt.datetime]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Tags
<details><summary><code>client.tags.<a href="src/mirascope/tags/client.py">list</a>()</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get all tags.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.tags.list()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.tags.<a href="src/mirascope/tags/client.py">create</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a tag
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.tags.create(
    name="name",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**project_uuid:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.tags.<a href="src/mirascope/tags/client.py">get</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get a tag.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.tags.get(
    tag_uuid="tag_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**tag_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.tags.<a href="src/mirascope/tags/client.py">delete</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete a tag
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.tags.delete(
    tag_uuid="tag_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**tag_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.tags.<a href="src/mirascope/tags/client.py">update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update a tag.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.tags.update(
    tag_uuid="tag_uuid",
    name="name",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**tag_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**project_uuid:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Comments
<details><summary><code>client.comments.<a href="src/mirascope/comments/client.py">list</a>()</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get all comments.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.comments.list()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.comments.<a href="src/mirascope/comments/client.py">create</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a comment
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.comments.create(
    text="text",
    span_uuid="span_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**text:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**span_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**parent_comment_uuid:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.comments.<a href="src/mirascope/comments/client.py">get</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get a comment.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.comments.get(
    comment_uuid="comment_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**comment_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.comments.<a href="src/mirascope/comments/client.py">delete</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete a comment
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.comments.delete(
    comment_uuid="comment_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**comment_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.comments.<a href="src/mirascope/comments/client.py">update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update a comment.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.comments.update(
    comment_uuid="comment_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**comment_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**text:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**is_edited:** `typing.Optional[bool]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Settings
<details><summary><code>client.settings.<a href="src/mirascope/settings/client.py">get</a>()</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get the configuration.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.settings.get()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Ee Organizations
<details><summary><code>client.ee.organizations.<a href="src/mirascope/ee/organizations/client.py">get_license</a>()</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get the license information for the organization
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.ee.organizations.get_license()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.ee.organizations.<a href="src/mirascope/ee/organizations/client.py">list</a>()</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get all user organizations.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.ee.organizations.list()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.ee.organizations.<a href="src/mirascope/ee/organizations/client.py">create</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create user organization
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.ee.organizations.create(
    token="token",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**token:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.ee.organizations.<a href="src/mirascope/ee/organizations/client.py">delete</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete user organization by uuid
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.ee.organizations.delete(
    user_organization_uuid="user_organization_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**user_organization_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Ee Organizations Users
<details><summary><code>client.ee.organizations.users.<a href="src/mirascope/ee/organizations/users/client.py">list</a>()</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get all users of an organization.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.ee.organizations.users.list()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Ee Projects Annotations
<details><summary><code>client.ee.projects.annotations.<a href="src/mirascope/ee/projects/annotations/client.py">list</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get annotations by project.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.ee.projects.annotations.list(
    project_uuid="project_uuid",
    environment_uuid="environment_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**environment_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.ee.projects.annotations.<a href="src/mirascope/ee/projects/annotations/client.py">create</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create an annotation.

Args:
    project_uuid: The project UUID.
    annotations_service: The annotation service.
    project_service: The project service.
    annotations_create: The annotation create model.

Returns:
    AnnotationPublic: The created annotation.

Raises:
    HTTPException: If the span has already been assigned to a user and has
    not been labeled yet.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import AnnotationCreate, Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.ee.projects.annotations.create(
    project_uuid="project_uuid",
    request=[AnnotationCreate()],
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request:** `typing.Sequence[AnnotationCreate]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.ee.projects.annotations.<a href="src/mirascope/ee/projects/annotations/client.py">delete</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete an annotation.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.ee.projects.annotations.delete(
    annotation_uuid="annotation_uuid",
    project_uuid="project_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**annotation_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.ee.projects.annotations.<a href="src/mirascope/ee/projects/annotations/client.py">update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update an annotation.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.ee.projects.annotations.update(
    annotation_uuid="annotation_uuid",
    project_uuid="project_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**annotation_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**label:** `typing.Optional[Label]` 
    
</dd>
</dl>

<dl>
<dd>

**reasoning:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**type:** `typing.Optional[EvaluationType]` 
    
</dd>
</dl>

<dl>
<dd>

**data:** `typing.Optional[typing.Dict[str, typing.Optional[typing.Any]]]` 
    
</dd>
</dl>

<dl>
<dd>

**assigned_to:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Ee Projects Spans
<details><summary><code>client.ee.projects.spans.<a href="src/mirascope/ee/projects/spans/client.py">generate_annotation</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Stream function.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.ee.projects.spans.generate_annotation(
    span_uuid="span_uuid",
    project_uuid="project_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**span_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Ee Projects Functions
<details><summary><code>client.ee.projects.functions.<a href="src/mirascope/ee/projects/functions/client.py">run_playground</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Executes a function with specified parameters in a secure playground environment.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.ee.projects.functions.run_playground(
    project_uuid="project_uuid",
    function_uuid="function_uuid",
    arg_values={"key": 1},
    provider="openai",
    model="model",
    prompt_template="prompt_template",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**function_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**arg_values:** `typing.Dict[str, PlaygroundParametersArgValuesValue]` 
    
</dd>
</dl>

<dl>
<dd>

**provider:** `Provider` 
    
</dd>
</dl>

<dl>
<dd>

**model:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**prompt_template:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**environment_uuid:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**arg_types:** `typing.Optional[typing.Dict[str, typing.Optional[str]]]` 
    
</dd>
</dl>

<dl>
<dd>

**call_params:** `typing.Optional[CommonCallParams]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Ee Projects Functions Annotations
<details><summary><code>client.ee.projects.functions.annotations.<a href="src/mirascope/ee/projects/functions/annotations/client.py">list</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get annotations by functions.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.ee.projects.functions.annotations.list(
    project_uuid="project_uuid",
    function_uuid="function_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**function_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.ee.projects.functions.annotations.<a href="src/mirascope/ee/projects/functions/annotations/client.py">get_metrics</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get annotation metrics by function.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.ee.projects.functions.annotations.get_metrics(
    function_uuid="function_uuid",
    project_uuid="project_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**function_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Ee Projects Spans Annotations
<details><summary><code>client.ee.projects.spans.annotations.<a href="src/mirascope/ee/projects/spans/annotations/client.py">list</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get annotations by functions.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.ee.projects.spans.annotations.list(
    project_uuid="project_uuid",
    span_uuid="span_uuid",
    environment_uuid="environment_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**span_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**environment_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Organizations Invites
<details><summary><code>client.organizations.invites.<a href="src/mirascope/organizations/invites/client.py">list</a>()</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get an organization invite.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.organizations.invites.list()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.organizations.invites.<a href="src/mirascope/organizations/invites/client.py">get</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get an organization invite.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.organizations.invites.get(
    invite_token="invite_token",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**invite_token:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.organizations.invites.<a href="src/mirascope/organizations/invites/client.py">create</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create an organization invite.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.organizations.invites.create(
    invited_by="invited_by",
    email="email",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**invited_by:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**email:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**expires_at:** `typing.Optional[dt.datetime]` 
    
</dd>
</dl>

<dl>
<dd>

**token:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**resend_email_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**organization_uuid:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.organizations.invites.<a href="src/mirascope/organizations/invites/client.py">remove</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Remove an organization invite.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.organizations.invites.remove(
    organization_invite_uuid="organization_invite_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**organization_invite_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Projects Functions
<details><summary><code>client.projects.functions.<a href="src/mirascope/projects/functions/client.py">get_by_version</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get function by name.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.functions.get_by_version(
    project_uuid="project_uuid",
    function_name="function_name",
    version_num=1,
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**function_name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**version_num:** `int` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.functions.<a href="src/mirascope/projects/functions/client.py">get_by_name</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get function by name.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.functions.get_by_name(
    project_uuid="project_uuid",
    function_name="function_name",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**function_name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.functions.<a href="src/mirascope/projects/functions/client.py">get_deployed_environments</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get the deployed function by function name and environment name.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.functions.get_deployed_environments(
    project_uuid="project_uuid",
    function_name="function_name",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**function_name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.functions.<a href="src/mirascope/projects/functions/client.py">create_versioned</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a managed function.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.functions.create_versioned(
    project_uuid_="project_uuid",
    name="name",
    signature="signature",
    code="code",
    hash="hash",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid_:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**signature:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**code:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**hash:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**project_uuid:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**version_num:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**dependencies:** `typing.Optional[typing.Dict[str, DependencyInfo]]` 
    
</dd>
</dl>

<dl>
<dd>

**arg_types:** `typing.Optional[typing.Dict[str, str]]` 
    
</dd>
</dl>

<dl>
<dd>

**archived:** `typing.Optional[dt.datetime]` 
    
</dd>
</dl>

<dl>
<dd>

**custom_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**prompt_template:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**provider:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**model:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**call_params:** `typing.Optional[CommonCallParams]` 
    
</dd>
</dl>

<dl>
<dd>

**is_versioned:** `typing.Optional[bool]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.functions.<a href="src/mirascope/projects/functions/client.py">get_unique_names</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get all unique function names.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.functions.get_unique_names(
    project_uuid="project_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.functions.<a href="src/mirascope/projects/functions/client.py">get_latest_versions</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get all unique function names.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.functions.get_latest_versions(
    project_uuid="project_uuid",
    environment_uuid="environment_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**environment_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.functions.<a href="src/mirascope/projects/functions/client.py">get_by_hash</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get function by hash.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.functions.get_by_hash(
    project_uuid="project_uuid",
    function_hash="function_hash",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**function_hash:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.functions.<a href="src/mirascope/projects/functions/client.py">list</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Grab all functions.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.functions.list(
    project_uuid="project_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.functions.<a href="src/mirascope/projects/functions/client.py">create</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a new function version.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.functions.create(
    project_uuid_="project_uuid",
    name="name",
    signature="signature",
    code="code",
    hash="hash",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid_:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**signature:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**code:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**hash:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**project_uuid:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**version_num:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**dependencies:** `typing.Optional[typing.Dict[str, DependencyInfo]]` 
    
</dd>
</dl>

<dl>
<dd>

**arg_types:** `typing.Optional[typing.Dict[str, str]]` 
    
</dd>
</dl>

<dl>
<dd>

**archived:** `typing.Optional[dt.datetime]` 
    
</dd>
</dl>

<dl>
<dd>

**custom_id:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**prompt_template:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**provider:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**model:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**call_params:** `typing.Optional[CommonCallParams]` 
    
</dd>
</dl>

<dl>
<dd>

**is_versioned:** `typing.Optional[bool]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.functions.<a href="src/mirascope/projects/functions/client.py">get</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Grab function by UUID.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.functions.get(
    project_uuid="project_uuid",
    function_uuid="function_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**function_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.functions.<a href="src/mirascope/projects/functions/client.py">archive</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Archive a function and delete spans by function UUID.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.functions.archive(
    project_uuid="project_uuid",
    function_uuid="function_uuid",
    environment_uuid="environment_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**function_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**environment_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.functions.<a href="src/mirascope/projects/functions/client.py">update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update a function.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.functions.update(
    project_uuid="project_uuid",
    function_uuid="function_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**function_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.functions.<a href="src/mirascope/projects/functions/client.py">archive_by_name</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Archive a function by name and delete spans by function name.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.functions.archive_by_name(
    project_uuid="project_uuid",
    function_name="function_name",
    environment_uuid="environment_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**function_name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**environment_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Projects Spans
<details><summary><code>client.projects.spans.<a href="src/mirascope/projects/spans/client.py">get_aggregates</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get aggregated span by project uuid.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.spans.get_aggregates(
    project_uuid="project_uuid",
    time_frame="day",
    environment_uuid="environment_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**time_frame:** `TimeFrame` 
    
</dd>
</dl>

<dl>
<dd>

**environment_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.spans.<a href="src/mirascope/projects/spans/client.py">get_recent</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get spans created recently for real-time polling.

If no 'since' parameter is provided, returns spans from the last 30 seconds.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.spans.get_recent(
    project_uuid="project_uuid",
    environment_uuid="environment_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**environment_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**since:** `typing.Optional[dt.datetime]` — Get spans created since this timestamp
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.spans.<a href="src/mirascope/projects/spans/client.py">search</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Search for traces in OpenSearch.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.spans.search(
    project_uuid="project_uuid",
    environment_uuid="environment_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**environment_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**query_string:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**time_range_start:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**time_range_end:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**scope:** `typing.Optional[Scope]` 
    
</dd>
</dl>

<dl>
<dd>

**type:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.spans.<a href="src/mirascope/projects/spans/client.py">delete</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete spans by UUID.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.spans.delete(
    project_uuid="project_uuid",
    span_uuid="span_uuid",
    environment_uuid="environment_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**span_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**environment_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.spans.<a href="src/mirascope/projects/spans/client.py">get_by_id</a>(...)</code></summary>
<dl>
<dd>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.spans.get_by_id(
    project_uuid="project_uuid",
    span_id="span_id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**span_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Projects Traces
<details><summary><code>client.projects.traces.<a href="src/mirascope/projects/traces/client.py">get_root</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get traces by project UUID.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.traces.get_root(
    project_uuid="project_uuid",
    span_id="span_id",
    environment_uuid="environment_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**span_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**environment_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.traces.<a href="src/mirascope/projects/traces/client.py">list</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get traces by project UUID.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.traces.list(
    project_uuid="project_uuid",
    environment_uuid="environment_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**environment_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**offset:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**order:** `typing.Optional[Order]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.traces.<a href="src/mirascope/projects/traces/client.py">create</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create span traces using queue-based processing.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.traces.create(
    project_uuid="project_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Projects Environments
<details><summary><code>client.projects.environments.<a href="src/mirascope/projects/environments/client.py">deploy</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Deploy a function to an environment.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.environments.deploy(
    project_uuid="project_uuid",
    environment_uuid="environment_uuid",
    function_uuid="function_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**environment_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**function_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**notes:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.environments.<a href="src/mirascope/projects/environments/client.py">get_active_deployment</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get active deployment for an environment.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.environments.get_active_deployment(
    project_uuid="project_uuid",
    environment_uuid="environment_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**environment_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.environments.<a href="src/mirascope/projects/environments/client.py">get_function</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get the currently active function for an environment.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.environments.get_function(
    project_uuid="project_uuid",
    environment_uuid="environment_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**environment_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.environments.<a href="src/mirascope/projects/environments/client.py">get_deployment_history</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get deployment history for an environment.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.environments.get_deployment_history(
    project_uuid="project_uuid",
    environment_uuid="environment_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**environment_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Projects Tags
<details><summary><code>client.projects.tags.<a href="src/mirascope/projects/tags/client.py">list</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get all tags by project.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.tags.list(
    project_uuid="project_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Projects Functions Spans
<details><summary><code>client.projects.functions.spans.<a href="src/mirascope/projects/functions/spans/client.py">get_aggregates</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get aggregated span by function uuid.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.functions.spans.get_aggregates(
    project_uuid="project_uuid",
    function_uuid="function_uuid",
    time_frame="day",
    environment_uuid="environment_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**function_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**time_frame:** `TimeFrame` 
    
</dd>
</dl>

<dl>
<dd>

**environment_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.projects.functions.spans.<a href="src/mirascope/projects/functions/spans/client.py">list_paginated</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get spans for a function with pagination (new, non-breaking).
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.projects.functions.spans.list_paginated(
    project_uuid="project_uuid",
    function_uuid="function_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**project_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**function_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**environment_uuid:** `typing.Optional[str]` 
    
</dd>
</dl>

<dl>
<dd>

**limit:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**offset:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**order:** `typing.Optional[Order]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Spans Comments
<details><summary><code>client.spans.comments.<a href="src/mirascope/spans/comments/client.py">list</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get all comments by span.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from mirascope import Lilypad

client = Lilypad(
    api_key="YOUR_API_KEY",
    token="YOUR_TOKEN",
    base_url="https://yourhost.com/path/to/api",
)
client.spans.comments.list(
    span_uuid="span_uuid",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**span_uuid:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

