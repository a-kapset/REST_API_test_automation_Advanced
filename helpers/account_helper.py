from services.dm_api_account import DmApiAccount
from services.api_mailhog import MailHogApi
from json import loads

# Composite facade implementation

class AccountHelper:
    def __init__(self, dm_account_api: DmApiAccount, mailhog_api: MailHogApi):
        self.dm_account_api = dm_account_api
        self.mailhog_api = mailhog_api
    
    def register_new_user(self, login: str, password: str, email: str):
                
        json_data = {
            'login': login,
            'email': email,
            'password': password,
        }
        
        response_post_v1_account = self.dm_account_api.account_api.post_v1_account(json_data=json_data)
        assert response_post_v1_account.status_code == 201, f"User has not been created. Response: {response_post_v1_account.json()}"
        
        response_get_api_v2_messages = self.mailhog_api.mailhog_api.get_api_v2_messages()
        assert response_get_api_v2_messages.status_code == 200, f"Mails have not been recieved. Response: {response_get_api_v2_messages.json()}"
        
        token = self.get_activation_token_by_login(login=login, response=response_get_api_v2_messages)
        assert token is not None
        
        response_put_v1_account_token = self.dm_account_api.account_api.put_v1_account_token(token=token)
        assert response_put_v1_account_token.status_code == 200, f"User has not been activated. Response: {response_put_v1_account_token.json()}"
        
        return response_put_v1_account_token
    
    
    def user_login(self, login: str, password: str, rememberMe: bool):
        
        json_data = {
            'login': login,        
            'password': password,
            'rememberMe': rememberMe
        }
        
        response = self.dm_account_api.login_api.post_v1_account_login(json_data)        
        assert response.status_code == 200, f"User has not been logged in. Response: {response.json()}"
        
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