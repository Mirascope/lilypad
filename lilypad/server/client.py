from typing import Any, Literal, TypeVar, get_origin, overload

import requests
from pydantic import BaseModel, TypeAdapter
from requests.exceptions import HTTPError, RequestException, Timeout
from rich import print

from lilypad.models import CallArgsPublic, LLMFunctionBasePublic, SpanPublic

# Configure logging


# Define a generic type variable for Pydantic models
T = TypeVar("T", bound=BaseModel)


class NotFoundError(Exception):
    """Raised when an API response has a status code of 404."""

    status_code: Literal[404] = 404


class APIConnectionError(Exception):
    """Raised when an API connection error occurs."""

    ...


class LilypadClient:
    def __init__(
        self,
        base_url: str,
        timeout: int = 10,
        headers: dict[str, str] | None = None,
        **session_kwargs: Any,
    ) -> None:
        """Initialize the API client.

        Args:
            base_url (str): The base URL for the API endpoints.
            timeout (int, optional): Default timeout for requests in seconds. Defaults to 10.
            headers (dict, optional): Default headers to include in all requests. Defaults to None.
            **session_kwargs: Additional keyword arguments for the session.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

        if headers:
            self.session.headers.update(headers)

        for key, value in session_kwargs.items():
            setattr(self.session, key, value)

    @overload
    def _request(
        self,
        method: str,
        endpoint: str,
        response_model: type[T],
        **kwargs: Any,
    ) -> T: ...

    @overload
    def _request(
        self,
        method: str,
        endpoint: str,
        response_model: type[list[T]],
        **kwargs: Any,
    ) -> list[T]: ...

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
        response_model: type[list[T]] | type[T] | None = None,
        **kwargs: Any,
    ) -> T | list[T] | dict[str, Any]:
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
        except RequestException as err:
            print(f"Error during request to {url}: {err}")
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
            "/v1/traces",
            response_model=list[SpanPublic],
            params=params,
            **kwargs,
        )

    def get_llm_function_by_hash(
        self, version_hash: str, **kwargs: Any
    ) -> LLMFunctionBasePublic:
        """Creates span traces."""
        return self._request(
            "GET",
            f"/llm-functions/{version_hash}",
            response_model=LLMFunctionBasePublic,
            **kwargs,
        )

    def post_llm_function(
        self,
        function_name: str,
        code: str,
        version_hash: str,
        input_arguments: str,
        **kwargs: Any,
    ) -> LLMFunctionBasePublic:
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
            "/llm-functions/",
            response_model=LLMFunctionBasePublic,
            json={
                "function_name": function_name,
                "code": code,
                "version_hash": version_hash,
                "input_arguments": input_arguments,
            },
            **kwargs,
        )

    def get_provider_call_params_by_llm_function_hash(
        self, version_hash: str, **kwargs: Any
    ) -> CallArgsPublic:
        """Creates span traces."""
        return self._request(
            "GET",
            f"/llm-functions/{version_hash}/provider-call-params",
            response_model=CallArgsPublic,
            **kwargs,
        )
