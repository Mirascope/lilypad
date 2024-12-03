"""The `lilypad` API client."""

from collections.abc import Callable
from typing import Any, Literal, TypeVar, get_origin, overload
from uuid import UUID

import requests
from pydantic import BaseModel, TypeAdapter
from requests.exceptions import HTTPError, RequestException, Timeout
from rich import print

from .._utils import compute_closure, load_config
from .models import ActiveVersionPublic, ProjectPublic, SpanPublic, VersionPublic

_R = TypeVar("_R", bound=BaseModel)


class NotFoundError(Exception):
    """Raised when an API response has a status code of 404."""

    status_code: Literal[404] = 404


class APIConnectionError(Exception):
    """Raised when an API connection error occurs."""

    ...


class LilypadClient:
    """Client for interacting with the Lilypad API."""

    _token: str | None = None

    def __init__(
        self,
        base_url: str,
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
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        try:
            config = load_config()
            self.project_uuid = (
                UUID(config["project_uuid"])
                if config.get("project_uuid", None)
                else None
            )
        except FileNotFoundError:
            self.project_uuid = None
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
            self.session.headers["Authorization"] = f"Bearer {value}"

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
            Timeout: If the request times out.
            HTTPError: For bad HTTP responses.
            RequestException: For other request-related errors.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        timeout = kwargs.pop("timeout", self.timeout)

        try:
            response = self.session.request(method, url, timeout=timeout, **kwargs)
            response.raise_for_status()
        except Timeout:
            print(f"Request to {url} timed out.")
            raise
        except ConnectionError as conn_err:
            raise APIConnectionError(
                f"Connection error during request to {url}: {conn_err}"
            )
        except HTTPError as http_err:
            if http_err.response.status_code == 404:
                raise NotFoundError(f"Resource not found: {url}")
            raise HTTPError(
                f"HTTP error during request to {url}: {http_err.response.text}"
            )
        except RequestException:
            raise

        try:
            if get_origin(response_model) is list:
                return TypeAdapter(response_model).validate_python(response.json())
            elif response_model and issubclass(response_model, BaseModel):
                return response_model.model_validate(response.json())
            else:
                return response.json()
        except Exception as e:
            print(f"Error parsing response into {response_model}: {e}")
            raise

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
    ) -> list[SpanPublic]:
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
            "/v0/traces",
            response_model=list[SpanPublic],
            params=params,
            **kwargs,
        )

    def get_or_create_function_version(
        self, fn: Callable[..., Any], arg_types: dict[str, str]
    ) -> VersionPublic:
        """Get the active version for a function or create it if non-existent.

        Args:
            fn (Callable): The function to get the version for.
            arg_types (dict): Dictionary of argument names and types.

        Returns:
            VersionPublic: The active version for the function.
        """
        code, hash = compute_closure(fn)
        try:
            return self._request(
                "GET",
                f"/v0/projects/{self.project_uuid}/functions/{hash}/versions",
                response_model=VersionPublic,
            )
        except NotFoundError:
            return self._request(
                "POST",
                f"/v0/projects/{self.project_uuid}/functions/{hash}/versions",
                response_model=VersionPublic,
                json={
                    "name": fn.__name__,
                    "hash": hash,
                    "code": code,
                    "arg_types": arg_types,
                },
            )

    def get_prompt_active_version(self, fn: Callable[..., Any]) -> ActiveVersionPublic:
        """Get the active version for a function with a prompt.

        Args:
            fn (Callable): The function to get the version for.
            arg_types (dict): Dictionary of argument names and types.

        Returns:
            VersionPublic: The active version for the function.
        """
        _, hash = compute_closure(fn)
        return self._request(
            "GET",
            f"/v0/projects/{self.project_uuid}/functions/{hash}/versions/active",
            response_model=ActiveVersionPublic,
        )
