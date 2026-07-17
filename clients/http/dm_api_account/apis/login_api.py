from collections.abc import Mapping
from typing import Literal, overload

import allure
import httpx
from restclient.client import RestClient

from clients.http.dm_api_account.models.login_credentials import LoginCredentials
from clients.http.dm_api_account.models.user_envelope import UserEnvelope

# See the note in account_api.py: `validate_response` decides the return type, and
# only 2xx responses reach the validation because RestClient._send_request calls
# raise_for_status(). A failed login surfaces as an HTTPStatusError, which
# checkers.http_checkers.check_status_code_http asserts on.


class LoginApi(RestClient):
    @overload
    async def post_v1_account_login(
        self, login_credentials: LoginCredentials, validate_response: Literal[True] = True
    ) -> UserEnvelope: ...

    @overload
    async def post_v1_account_login(
        self, login_credentials: LoginCredentials, validate_response: Literal[False]
    ) -> httpx.Response: ...

    @allure.step("Send POST request to /v1/account/login (Login API)")
    async def post_v1_account_login(
        self, login_credentials: LoginCredentials, validate_response: bool = True
    ) -> UserEnvelope | httpx.Response:
        """
        Authenticate via credentials

        Args:
            login_credentials
            validate_response: parse the body into UserEnvelope; return the raw
                response when False (needed to read the x-dm-auth-token header).

        Returns:
            UserEnvelope when validate_response is True, otherwise httpx.Response
        """

        response = await self.post(
            path="/v1/account/login",
            json=login_credentials.model_dump(exclude_none=True, by_alias=True),
        )

        if validate_response:
            return UserEnvelope(**response.json())

        return response

    @allure.step("Send DELETE request to /v1/account/login (Login API)")
    async def delete_v1_account_login(self, headers: Mapping[str, str] | None = None) -> httpx.Response:
        """
        Logout as current user

        Args:
            headers: extra request headers, e.g. the x-dm-auth-token of the user
                to log out.

        Returns:
            httpx.Response
        """

        response = await self.delete(path="/v1/account/login", headers=headers)

        return response

    @allure.step("Send DELETE request to /v1/account/login/all (Login API)")
    async def delete_v1_account_login_all(self, headers: Mapping[str, str] | None = None) -> httpx.Response:
        """
        Logout from every device

        Args:
            headers: extra request headers, e.g. the x-dm-auth-token of the user
                to log out.

        Returns:
            httpx.Response
        """

        response = await self.delete(path="/v1/account/login/all", headers=headers)

        return response
