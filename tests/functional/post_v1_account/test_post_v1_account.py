import time
from json import loads
from dm_api_account.apis.account_api import AccountApi
from dm_api_account.apis.login_api import LoginApi
from api_mailhog.apis.mailhog_api import MailhogApi

def test_post_v1_account():
    
    account_api = AccountApi(host='http://185.185.143.231:5051')
    login_api = LoginApi(host='http://185.185.143.231:5051')
    mailhog_api = MailhogApi(host='http://185.185.143.231:5025')
    
    login = f'ab{int(time.time())}'
    email = f"{login}@test.com"
    password = 'qwerty123'    
    
    # register
    json_data = {
        'login': login,
        'email': email,
        'password': password,
    }
    response = account_api.post_v1_account(json_data=json_data)
    assert response.status_code == 201, f"User has not been created. Response: {response.json()}"
    
    
    # get emails
    response = mailhog_api.get_api_v2_messages()
    assert response.status_code == 200, f"Mails have not been recieved. Response: {response.json()}"
    
    # get activation token
    token = get_activation_token_by_login(login, response)    
    assert token is not None    
    
    # activate
    response = account_api.put_v1_account_token(token=token)
    assert response.status_code == 200, f"User has not been activated. Response: {response.json()}"

    # auth
    json_data = {
        'login': login,        
        'password': password,
        'rememberMe': True
    }
    response = login_api.post_v1_account_login(json_data)
    assert response.status_code == 200, f"User has not been logged in. Response: {response.json()}"
        

def get_activation_token_by_login(login, response):
    token = None
    
    for item in response.json()['items']:
        user_data = loads(item['Content']['Body'])
        user_login = user_data['Login']
        
        if user_login == login:        
            token = user_data['ConfirmationLinkUrl'].split('/')[-1]
            
    return token