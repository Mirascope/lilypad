# This file was auto-generated by Fern from our API Definition.

import typing

from ..core.client_wrapper import AsyncClientWrapper, SyncClientWrapper
from ..core.request_options import RequestOptions
from ..types.external_api_key_public import ExternalApiKeyPublic
from .raw_client import AsyncRawExternalApiKeysClient, RawExternalApiKeysClient

# this is used as the default value for optional parameters
OMIT = typing.cast(typing.Any, ...)


class ExternalApiKeysClient:
    def __init__(self, *, client_wrapper: SyncClientWrapper):
        self._raw_client = RawExternalApiKeysClient(client_wrapper=client_wrapper)

    @property
    def with_raw_response(self) -> RawExternalApiKeysClient:
        """
        Retrieves a raw implementation of this client that returns raw responses.

        Returns
        -------
        RawExternalApiKeysClient
        """
        return self._raw_client

    def list(self, *, request_options: typing.Optional[RequestOptions] = None) -> typing.List[ExternalApiKeyPublic]:
        """
        List all external API keys for the user with masked values.

        Parameters
        ----------
        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        typing.List[ExternalApiKeyPublic]
            Successful Response

        Examples
        --------
        from mirascope import Lilypad

        client = Lilypad(
            api_key="YOUR_API_KEY",
            token="YOUR_TOKEN",
            base_url="https://yourhost.com/path/to/api",
        )
        client.external_api_keys.list()
        """
        _response = self._raw_client.list(request_options=request_options)
        return _response.data

    def create(
        self, *, service_name: str, api_key: str, request_options: typing.Optional[RequestOptions] = None
    ) -> ExternalApiKeyPublic:
        """
        Store an external API key for a given service.

        Parameters
        ----------
        service_name : str

        api_key : str
            New API key

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        ExternalApiKeyPublic
            Successful Response

        Examples
        --------
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
        """
        _response = self._raw_client.create(service_name=service_name, api_key=api_key, request_options=request_options)
        return _response.data

    def get(
        self, service_name: str, *, request_options: typing.Optional[RequestOptions] = None
    ) -> ExternalApiKeyPublic:
        """
        Retrieve an external API key for a given service.

        Parameters
        ----------
        service_name : str

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        ExternalApiKeyPublic
            Successful Response

        Examples
        --------
        from mirascope import Lilypad

        client = Lilypad(
            api_key="YOUR_API_KEY",
            token="YOUR_TOKEN",
            base_url="https://yourhost.com/path/to/api",
        )
        client.external_api_keys.get(
            service_name="service_name",
        )
        """
        _response = self._raw_client.get(service_name, request_options=request_options)
        return _response.data

    def delete(self, service_name: str, *, request_options: typing.Optional[RequestOptions] = None) -> bool:
        """
        Delete an external API key for a given service.

        Parameters
        ----------
        service_name : str

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        bool
            Successful Response

        Examples
        --------
        from mirascope import Lilypad

        client = Lilypad(
            api_key="YOUR_API_KEY",
            token="YOUR_TOKEN",
            base_url="https://yourhost.com/path/to/api",
        )
        client.external_api_keys.delete(
            service_name="service_name",
        )
        """
        _response = self._raw_client.delete(service_name, request_options=request_options)
        return _response.data

    def update(
        self, service_name: str, *, api_key: str, request_options: typing.Optional[RequestOptions] = None
    ) -> ExternalApiKeyPublic:
        """
        Update users keys.

        Parameters
        ----------
        service_name : str

        api_key : str
            New API key

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        ExternalApiKeyPublic
            Successful Response

        Examples
        --------
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
        """
        _response = self._raw_client.update(service_name, api_key=api_key, request_options=request_options)
        return _response.data


