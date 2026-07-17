import asyncio
import functools
from collections.abc import Awaitable, Callable
from json import JSONDecodeError, loads
from typing import Any, Literal, overload

import allure
import httpx

from clients.http.dm_api_account.models.change_email import ChangeEmail
from clients.http.dm_api_account.models.change_password import ChangePassword
from clients.http.dm_api_account.models.login_credentials import LoginCredentials
from clients.http.dm_api_account.models.registration import Registration
from clients.http.dm_api_account.models.reset_password import ResetPassword
from clients.http.dm_api_account.models.user_details_envelope import UserDetailsEnvelope
from clients.http.dm_api_account.models.user_envelope import UserEnvelope
from services.api_mailhog import MailHogApi
from services.dm_api_account import DmApiAccount


# Custom decorator implementaion
#
# **P keeps the wrapped function's signature intact, and T narrows
# `Awaitable[T | None]` to `Awaitable[T]`: retrying until a value appears is
# exactly what removes None from the result type, so callers get a plain `str`
# rather than `str | None` they would have to re-check.
def retrier[**P, T](attempts: int) -> Callable[[Callable[P, Awaitable[T | None]]], Callable[P, Awaitable[T]]]:
    def decorator(func: Callable[P, Awaitable[T | None]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            for attempt in range(1, attempts + 1):
                result = await func(*args, **kwargs)

                if result:
                    return result

                if attempt < attempts:
                    await asyncio.sleep(1)

            raise AssertionError(f"Activation token is not recieved after {attempts} attempts")

        return wrapper

    return decorator


# Composite facade implementation
class AccountHelper:
    def __init__(self, dm_account_api: DmApiAccount, mailhog_api: MailHogApi) -> None:
        self.dm_account_api = dm_account_api
        self.mailhog_api = mailhog_api

    @allure.step("New user registration")
    async def register_new_user(self, login: str, password: str, email: str) -> httpx.Response:
        registration = Registration(login=login, password=password, email=email)
        resp_acc = await self.dm_account_api.account_api.post_v1_account(registration=registration)

        return resp_acc

    @overload
    async def activate_user(self, login: str, validate_response: Literal[True] = True) -> UserEnvelope: ...

    @overload
    async def activate_user(self, login: str, validate_response: Literal[False]) -> httpx.Response: ...

    @allure.step("Activate user's account")
    async def activate_user(self, login: str, validate_response: bool = True) -> UserEnvelope | httpx.Response:
        token = await self._get_activation_token_by_login(login=login)

        # Branching on the flag (rather than forwarding it) is what lets the
        # overloads above resolve: each call site passes a Literal, so the client
        # returns a concrete type instead of a union.
        if validate_response:
            return await self.dm_account_api.account_api.put_v1_account_token(token=token, validate_response=True)

        return await self.dm_account_api.account_api.put_v1_account_token(token=token, validate_response=False)

    @overload
    async def change_email(
        self, login: str, password: str, email: str, validate_response: Literal[True] = True
    ) -> UserEnvelope: ...

    @overload
    async def change_email(
        self, login: str, password: str, email: str, validate_response: Literal[False]
    ) -> httpx.Response: ...

    @allure.step("Change email address")
    async def change_email(
        self, login: str, password: str, email: str, validate_response: bool = True
    ) -> UserEnvelope | httpx.Response:
        change_email = ChangeEmail(login=login, password=password, email=email)

        if validate_response:
            return await self.dm_account_api.account_api.put_v1_account_email(
                change_email=change_email, validate_response=True
            )

        return await self.dm_account_api.account_api.put_v1_account_email(
            change_email=change_email, validate_response=False
        )

    @overload
    async def user_login(
        self,
        login: str,
        password: str,
        remember_me: bool = True,
        validate_response: Literal[True] = True,
        validate_headers: bool = False,
    ) -> UserEnvelope: ...

    @overload
    async def user_login(
        self,
        login: str,
        password: str,
        remember_me: bool = True,
        *,
        validate_response: Literal[False],
        validate_headers: bool = False,
    ) -> httpx.Response: ...

    @allure.step("User login")
    async def user_login(
        self,
        login: str,
        password: str,
        remember_me: bool = True,
        validate_response: bool = True,
        validate_headers: bool = False,
    ) -> UserEnvelope | httpx.Response:
        login_credentials = LoginCredentials(login=login, password=password, remember_me=remember_me)

        if validate_response:
            return await self.dm_account_api.login_api.post_v1_account_login(
                login_credentials=login_credentials, validate_response=True
            )

        resp_acc_login = await self.dm_account_api.login_api.post_v1_account_login(
            login_credentials=login_credentials, validate_response=False
        )

        if validate_headers:
            # Reading the auth token off the response headers only makes sense
            # for a raw httpx.Response, which is why the overloads pair
            # validate_headers with validate_response=False.
            assert resp_acc_login.headers["x-dm-auth-token"], "Token has not been recieved"

        return resp_acc_login

    @overload
    async def get_user_info(
        self, token: str | None = None, validate_response: Literal[True] = True
    ) -> UserDetailsEnvelope: ...

    @overload
    async def get_user_info(self, token: str | None = None, *, validate_response: Literal[False]) -> httpx.Response: ...

    @allure.step("Get user's account info")
    async def get_user_info(
        self, token: str | None = None, validate_response: bool = True
    ) -> UserDetailsEnvelope | httpx.Response:
        headers = {"x-dm-auth-token": token} if token else None

        if validate_response:
            return await self.dm_account_api.account_api.get_v1_account(validate_response=True, headers=headers)

        return await self.dm_account_api.account_api.get_v1_account(validate_response=False, headers=headers)

    @overload
    async def change_password(
        self,
        login: str,
        email: str,
        old_password: str,
        new_password: str,
        validate_response: Literal[True] = True,
    ) -> UserEnvelope: ...

    @overload
    async def change_password(
        self,
        login: str,
        email: str,
        old_password: str,
        new_password: str,
        validate_response: Literal[False],
    ) -> httpx.Response: ...

    @allure.step("Get user's password")
    async def change_password(
        self,
        login: str,
        email: str,
        old_password: str,
        new_password: str,
        validate_response: bool = True,
    ) -> UserEnvelope | httpx.Response:
        reset_password = ResetPassword(login=login, email=email)

        if validate_response:
            await self.dm_account_api.account_api.post_v1_account_password(
                reset_password=reset_password, validate_response=True
            )
        else:
            await self.dm_account_api.account_api.post_v1_account_password(
                reset_password=reset_password, validate_response=False
            )

        token = await self._get_reset_password_token_by_login(login=login)

        change_password = ChangePassword(
            login=login,
            token=token,
            old_password=old_password,
            new_password=new_password,
        )

        if validate_response:
            return await self.dm_account_api.account_api.put_v1_account_password(
                change_password, validate_response=True
            )

        return await self.dm_account_api.account_api.put_v1_account_password(change_password, validate_response=False)

    @allure.step("User logout")
    async def user_logout(self, token: str | None = None) -> httpx.Response:
        headers = {"x-dm-auth-token": token} if token else None
        resp_logout = await self.dm_account_api.login_api.delete_v1_account_login(headers=headers)

        return resp_logout

    @allure.step("User logout from all devices")
    async def user_logout_all(self, token: str | None = None) -> httpx.Response:
        headers = {"x-dm-auth-token": token} if token else None
        resp_logout_all = await self.dm_account_api.login_api.delete_v1_account_login_all(headers=headers)

        return resp_logout_all

    @allure.step("Authenticate client")
    async def authenticate_client(self, login: str, password: str) -> None:
        resp_login = await self.user_login(login=login, password=password, validate_response=False)

        auth_token = {"x-dm-auth-token": resp_login.headers["x-dm-auth-token"]}

        self.dm_account_api.account_api.set_headers(auth_token)
        self.dm_account_api.login_api.set_headers(auth_token)

    @retrier(attempts=5)
    async def _get_activation_token_by_login(self, login: str) -> str | None:
        # Registration emails carry the activation link under 'ConfirmationLinkUrl'.
        return await self._get_token_by_login(login=login, link_field="ConfirmationLinkUrl")

    @retrier(attempts=5)
    async def _get_reset_password_token_by_login(self, login: str) -> str | None:
        # Password-reset emails carry the link under 'ConfirmationLinkUri'.
        return await self._get_token_by_login(login=login, link_field="ConfirmationLinkUri")

    @allure.step("Get activation token from email")
    async def _get_token_by_login(self, login: str, link_field: str) -> str | None:
        resp_get_messages = await self.mailhog_api.mailhog_api.get_api_v2_messages()

        for item in resp_get_messages.json()["items"]:
            # MailHog is a shared inbox: skip messages whose body is not the
            # expected JSON (non-JSON bodies or missing fields).
            try:
                user_data: dict[str, Any] = loads(item["Content"]["Body"])

                if user_data["Login"] != login:
                    continue

                link: str = user_data[link_field]

            except (JSONDecodeError, KeyError, TypeError):
                continue

            return link.split("/")[-1]

        return None
