from typing import Any

import allure
import httpx
from clients.http.dm_api_account.models.change_email import ChangeEmail
from clients.http.dm_api_account.models.change_password import ChangePassword
from clients.http.dm_api_account.models.problem_details import ProblemDetails
from clients.http.dm_api_account.models.registration import Registration
from clients.http.dm_api_account.models.reset_password import ResetPassword
from clients.http.dm_api_account.models.user_details_envelope import UserDetailsEnvelope
from clients.http.dm_api_account.models.user_envelope import UserEnvelope
from packages.restclient.client import RestClient


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

    @allure.step("Send PUT request to /v1/account/[token] (Account API)")
    async def put_v1_account_token(self, token: str, validate_response: bool = True) -> UserEnvelope | httpx.Response:
        """
        Activate registered user

        Args:
            token

        Returns:
            _type_: Response
        """

        headers = {"accept": "text/plain"}

        response = await self.put(path=f"/v1/account/{token}", headers=headers)

        if validate_response:
            return UserEnvelope(**response.json())

        return response

    @allure.step("Send PUT request to /v1/account/email (Account API)")
    async def put_v1_account_email(
        self, change_email: ChangeEmail, validate_response: bool = True
    ) -> UserEnvelope | httpx.Response:
        """
        Change registered user email

        Args:
            change_email

        Returns:
            _type_: Response
        """

        response = await self.put(
            path="/v1/account/email",
            json=change_email.model_dump(exclude_none=True, by_alias=True),
        )

        if validate_response:
            return UserEnvelope(**response.json())

        return response

    @allure.step("Send GET request to /v1/account (Account API)")
    async def get_v1_account(
        self, validate_response: bool = True, **kwargs: Any
    ) -> UserDetailsEnvelope | ProblemDetails | httpx.Response:
        """
        Get current user

        Args:
            **kwargs

        Returns:
            _type_: Response
        """

        response = await self.get(path="/v1/account", **kwargs)

        # Validate against the model that matches the returned status code so
        # error responses are validated too (not just 2xx). 401 uses
        # ProblemDetails because that is the body the server actually returns
        # for an unauthenticated request, even though swagger only declares
        # the 200 -> UserDetailsEnvelope response.
        if validate_response:
            if response.status_code == 200:
                return UserDetailsEnvelope(**response.json())
            if response.status_code == 401:
                return ProblemDetails(**response.json())

        return response

    @allure.step("Send POST request to /v1/account/password (Account API)")
    async def post_v1_account_password(
        self, reset_password: ResetPassword, validate_response: bool = True
    ) -> UserEnvelope | httpx.Response:
        """
        Reset registered user password

        Args:
            reset_password

        Returns:
            _type_: Response
        """

        response = await self.post(
            path="/v1/account/password",
            json=reset_password.model_dump(exclude_none=True, by_alias=True),
        )

        if validate_response:
            return UserEnvelope(**response.json())

        return response

    @allure.step("Send PUT request to /v1/account/password (Account API)")
    async def put_v1_account_password(
        self, change_password: ChangePassword, validate_response: bool = True
    ) -> UserEnvelope | httpx.Response:
        """
        Change registered user password

        Args:
            change_password

        Returns:
            _type_: Response
        """

        response = await self.put(
            path="/v1/account/password",
            json=change_password.model_dump(exclude_none=True, by_alias=True),
        )

        if validate_response:
            return UserEnvelope(**response.json())

        return response
