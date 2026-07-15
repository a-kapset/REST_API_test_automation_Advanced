import asyncio
import allure
import httpx
from collections.abc import Awaitable, Callable
from json import loads, JSONDecodeError
from typing import Any, TypeVar
from services.dm_api_account import DmApiAccount
from services.api_mailhog import MailHogApi
from clients.http.dm_api_account.models.api_models import (
    ChangeEmail,
    ChangePassword,
    LoginCredentials,
    Registration,
    ResetPassword,
    UserEnvelope,
)


F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


# Custom decorator implementaion
def retrier(n: int) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            token = None
            counter = 0

            while token is None:
                token = await func(*args, **kwargs)
                counter += 1

                if token:
                    return token

                if counter > 5:
                    raise AssertionError(f"Activation token is not recieved after {n} attempts")

                await asyncio.sleep(1)

        return wrapper  # type: ignore[return-value]

    return decorator


# Composite facade implementation
class AccountHelper:
    def __init__(self, dm_account_api: DmApiAccount, mailhog_api: MailHogApi) -> None:
        self.dm_account_api = dm_account_api
        self.mailhog_api = mailhog_api

    @allure.step("New user registration")
    async def register_new_user(self, login: str, password: str, email: str) -> Any:
        registration = Registration(login=login, password=password, email=email)
        resp_acc = await self.dm_account_api.account_api.post_v1_account(registration=registration)

        return resp_acc

    @allure.step("Activate user's account")
    async def activate_user(self, login: str, validate_response: bool = True) -> Any:
        token = await self._get_activation_token_by_login(login=login)
        account_api = self.dm_account_api.account_api

        if validate_response:
            return await account_api.put_v1_account_token(token=token)

        return await account_api.put_v1_account_token_with_http_info(token=token)

    @allure.step("Change email address")
    async def change_email(self, login: str, password: str, email: str, validate_response: bool = True) -> Any:
        change_email = ChangeEmail(login=login, password=password, email=email)
        account_api = self.dm_account_api.account_api

        if validate_response:
            return await account_api.put_v1_account_email(change_email=change_email)

        return await account_api.put_v1_account_email_with_http_info(change_email=change_email)

    @allure.step("User login")
    async def user_login(
        self,
        login: str,
        password: str,
        remember_me: bool = True,
        status_code: int = 200,
        validate_response: bool = True,
        validate_headers: bool = False,
    ) -> Any:
        # rememberMe uses the field's alias: the generated model declares it with
        # alias="rememberMe" (no populate_by_name), so it is built by alias.
        login_credentials = LoginCredentials(login=login, password=password, rememberMe=remember_me)
        login_api = self.dm_account_api.login_api

        resp_acc_login: UserEnvelope | httpx.Response
        if validate_response:
            resp_acc_login = await login_api.post_v1_account_login(login_credentials=login_credentials)
        else:
            resp_acc_login = await login_api.post_v1_account_login_with_http_info(login_credentials=login_credentials)

        if validate_headers:
            # Reading the auth token off the response headers only makes sense
            # for a raw httpx.Response (i.e. validate_response=False); a parsed
            # model has no headers.
            assert isinstance(resp_acc_login, httpx.Response), "validate_headers=True requires validate_response=False"
            assert resp_acc_login.headers["x-dm-auth-token"], "Token has not been recieved"

        return resp_acc_login

    @allure.step("Get user's account info")
    async def get_user_info(
        self,
        token: str | None = None,
        validate_response: bool = True,
        **kwargs: Any,
    ) -> Any:
        # An empty token is stringified to "" by the generated client and thus
        # dropped, so a client already carrying the auth header (see
        # authenticate_client) stays authenticated.
        x_dm_auth_token = token or ""
        account_api = self.dm_account_api.account_api

        if validate_response:
            return await account_api.get_v1_account(x_dm_auth_token=x_dm_auth_token, **kwargs)

        return await account_api.get_v1_account_with_http_info(x_dm_auth_token=x_dm_auth_token, **kwargs)

    @allure.step("Get user's password")
    async def change_password(
        self,
        login: str,
        email: str,
        old_password: str,
        new_password: str,
        validate_response: bool = True,
    ) -> Any:
        reset_password = ResetPassword(login=login, email=email)
        account_api = self.dm_account_api.account_api

        if validate_response:
            await account_api.post_v1_account_password(reset_password=reset_password)
        else:
            await account_api.post_v1_account_password_with_http_info(reset_password=reset_password)

        token = await self._get_reset_password_token_by_login(login=login)

        # oldPassword/newPassword use the fields' aliases (see user_login).
        change_password = ChangePassword(
            login=login,
            token=token,
            oldPassword=old_password,
            newPassword=new_password,
        )

        if validate_response:
            return await account_api.put_v1_account_password(change_password=change_password)

        return await account_api.put_v1_account_password_with_http_info(change_password=change_password)

    @allure.step("User logout")
    async def user_logout(self, token: str | None = None, **kwargs: Any) -> Any:
        return await self.dm_account_api.login_api.delete_v1_account_login(x_dm_auth_token=token or "", **kwargs)

    @allure.step("User logout from all devices")
    async def user_logout_all(self, token: str | None = None, **kwargs: Any) -> Any:
        return await self.dm_account_api.login_api.delete_v1_account_login_all(x_dm_auth_token=token or "", **kwargs)

    @allure.step("Authenticate client")
    async def authenticate_client(self, login: str, password: str) -> None:
        resp_login = await self.user_login(login=login, password=password, validate_response=False)

        auth_token = {"x-dm-auth-token": resp_login.headers["x-dm-auth-token"]}

        # The generated API clients share one api_client (httpx.AsyncClient);
        # persisting the auth header there authenticates every later request.
        self.dm_account_api.api_client.set_headers(auth_token)

    @retrier(n=5)
    async def _get_activation_token_by_login(self, login: str) -> Any:
        # Registration emails carry the activation link under 'ConfirmationLinkUrl'.
        return await self._get_token_by_login(login=login, link_field="ConfirmationLinkUrl")

    @retrier(n=5)
    async def _get_reset_password_token_by_login(self, login: str) -> Any:
        # Password-reset emails carry the link under 'ConfirmationLinkUri'.
        return await self._get_token_by_login(login=login, link_field="ConfirmationLinkUri")

    @allure.step("Get activation token from email")
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

            return link.split("/")[-1]

        return None
