from services.dm_api_account import DmApiAccount
from services.api_mailhog import MailHogApi
from json import loads

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
        
        response_post_v1_account = self.dm_account_api.account_api.post_v1_account(json_data=json_data)
        assert response_post_v1_account.status_code == status_code, f"Error occurred during user creation. Response: {response_post_v1_account.json()}"
        
        return response_post_v1_account
    
    
    def register_a_user(self, login: str):
        
        response_get_api_v2_messages = self.mailhog_api.mailhog_api.get_api_v2_messages()
        assert response_get_api_v2_messages.status_code == 200, f"Error occurred during mail receiving. Response: {response_get_api_v2_messages.json()}"
        
        token = self.get_activation_token_by_login(login=login, response=response_get_api_v2_messages)
        assert token is not None
        
        response_put_v1_account_token = self.dm_account_api.account_api.put_v1_account_token(token=token)
        assert response_put_v1_account_token.status_code == 200, f"Error occurred during user activation. Response: {response_put_v1_account_token.json()}"
        
        return response_put_v1_account_token
    
    
    def change_email(self, login: str, password: str, email: str):
            
        json_data = {
            'login': login,        
            'password': password,
            'email': email
        }
        response_put_v1_account_email = self.dm_account_api.account_api.put_v1_account_email(json_data)
        assert response_put_v1_account_email.status_code == 200, f"Error occurred during email updating. Response: {response_put_v1_account_email.json()}"
        
        return response_put_v1_account_email
    
    
    def user_login(self, login: str, password: str, rememberMe: bool = True, status_code: int = 200):
        
        json_data = {
            'login': login,        
            'password': password,
            'rememberMe': rememberMe
        }
        
        response = self.dm_account_api.login_api.post_v1_account_login(json_data)        
        assert response.status_code == status_code, f"Error occurred during logging in. Response: {response.json()}"
        
        return response
        
    
    @staticmethod
    def get_activation_token_by_login(login, response):
        token = None
        
        for item in response.json()['items']:
            user_data = loads(item['Content']['Body'])
            user_login = user_data['Login']
            
            if user_login == login:        
                token = user_data['ConfirmationLinkUrl'].split('/')[-1]
                
        return token    