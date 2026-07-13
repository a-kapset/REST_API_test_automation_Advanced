import asyncio
import allure
from json import loads, JSONDecodeError
from clients.http.dm_api_account.models.change_email import ChangeEmail
from clients.http.dm_api_account.models.change_password import ChangePassword
from clients.http.dm_api_account.models.login_credentials import LoginCredentials
from clients.http.dm_api_account.models.registration import Registration
from clients.http.dm_api_account.models.reset_password import ResetPassword
from services.dm_api_account import DmApiAccount
from services.api_mailhog import MailHogApi


# Custom decorator implementaion
def retrier(n: int):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            token = None
            counter = 0

            while token is None:
                token = await func(*args, **kwargs)
                counter += 1

                if token:
                    return token

                if counter > 5:
                    raise AssertionError(f'Activation token is not recieved after {n} attempts')

                await asyncio.sleep(1)

        return wrapper

    return decorator

# Composite facade implementation
class AccountHelper:
    def __init__(self, dm_account_api: DmApiAccount, mailhog_api: MailHogApi):
        self.dm_account_api = dm_account_api
        self.mailhog_api = mailhog_api
    
    @allure.step("New user registration")
    async def register_new_user(self, login: str, password: str, email: str):
        registration = Registration(login=login, password=password, email=email)
        resp_acc = await self.dm_account_api.account_api.post_v1_account(registration=registration)

        return resp_acc

    @allure.step("Activate user's account")
    async def activate_user(self, login: str, validate_response: bool = True):
        token = await self._get_activation_token_by_login(login=login)
        resp_acc_token = await self.dm_account_api.account_api.put_v1_account_token(token=token, validate_response=validate_response)

        return resp_acc_token

    @allure.step("Change email address")
    async def change_email(self, login: str, password: str, email: str, validate_response: bool = True):
        change_email = ChangeEmail(login=login, password=password, email=email)
        resp_acc_email = await self.dm_account_api.account_api.put_v1_account_email(change_email=change_email, validate_response=validate_response)

        return resp_acc_email

    @allure.step("User login")
    async def user_login(self, login: str, password: str, remember_me: bool = True, status_code: int = 200, validate_response: bool = True, validate_headers: bool = False):
        login_credentials = LoginCredentials(login=login, password=password, remember_me=remember_me)
        resp_acc_login = await self.dm_account_api.login_api.post_v1_account_login(login_credentials=login_credentials, validate_response=validate_response)

        if validate_headers:
            assert resp_acc_login.headers['x-dm-auth-token'], 'Token has not been recieved'

        return resp_acc_login

    @allure.step("Get user's account info")
    async def get_user_info(self, token=None, validate_response: bool = True, **kwargs):
        if token:
            kwargs['headers'] = {'x-dm-auth-token': token}

        resp_acc = await self.dm_account_api.account_api.get_v1_account(validate_response=validate_response, **kwargs)

        return resp_acc


    @allure.step("Get user's password")
    async def change_password(self, login: str, email: str, old_password: str, new_password: str, validate_response: bool = True):
        reset_password = ResetPassword(login=login, email=email)
        await self.dm_account_api.account_api.post_v1_account_password(reset_password=reset_password, validate_response=validate_response)
        token = await self._get_reset_password_token_by_login(login=login)

        change_password = ChangePassword(
            login=login,
            token=token,
            old_password=old_password,
            new_password=new_password
        )

        resp_pass_change = await self.dm_account_api.account_api.put_v1_account_password(change_password, validate_response=validate_response)

        return resp_pass_change

    @allure.step("User logout")
    async def user_logout(self, token=None, **kwargs):
        if token:
            kwargs['headers'] = {'x-dm-auth-token': token}

        resp_logout = await self.dm_account_api.login_api.delete_v1_account_login(**kwargs)

        return resp_logout

    @allure.step("User logout from all devices")
    async def user_logout_all(self, token=None, **kwargs):
        if token:
            kwargs['headers'] = {'x-dm-auth-token': token}

        resp_logout_all = await self.dm_account_api.login_api.delete_v1_account_login_all(**kwargs)

        return resp_logout_all

    @allure.step("Authenticate client")
    async def authenticate_client(self, login: str, password: str):
        resp_login = await self.user_login(login=login, password=password, validate_response=False)

        auth_token = {
            'x-dm-auth-token': resp_login.headers['x-dm-auth-token']
        }

        self.dm_account_api.account_api.set_headers(auth_token)
        self.dm_account_api.login_api.set_headers(auth_token)


    @retrier(n=5)
    async def _get_activation_token_by_login(self, login):
        # Registration emails carry the activation link under 'ConfirmationLinkUrl'.
        return await self._get_token_by_login(login=login, link_field='ConfirmationLinkUrl')


    @retrier(n=5)
    async def _get_reset_password_token_by_login(self, login):
        # Password-reset emails carry the link under 'ConfirmationLinkUri'.
        return await self._get_token_by_login(login=login, link_field='ConfirmationLinkUri')

    @allure.step("Get activation token from email")
    async def _get_token_by_login(self, login, link_field):
        resp_get_messages = await self.mailhog_api.mailhog_api.get_api_v2_messages()

        for item in resp_get_messages.json()['items']:
            # MailHog is a shared inbox: skip messages whose body is not the
            # expected JSON (non-JSON bodies or missing fields).
            try:
                user_data = loads(item['Content']['Body'])

                if user_data['Login'] != login:
                    continue

                link = user_data[link_field]

            except (JSONDecodeError, KeyError, TypeError):
                continue

            return link.split('/')[-1]

        return None