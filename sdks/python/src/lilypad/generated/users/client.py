# This file was auto-generated by Fern from our API Definition.

import typing

from ..core.client_wrapper import AsyncClientWrapper, SyncClientWrapper
from ..core.request_options import RequestOptions
from ..types.user_public import UserPublic
from .raw_client import AsyncRawUsersClient, RawUsersClient

# this is used as the default value for optional parameters
OMIT = typing.cast(typing.Any, ...)


class UsersClient:
    def __init__(self, *, client_wrapper: SyncClientWrapper):
        self._raw_client = RawUsersClient(client_wrapper=client_wrapper)

    @property
    def with_raw_response(self) -> RawUsersClient:
        """
        Retrieves a raw implementation of this client that returns raw responses.

        Returns
        -------
        RawUsersClient
        """
        return self._raw_client

    def set_active_organization(
        self, active_organization_uuid: str, *, request_options: typing.Optional[RequestOptions] = None
    ) -> UserPublic:
        """
        Update users active organization uuid.

        Parameters
        ----------
        active_organization_uuid : str

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        UserPublic
            Successful Response

        Examples
        --------
        from mirascope import Lilypad

        client = Lilypad(
            api_key="YOUR_API_KEY",
            token="YOUR_TOKEN",
            base_url="https://yourhost.com/path/to/api",
        )
        client.users.set_active_organization(
            active_organization_uuid="activeOrganizationUuid",
        )
        """
        _response = self._raw_client.set_active_organization(active_organization_uuid, request_options=request_options)
        return _response.data

    def update_api_keys(
        self,
        *,
        request: typing.Dict[str, typing.Optional[typing.Any]],
        request_options: typing.Optional[RequestOptions] = None,
    ) -> UserPublic:
        """
        Update users keys.

        Parameters
        ----------
        request : typing.Dict[str, typing.Optional[typing.Any]]

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        UserPublic
            Successful Response

        Examples
        --------
        from mirascope import Lilypad

        client = Lilypad(
            api_key="YOUR_API_KEY",
            token="YOUR_TOKEN",
            base_url="https://yourhost.com/path/to/api",
        )
        client.users.update_api_keys(
            request={"key": "value"},
        )
        """
        _response = self._raw_client.update_api_keys(request=request, request_options=request_options)
        return _response.data

    def get_current_user(self, *, request_options: typing.Optional[RequestOptions] = None) -> UserPublic:
        """
        Get user.

        Parameters
        ----------
        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        UserPublic
            Successful Response

        Examples
        --------
        from mirascope import Lilypad

        client = Lilypad(
            api_key="YOUR_API_KEY",
            token="YOUR_TOKEN",
            base_url="https://yourhost.com/path/to/api",
        )
        client.users.get_current_user()
        """
        _response = self._raw_client.get_current_user(request_options=request_options)
        return _response.data


class AsyncUsersClient:
    def __init__(self, *, client_wrapper: AsyncClientWrapper):
        self._raw_client = AsyncRawUsersClient(client_wrapper=client_wrapper)

    @property
    def with_raw_response(self) -> AsyncRawUsersClient:
        """
        Retrieves a raw implementation of this client that returns raw responses.

        Returns
        -------
        AsyncRawUsersClient
        """
        return self._raw_client

    async def set_active_organization(
        self, active_organization_uuid: str, *, request_options: typing.Optional[RequestOptions] = None
    ) -> UserPublic:
        """
        Update users active organization uuid.

        Parameters
        ----------
        active_organization_uuid : str

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        UserPublic
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
            await client.users.set_active_organization(
                active_organization_uuid="activeOrganizationUuid",
            )


        asyncio.run(main())
        """
        _response = await self._raw_client.set_active_organization(
            active_organization_uuid, request_options=request_options
        )
        return _response.data

    async def update_api_keys(
        self,
        *,
        request: typing.Dict[str, typing.Optional[typing.Any]],
        request_options: typing.Optional[RequestOptions] = None,
    ) -> UserPublic:
        """
        Update users keys.

        Parameters
        ----------
        request : typing.Dict[str, typing.Optional[typing.Any]]

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        UserPublic
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
            await client.users.update_api_keys(
                request={"key": "value"},
            )


        asyncio.run(main())
        """
        _response = await self._raw_client.update_api_keys(request=request, request_options=request_options)
        return _response.data

    async def get_current_user(self, *, request_options: typing.Optional[RequestOptions] = None) -> UserPublic:
        """
        Get user.

        Parameters
        ----------
        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        UserPublic
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
            await client.users.get_current_user()


        asyncio.run(main())
        """
        _response = await self._raw_client.get_current_user(request_options=request_options)
        return _response.data
