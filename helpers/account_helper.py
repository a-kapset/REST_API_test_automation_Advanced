import time
from json import loads, JSONDecodeError
from retrying import retry
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
    
    
    def create_new_user(self, login: str, password: str, email: str, status_code: int = 201):
                 
        json_data = {
            'login': login,
            'email': email,
            'password': password,
        }       
        
        resp_acc = self.dm_account_api.account_api.post_v1_account(json_data=json_data)
        assert resp_acc.status_code == status_code, f"Error occurred during user creation. Response: {resp_acc.json()}"
        
        return resp_acc
    
    
    def register_a_user(self, login: str):
        
        token = self._get_activation_token_by_login(login=login)
        assert token is not None
        
        resp_acc_token = self.dm_account_api.account_api.put_v1_account_token(token=token)
        assert resp_acc_token.status_code == 200, f"Error occurred during user activation. Response: {resp_acc_token.json()}"
        
        return resp_acc_token
    
    
    def change_email(self, login: str, password: str, email: str):
            
        json_data = {
            'login': login,        
            'password': password,
            'email': email
        }
        
        resp_acc_email = self.dm_account_api.account_api.put_v1_account_email(json_data)
        assert resp_acc_email.status_code == 200, f"Error occurred during email updating. Response: {resp_acc_email.json()}"
        
        return resp_acc_email
    
    
    def user_login(self, login: str, password: str, rememberMe: bool = True, status_code: int = 200):
        
        json_data = {
            'login': login,        
            'password': password,
            'rememberMe': rememberMe
        }
        
        resp_acc_login = self.dm_account_api.login_api.post_v1_account_login(json_data)        
        assert resp_acc_login.status_code == status_code, f"Error occurred during logging in. Response: {resp_acc_login.json()}"
        
        return resp_acc_login
    

    def get_user_info(self, status_code: int = 200):
        resp_acc = self.dm_account_api.account_api.get_v1_account()
        assert resp_acc.status_code == status_code, f"Error occurred during getting user's info. Response: {resp_acc.json()}"

        return resp_acc
    
    
    def change_password(self, login: str, email: str, old_password: str, new_password: str):
        reset_pass_data  = {
            'login': login,
            'email': email
        }

        resp_pass_reset = self.dm_account_api.account_api.post_v1_account_password(reset_pass_data)
        assert resp_pass_reset.status_code == 200, f"Error occurred during resetting user's password. Response: {resp_pass_reset.json()}"

        token = self._get_reset_password_token_by_login(login=login)
        assert token is not None

        change_pass_data  = {
            'login': login,
            'token': token,
            'oldPassword': old_password,
            'newPassword': new_password
        }

        resp_pass_change = self.dm_account_api.account_api.put_v1_account_password(change_pass_data)
        assert resp_pass_change.status_code == 200, f"Error occurred during resetting user's password. Response: {resp_pass_change.json()}"

        return resp_pass_change
    

    def user_logout(self):
        resp_logout = self.dm_account_api.login_api.delete_v1_account_login()
        assert resp_logout.status_code == 204, f"Error occurred during logging out. Response: {resp_logout.json()}"

        return resp_logout
    

    def user_logout_all(self):
        resp_logout_all = self.dm_account_api.login_api.delete_v1_account_login_all()
        assert resp_logout_all.status_code == 204, f"Error occurred during logging out from all devices. Response: {resp_logout_all.json()}"

        return resp_logout_all


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
    

    def _authenticate_client(self, login: str, password: str):
        resp_login = self.user_login(login=login, password=password)

        auth_token = {
            'x-dm-auth-token': resp_login.headers['x-dm-auth-token']
        }

        self.dm_account_api.account_api.set_headers(auth_token)
        self.dm_account_api.login_api.set_headers(auth_token)