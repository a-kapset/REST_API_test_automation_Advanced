import asyncio
import functools
from collections.abc import Awaitable, Callable
from json import JSONDecodeError, loads
from typing import Literal, overload
from uuid import UUID

import allure
import httpx

from clients.http.dm_api_account.models.api_models import (
    ChangeEmail,
    ChangePassword,
    LoginCredentials,
    Registration,
    ResetPassword,
    UserDetailsEnvelope,
    UserEnvelope,
)
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

        return await self.dm_account_api.account_api.post_v1_account(registration=registration)

    @overload
    async def activate_user(self, login: str, validate_response: Literal[True] = True) -> UserEnvelope: ...

    @overload
    async def activate_user(self, login: str, validate_response: Literal[False]) -> httpx.Response: ...

    @allure.step("Activate user's account")
    async def activate_user(self, login: str, validate_response: bool = True) -> UserEnvelope | httpx.Response:
        token = await self._get_activation_token_by_login(login=login)
        account_api = self.dm_account_api.account_api

        # Branching on the flag (rather than forwarding it) is what lets the
        # overloads resolve: each call site passes a Literal, so the concrete
        # generated method returns a concrete type instead of a union.
        if validate_response:
            return await account_api.put_v1_account_token(token=token)

        return await account_api.put_v1_account_token_with_http_info(token=token)

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
        account_api = self.dm_account_api.account_api

        if validate_response:
            return await account_api.put_v1_account_email(change_email=change_email)

        return await account_api.put_v1_account_email_with_http_info(change_email=change_email)

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
        # rememberMe uses the field's alias: the generated model declares it with
        # alias="rememberMe" (no populate_by_name), so it is built by alias.
        login_credentials = LoginCredentials(login=login, password=password, rememberMe=remember_me)
        login_api = self.dm_account_api.login_api

        if validate_response:
            return await login_api.post_v1_account_login(login_credentials=login_credentials)

        resp_acc_login = await login_api.post_v1_account_login_with_http_info(login_credentials=login_credentials)

        if validate_headers:
            # Reading the auth token off the response headers only makes sense for
            # a raw httpx.Response, which is why the overloads pair validate_headers
            # with validate_response=False.
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
        # An empty token is dropped by the generated client's header filter, so a
        # client already carrying the auth header (see authenticate_client) stays
        # authenticated.
        x_dm_auth_token = token or ""
        account_api = self.dm_account_api.account_api

        if validate_response:
            return await account_api.get_v1_account(x_dm_auth_token=x_dm_auth_token)

        return await account_api.get_v1_account_with_http_info(x_dm_auth_token=x_dm_auth_token)

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

    @allure.step("Change user's password")
    async def change_password(
        self,
        login: str,
        email: str,
        old_password: str,
        new_password: str,
        validate_response: bool = True,
    ) -> UserEnvelope | httpx.Response:
        reset_password = ResetPassword(login=login, email=email)
        account_api = self.dm_account_api.account_api

        if validate_response:
            await account_api.post_v1_account_password(reset_password=reset_password)
        else:
            await account_api.post_v1_account_password_with_http_info(reset_password=reset_password)

        token = await self._get_reset_password_token_by_login(login=login)

        # The reset token from the email is a UUID string; the generated model
        # types this field as UUID. oldPassword/newPassword use the fields'
        # aliases (see user_login).
        change_password = ChangePassword(
            login=login,
            token=UUID(token),
            oldPassword=old_password,
            newPassword=new_password,
        )

        if validate_response:
            return await account_api.put_v1_account_password(change_password=change_password)

        return await account_api.put_v1_account_password_with_http_info(change_password=change_password)

    @allure.step("User logout")
    async def user_logout(self, token: str | None = None) -> httpx.Response:
        return await self.dm_account_api.login_api.delete_v1_account_login(x_dm_auth_token=token or "")

    @allure.step("User logout from all devices")
    async def user_logout_all(self, token: str | None = None) -> httpx.Response:
        return await self.dm_account_api.login_api.delete_v1_account_login_all(x_dm_auth_token=token or "")

    @allure.step("Authenticate client")
    async def authenticate_client(self, login: str, password: str) -> None:
        resp_login = await self.user_login(login=login, password=password, validate_response=False)

        auth_token = {"x-dm-auth-token": resp_login.headers["x-dm-auth-token"]}

        # AccountApi and LoginApi share one RestClient (see DmApiAccount);
        # persisting the auth header there authenticates every later request.
        self.dm_account_api.api_client.set_headers(auth_token)

    @retrier(attempts=5)
    async def _get_activation_token_by_login(self, login: str) -> str | None:
        # Registration emails carry the activation link under 'ConfirmationLinkUrl'.
        return await self._get_token_by_login(login=login, link_field="ConfirmationLinkUrl")

    @retrier(attempts=5)
    async def _get_reset_password_token_by_login(self, login: str) -> str | None:
        # Password-reset emails carry the link under 'ConfirmationLinkUri'.
        return await self._get_token_by_login(login=login, link_field="ConfirmationLinkUri")

    @allure.step("Get token from email")
    async def _get_token_by_login(self, login: str, link_field: str) -> str | None:
        resp_get_messages = await self.mailhog_api.mailhog_api.get_api_v2_messages()

        for item in resp_get_messages.json()["items"]:
            # MailHog is a shared inbox: skip messages whose body is not the
            # expected JSON (non-JSON bodies or missing fields).
            try:
                user_data = loads(item["Content"]["Body"])

                if user_data["Login"] != login:
                    continue

                link = user_data[link_field]

            except (JSONDecodeError, KeyError, TypeError):
                continue

            return str(link).split("/")[-1]

        return None
