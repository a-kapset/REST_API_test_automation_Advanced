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
        
        token = self.get_activation_token_by_login(login=login)
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
    
    
    @retry(stop_max_attempt_number=5, retry_on_result=retry_if_result_none, wait_fixed=1000)
    def get_activation_token_by_login(self, login):
        token = None
        resp_get_messages = self.mailhog_api.mailhog_api.get_api_v2_messages()        
        
        for item in resp_get_messages.json()['items']:
            # MailHog is a shared inbox: skip messages whose body is not the
            # expected activation JSON (non-JSON bodies or missing fields).
            try:
                user_data = loads(item['Content']['Body'])
                user_login = user_data['Login']

            except (JSONDecodeError, KeyError, TypeError):
                continue
            
            if user_login == login:        
                token = user_data['ConfirmationLinkUrl'].split('/')[-1]
                
        return token