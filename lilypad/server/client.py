"""The `lilypad` API client."""

import logging
from collections.abc import Callable
from typing import Any, TypeVar, get_origin, overload
from uuid import UUID

import requests
from pydantic import BaseModel, TypeAdapter
from requests.exceptions import HTTPError, RequestException, Timeout

from .._utils import Closure, load_config
from ..exceptions import (
    LilypadAPIConnectionError,
    LilypadException,
    LilypadFileNotFoundError,
    LilypadHTTPError,
    LilypadNotFoundError,
    LilypadRequestException,
    LilypadTimeout,
)
from ..server.settings import get_settings
from .schemas import GenerationPublic, OrganizationPublic, ProjectPublic, SpanPublic
from .schemas.prompts import PromptPublic
from .schemas.response_models import ResponseModelPublic

_R = TypeVar("_R", bound=BaseModel)

log = logging.getLogger(__name__)


class LilypadClient:
    """Client for interacting with the Lilypad API."""

    _token: str | None = None

    def __init__(
        self,
        timeout: int = 10,
        headers: dict[str, str] | None = None,
        token: str | None = None,
        **session_kwargs: Any,
    ) -> None:
        """Initialize the API client.

        Args:
            base_url (str): The base URL for the API endpoints.
            timeout (int, optional): Default timeout for requests in seconds. Defaults to 10.
            headers (dict, optional): Default headers to include in all requests. Defaults to None.
            token (str, optional): Default authentication token to include in all requests. Defaults to None.
            **session_kwargs: Additional keyword arguments for the session.
        """
        config = load_config()
        settings = get_settings()
        base_url: str = config.get("base_url", None) or settings.api_url
        self.base_url = f"{base_url.rstrip('/')}"
        self.timeout = timeout
        self.session = requests.Session()
        self.project_uuid = settings.project_id
        if not self.project_uuid:
            try:
                self.project_uuid = (
                    UUID(config["project_uuid"])
                    if config.get("project_uuid", None)
                    else None
                )
            except LilypadFileNotFoundError:
                self.project_uuid = None
        if settings.api_key:
            self.session.headers.update({"X-API-Key": settings.api_key})
        if headers:
            self.session.headers.update(headers)

        self.token = token

        for key, value in session_kwargs.items():
            setattr(self.session, key, value)

    @property
    def token(self) -> str | None:
        """Get the current authentication token."""
        return self._token

    @token.setter
    def token(self, value: str | None) -> None:
        """Set the authentication token and update headers.

        Args:
            value (str | None): The authentication token or None to remove authentication.
        """
        self._token = value
        if value:
            self.session.headers.update({"Authorization": f"Bearer {value}"})

    @overload
    def _request(
        self,
        method: str,
        endpoint: str,
        response_model: type[_R],
        **kwargs: Any,
    ) -> _R: ...
    @overload
    def _request(
        self,
        method: str,
        endpoint: str,
        response_model: type[list[_R]],
        **kwargs: Any,
    ) -> list[_R]: ...

    @overload
    def _request(
        self,
        method: str,
        endpoint: str,
        response_model: None,
        **kwargs: Any,
    ) -> dict[str, Any]: ...

    def _request(
        self,
        method: str,
        endpoint: str,
        response_model: type[list[_R]] | type[_R] | None = None,
        **kwargs: Any,
    ) -> _R | list[_R] | dict[str, Any]:
        """Internal method to make HTTP requests and parse responses.

        Args:
            method (str): HTTP method as a string (e.g., 'GET', 'POST').
            endpoint (str): API endpoint (appended to base_url).
            response_model (Type[T], optional): Pydantic model to parse the response into. Defaults to None.
            **kwargs: Additional arguments passed to requests.request().

        Returns:
            Union[T, str]: Parsed Pydantic model if response_model is provided; otherwise, raw text.

        Raises:
            LilypadTimeout: If the request times out.
            LilypadHTTPError: For bad HTTP responses.
            LilypadRequestException: For other request-related errors.
            LilypadException: For other unknown errors.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        timeout = kwargs.pop("timeout", self.timeout)

        try:
            response = self.session.request(method, url, timeout=timeout, **kwargs)
            response.raise_for_status()
        except Timeout:
            log.error(f"Request to {url} timed out.")
            raise LilypadTimeout(f"Request to {url} timed out.")
        except ConnectionError as conn_err:
            raise LilypadAPIConnectionError(
                f"Connection error during request to {url}: {conn_err}"
            )
        except HTTPError as http_err:
            if http_err.response.status_code == 404:
                raise LilypadNotFoundError(f"Resource not found: {url}")
            raise LilypadHTTPError(
                f"HTTP error during request to {url}: {http_err.response.text}"
            )
        except RequestException:
            raise LilypadRequestException("Unknown error during request.")
        try:
            if get_origin(response_model) is list:
                return TypeAdapter(response_model).validate_python(response.json())
            elif response_model and issubclass(response_model, BaseModel):
                return response_model.model_validate(response.json())
            else:
                return response.json()
        except Exception as e:
            log.error(f"Error parsing response into {response_model}: {e}")
            raise LilypadException

    def get_health(self) -> dict[str, Any]:
        """Get the health status of the server."""
        return self._request("GET", "/health", response_model=None)

    def post_project(self, project_name: str, **kwargs: Any) -> ProjectPublic:
        """Creates a new project."""
        return self._request(
            "POST",
            "/v0/projects/",
            response_model=ProjectPublic,
            json={"name": project_name},
            **kwargs,
        )

    def get_projects(self, **kwargs: Any) -> list[ProjectPublic]:
        """Creates a new project."""
        return self._request(
            "GET",
            "/v0/projects",
            response_model=list[ProjectPublic],
            **kwargs,
        )

    def post_traces(
        self, params: dict[str, Any] | None = None, **kwargs: Any
    ) -> SpanPublic:
        """Creates span traces.

        Args:
            params (dict, optional): Dictionary of query parameters. Defaults to None.
            **kwargs: Additional keyword arguments for the request.

        Returns:
            List of SpanPublic objects with no parents. Child spans are nested
                within the parent span.
        """
        return self._request(
            "POST",
            f"/v0/projects/{self.project_uuid}/traces",
            response_model=SpanPublic,
            params=params,
            **kwargs,
        )

    def get_or_create_generation_version(
        self,
        fn: Callable[..., Any],
        arg_types: dict[str, str],
        custom_id: str | None = None,
    ) -> GenerationPublic:
        """Get the matching version for a generation or create it if non-existent.

        Args:
            fn (Callable): The generation for which to get the version.
            arg_types (dict): Dictionary of argument names and types.
            custom_id (str, optional): Custom ID for the generation. Defaults to None.

        Returns:
            GenerationPublic: The matching (or created) version for the generation.
        """
        closure = Closure.from_fn(fn)
        try:
            return self._request(
                "GET",
                f"v0/projects/{self.project_uuid}/generations/hash/{closure.hash}",
                response_model=GenerationPublic,
            )
        except LilypadNotFoundError:
            return self._request(
                "POST",
                f"v0/projects/{self.project_uuid}/generations",
                response_model=GenerationPublic,
                json={
                    "name": closure.name,
                    "signature": closure.signature,
                    "code": closure.code,
                    "hash": closure.hash,
                    "dependencies": closure.dependencies,
                    "arg_types": arg_types,
                    "custom_id": custom_id,
                },
            )

    def get_prompt_active_version(
        self, fn: Callable[..., Any], generation: GenerationPublic | None
    ) -> PromptPublic | None:
        """Get the matching version for a prompt.

        Args:
            fn (Callable): The prompt for which to get the version.
            generation (GenerationPublic | None): A generation that may have a specific
                version of the prompt linked.

        Returns:
            PromptPublic | None: The matching version for the prompt, or `None`.
        """
        closure = Closure.from_fn(fn)
        if (
            generation
            and generation.prompt
            and generation.prompt.signature == closure.signature
        ):
            return generation.prompt
        elif generation and not generation.prompt:
            prompts = self._request(
                "GET",
                f"v0/projects/{self.project_uuid}/prompts/metadata/signature/public",
                params={"signature": closure.signature},
                response_model=list[PromptPublic],
            )
            if not prompts:
                return None

            self._request(
                "PATCH",
                f"v0/projects/{self.project_uuid}/generations/{generation.uuid}",
                json={"prompt_uuid": str(prompts[0].uuid)},
                response_model=GenerationPublic,
            )

            return prompts[0]
        try:
            return self._request(
                "GET",
                f"v0/projects/{self.project_uuid}/prompts/hash/{closure.hash}/active",
                response_model=PromptPublic,
            )
        except LilypadNotFoundError:
            return None

    def get_response_model_active_version(
        self, cls: type[BaseModel], generation: GenerationPublic | None
    ) -> ResponseModelPublic | None:
        """Get the active version of a response model."""
        closure = Closure.from_fn(cls)
        if (
            generation
            and generation.response_model
            and generation.response_model.hash == closure.hash
        ):
            return generation.response_model
        try:
            return self._request(
                "GET",
                f"v0/projects/{self.project_uuid}/response_models/hash/{closure.hash}/active",
                response_model=ResponseModelPublic,
            )
        except LilypadNotFoundError:
            return None

    def get_or_create_response_model_version(
        self,
        cls: type[BaseModel],
        schema_data: dict[str, Any],
        examples: list[dict[str, Any]],
    ) -> ResponseModelPublic:
        """Get or create a response model version by hash.

        If not found, this method will create a new response model version.
        """
        closure = Closure.from_fn(cls)
        try:
            rm = self._request(
                "GET",
                f"v0/projects/{self.project_uuid}/response_models/hash/{closure.hash}/active",
                response_model=ResponseModelPublic,
            )
            return rm
        except LilypadNotFoundError:
            create_data = {
                "name": closure.name,
                "signature": closure.signature,
                "code": closure.code,
                "hash": closure.hash,
                "dependencies": closure.dependencies,
                "schema_data": schema_data,
                "examples": examples,
            }
            rm_new = self._request(
                "POST",
                f"v0/projects/{self.project_uuid}/response_models",
                response_model=ResponseModelPublic,
                json=create_data,
            )
            return rm_new

    def patch_organization(
        self, organization_uuid: UUID, data: dict[str, Any]
    ) -> OrganizationPublic:
        """Update an organization."""
        return self._request(
            "PATCH",
            f"/v0/organizations/{organization_uuid}",
            response_model=OrganizationPublic,
            **data,
        )

    def get_organization(self, organization_uuid: UUID) -> OrganizationPublic:
        """Get an organization."""
        return self._request(
            "GET",
            f"/v0/organizations/{organization_uuid}",
            response_model=OrganizationPublic,
        )
