import time
from json import loads, JSONDecodeError
from retrying import retry
from dm_api_account.models.change_email import ChangeEmail
from dm_api_account.models.change_password import ChangePassword
from dm_api_account.models.login_credentials import LoginCredentials
from dm_api_account.models.registration import Registration
from dm_api_account.models.reset_password import ResetPassword
from services.dm_api_account import DmApiAccount
from services.api_mailhog import MailHogApi

def retry_if_result_none(result):
    """Return True if we should retry (in this case when result is None), False otherwise"""
    return result is None

# Custom decorator implementaion
def retrier(n: int):
    def decorator(func):
        def wrapper(*args, **kwargs):
            token = None
            counter = 0
            
            while token is None:
                token = func(*args, **kwargs)
                counter += 1
                
                if token:
                    return token
                
                if counter > 5:
                    raise AssertionError(f'Activation token is not recieved after {n} attempts')
                
                time.sleep(1)
        
        return wrapper
        
    return decorator

# Composite facade implementation
class AccountHelper:
    def __init__(self, dm_account_api: DmApiAccount, mailhog_api: MailHogApi):
        self.dm_account_api = dm_account_api
        self.mailhog_api = mailhog_api
    
    
    def register_new_user(self, login: str, password: str, email: str):
        registration = Registration(login=login, password=password, email=email)        
        resp_acc = self.dm_account_api.account_api.post_v1_account(registration=registration)        
        
        return resp_acc
    
    
    def activate_user(self, login: str, validate_response: bool = True):        
        token = self._get_activation_token_by_login(login=login)        
        resp_acc_token = self.dm_account_api.account_api.put_v1_account_token(token=token, validate_response=validate_response)        
        
        return resp_acc_token
    
    
    def change_email(self, login: str, password: str, email: str, validate_response: bool = True):
        change_email = ChangeEmail(login=login, password=password, email=email)
        resp_acc_email = self.dm_account_api.account_api.put_v1_account_email(change_email=change_email, validate_response=validate_response)        
        
        return resp_acc_email
    
    
    def user_login(self, login: str, password: str, remember_me: bool = True, status_code: int = 200, validate_response: bool = True, validate_headers: bool = False):
        login_credentials = LoginCredentials(login=login, password=password, remember_me=remember_me)
        resp_acc_login = self.dm_account_api.login_api.post_v1_account_login(login_credentials=login_credentials, validate_response=validate_response)
        
        if validate_headers:
            assert resp_acc_login.headers['x-dm-auth-token'], 'Token has not been recieved'            

        return resp_acc_login
    

    def get_user_info(self, token=None, validate_response: bool = True, **kwargs):
        if token:
            kwargs['headers'] = {'x-dm-auth-token': token}
            
        resp_acc = self.dm_account_api.account_api.get_v1_account(validate_response=validate_response, **kwargs)        

        return resp_acc
    
    
    def change_password(self, login: str, email: str, old_password: str, new_password: str, validate_response: bool = True):
        reset_password = ResetPassword(login=login, email=email)
        self.dm_account_api.account_api.post_v1_account_password(reset_password=reset_password, validate_response=validate_response)        
        token = self._get_reset_password_token_by_login(login=login)

        change_password = ChangePassword(
            login=login,
            token=token,
            old_password=old_password,
            new_password=new_password
        )

        resp_pass_change = self.dm_account_api.account_api.put_v1_account_password(change_password, validate_response=validate_response)        

        return resp_pass_change
    

    def user_logout(self, token=None, **kwargs):
        if token:
            kwargs['headers'] = {'x-dm-auth-token': token}
            
        resp_logout = self.dm_account_api.login_api.delete_v1_account_login(**kwargs)        

        return resp_logout
    

    def user_logout_all(self, token=None, **kwargs):
        if token:
            kwargs['headers'] = {'x-dm-auth-token': token}
            
        resp_logout_all = self.dm_account_api.login_api.delete_v1_account_login_all(**kwargs)        

        return resp_logout_all
    
    
    def authenticate_client(self, login: str, password: str):
        resp_login = self.user_login(login=login, password=password, validate_response=False)

        auth_token = {
            'x-dm-auth-token': resp_login.headers['x-dm-auth-token']
        }

        self.dm_account_api.account_api.set_headers(auth_token)
        self.dm_account_api.login_api.set_headers(auth_token)    


    @retry(stop_max_attempt_number=5, retry_on_result=retry_if_result_none, wait_fixed=1000)
    def _get_activation_token_by_login(self, login):
        # Registration emails carry the activation link under 'ConfirmationLinkUrl'.
        return self._get_token_by_login(login=login, link_field='ConfirmationLinkUrl')


    @retry(stop_max_attempt_number=5, retry_on_result=retry_if_result_none, wait_fixed=1000)
    def _get_reset_password_token_by_login(self, login):
        # Password-reset emails carry the link under 'ConfirmationLinkUri'.
        return self._get_token_by_login(login=login, link_field='ConfirmationLinkUri')


    def _get_token_by_login(self, login, link_field):
        resp_get_messages = self.mailhog_api.mailhog_api.get_api_v2_messages()
        
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