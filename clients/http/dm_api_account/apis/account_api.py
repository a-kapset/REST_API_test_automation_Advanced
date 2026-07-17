from collections.abc import Mapping
from typing import Literal, overload

import allure
import httpx
from restclient.client import RestClient

from clients.http.dm_api_account.models.change_email import ChangeEmail
from clients.http.dm_api_account.models.change_password import ChangePassword
from clients.http.dm_api_account.models.registration import Registration
from clients.http.dm_api_account.models.reset_password import ResetPassword
from clients.http.dm_api_account.models.user_details_envelope import UserDetailsEnvelope
from clients.http.dm_api_account.models.user_envelope import UserEnvelope

# `validate_response` decides the return type, so each method is overloaded on it:
# callers get UserEnvelope or httpx.Response directly instead of a union they have
# to narrow with isinstance at every call site.
#
# Only 2xx responses reach the validation below: RestClient._send_request calls
# raise_for_status(), so any 4xx/5xx leaves as an HTTPStatusError. Negative tests
# assert on that exception via checkers.http_checkers.check_status_code_http.


class AccountApi(RestClient):
    @allure.step("Send POST request to /v1/account (Account API)")
    async def post_v1_account(self, registration: Registration) -> httpx.Response:
        """
        Register new user

        Args:
            registration

        Returns:
            _type_: Response
        """

        response = await self.post(
            path="/v1/account",
            json=registration.model_dump(exclude_none=True, by_alias=True),
        )

        return response

    @overload
    async def put_v1_account_token(self, token: str, validate_response: Literal[True] = True) -> UserEnvelope: ...

    @overload
    async def put_v1_account_token(self, token: str, validate_response: Literal[False]) -> httpx.Response: ...

    @allure.step("Send PUT request to /v1/account/[token] (Account API)")
    async def put_v1_account_token(self, token: str, validate_response: bool = True) -> UserEnvelope | httpx.Response:
        """
        Activate registered user

        Args:
            token
            validate_response: parse the body into UserEnvelope; return the raw
                response when False.

        Returns:
            UserEnvelope when validate_response is True, otherwise httpx.Response
        """

        headers = {"accept": "text/plain"}

        response = await self.put(path=f"/v1/account/{token}", headers=headers)

        if validate_response:
            return UserEnvelope(**response.json())

        return response

    @overload
    async def put_v1_account_email(
        self, change_email: ChangeEmail, validate_response: Literal[True] = True
    ) -> UserEnvelope: ...

    @overload
    async def put_v1_account_email(
        self, change_email: ChangeEmail, validate_response: Literal[False]
    ) -> httpx.Response: ...

    @allure.step("Send PUT request to /v1/account/email (Account API)")
    async def put_v1_account_email(
        self, change_email: ChangeEmail, validate_response: bool = True
    ) -> UserEnvelope | httpx.Response:
        """
        Change registered user email

        Args:
            change_email
            validate_response: parse the body into UserEnvelope; return the raw
                response when False.

        Returns:
            UserEnvelope when validate_response is True, otherwise httpx.Response
        """

        response = await self.put(
            path="/v1/account/email",
            json=change_email.model_dump(exclude_none=True, by_alias=True),
        )

        if validate_response:
            return UserEnvelope(**response.json())

        return response

    @overload
    async def get_v1_account(
        self, validate_response: Literal[True] = True, headers: Mapping[str, str] | None = None
    ) -> UserDetailsEnvelope: ...

    @overload
    async def get_v1_account(
        self, validate_response: Literal[False], headers: Mapping[str, str] | None = None
    ) -> httpx.Response: ...

    @allure.step("Send GET request to /v1/account (Account API)")
    async def get_v1_account(
        self, validate_response: bool = True, headers: Mapping[str, str] | None = None
    ) -> UserDetailsEnvelope | httpx.Response:
        """
        Get current user

        Args:
            validate_response: parse the body into UserDetailsEnvelope; return the
                raw response when False.
            headers: extra request headers, e.g. the x-dm-auth-token of the user
                to read.

        Returns:
            UserDetailsEnvelope when validate_response is True, otherwise httpx.Response
        """

        response = await self.get(path="/v1/account", headers=headers)

        if validate_response:
            return UserDetailsEnvelope(**response.json())

        return response

    @overload
    async def post_v1_account_password(
        self, reset_password: ResetPassword, validate_response: Literal[True] = True
    ) -> UserEnvelope: ...

    @overload
    async def post_v1_account_password(
        self, reset_password: ResetPassword, validate_response: Literal[False]
    ) -> httpx.Response: ...

    @allure.step("Send POST request to /v1/account/password (Account API)")
    async def post_v1_account_password(
        self, reset_password: ResetPassword, validate_response: bool = True
    ) -> UserEnvelope | httpx.Response:
        """
        Reset registered user password

        Args:
            reset_password
            validate_response: parse the body into UserEnvelope; return the raw
                response when False.

        Returns:
            UserEnvelope when validate_response is True, otherwise httpx.Response
        """

        response = await self.post(
            path="/v1/account/password",
            json=reset_password.model_dump(exclude_none=True, by_alias=True),
        )

        if validate_response:
            return UserEnvelope(**response.json())

        return response

    @overload
    async def put_v1_account_password(
        self, change_password: ChangePassword, validate_response: Literal[True] = True
    ) -> UserEnvelope: ...

    @overload
    async def put_v1_account_password(
        self, change_password: ChangePassword, validate_response: Literal[False]
    ) -> httpx.Response: ...

    @allure.step("Send PUT request to /v1/account/password (Account API)")
    async def put_v1_account_password(
        self, change_password: ChangePassword, validate_response: bool = True
    ) -> UserEnvelope | httpx.Response:
        """
        Change registered user password

        Args:
            change_password
            validate_response: parse the body into UserEnvelope; return the raw
                response when False.

        Returns:
            UserEnvelope when validate_response is True, otherwise httpx.Response
        """

        response = await self.put(
            path="/v1/account/password",
            json=change_password.model_dump(exclude_none=True, by_alias=True),
        )

        if validate_response:
            return UserEnvelope(**response.json())

        return response