class AsyncExternalApiKeysClient:
    def __init__(self, *, client_wrapper: AsyncClientWrapper):
        self._raw_client = AsyncRawExternalApiKeysClient(client_wrapper=client_wrapper)

    @property
    def with_raw_response(self) -> AsyncRawExternalApiKeysClient:
        """
        Retrieves a raw implementation of this client that returns raw responses.

        Returns
        -------
        AsyncRawExternalApiKeysClient
        """
        return self._raw_client

    async def list(
        self, *, request_options: typing.Optional[RequestOptions] = None
    ) -> typing.List[ExternalApiKeyPublic]:
        """
        List all external API keys for the user with masked values.

        Parameters
        ----------
        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        typing.List[ExternalApiKeyPublic]
            Successful Response

        Examples
        --------
        import asyncio

        from mirascope import AsyncLilypad

        client = AsyncLilypad(
            api_key="YOUR_API_KEY",
            token="YOUR_TOKEN",
            base_url="https://yourhost.com/path/to/api",
        )


        async def main() -> None:
            await client.external_api_keys.list()


        asyncio.run(main())
        """
        _response = await self._raw_client.list(request_options=request_options)
        return _response.data

    async def create(
        self, *, service_name: str, api_key: str, request_options: typing.Optional[RequestOptions] = None
    ) -> ExternalApiKeyPublic:
        """
        Store an external API key for a given service.

        Parameters
        ----------
        service_name : str

        api_key : str
            New API key

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        ExternalApiKeyPublic
            Successful Response

        Examples
        --------
        import asyncio

        from mirascope import AsyncLilypad

        client = AsyncLilypad(
            api_key="YOUR_API_KEY",
            token="YOUR_TOKEN",
            base_url="https://yourhost.com/path/to/api",
        )


        async def main() -> None:
            await client.external_api_keys.create(
                service_name="service_name",
                api_key="api_key",
            )


        asyncio.run(main())
        """
        _response = await self._raw_client.create(
            service_name=service_name, api_key=api_key, request_options=request_options
        )
        return _response.data

    async def get(
        self, service_name: str, *, request_options: typing.Optional[RequestOptions] = None
    ) -> ExternalApiKeyPublic:
        """
        Retrieve an external API key for a given service.

        Parameters
        ----------
        service_name : str

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        ExternalApiKeyPublic
            Successful Response

        Examples
        --------
        import asyncio

        from mirascope import AsyncLilypad

        client = AsyncLilypad(
            api_key="YOUR_API_KEY",
            token="YOUR_TOKEN",
            base_url="https://yourhost.com/path/to/api",
        )


        async def main() -> None:
            await client.external_api_keys.get(
                service_name="service_name",
            )


        asyncio.run(main())
        """
        _response = await self._raw_client.get(service_name, request_options=request_options)
        return _response.data

    async def delete(self, service_name: str, *, request_options: typing.Optional[RequestOptions] = None) -> bool:
        """
        Delete an external API key for a given service.

        Parameters
        ----------
        service_name : str

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        bool
            Successful Response

        Examples
        --------
        import asyncio

        from mirascope import AsyncLilypad

        client = AsyncLilypad(
            api_key="YOUR_API_KEY",
            token="YOUR_TOKEN",
            base_url="https://yourhost.com/path/to/api",
        )


        async def main() -> None:
            await client.external_api_keys.delete(
                service_name="service_name",
            )


        asyncio.run(main())
        """
        _response = await self._raw_client.delete(service_name, request_options=request_options)
        return _response.data

    async def update(
        self, service_name: str, *, api_key: str, request_options: typing.Optional[RequestOptions] = None
    ) -> ExternalApiKeyPublic:
        """
        Update users keys.

        Parameters
        ----------
        service_name : str

        api_key : str
            New API key

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        ExternalApiKeyPublic
            Successful Response

        Examples
        --------
        import asyncio

        from mirascope import AsyncLilypad

        client = AsyncLilypad(
            api_key="YOUR_API_KEY",
            token="YOUR_TOKEN",
            base_url="https://yourhost.com/path/to/api",
        )


        async def main() -> None:
            await client.external_api_keys.update(
                service_name="service_name",
                api_key="api_key",
            )


        asyncio.run(main())
        """
        _response = await self._raw_client.update(service_name, api_key=api_key, request_options=request_options)
        return _response.data
