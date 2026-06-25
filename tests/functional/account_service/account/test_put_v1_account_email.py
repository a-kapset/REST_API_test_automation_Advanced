import time
from json import loads
from dm_api_account.apis.account_api import AccountApi
from dm_api_account.apis.login_api import LoginApi
from api_mailhog.apis.mailhog_api import MailhogApi

def test_put_v1_account_email():
    
    account_api = AccountApi(host='http://185.185.143.231:5051')
    login_api = LoginApi(host='http://185.185.143.231:5051')
    mailhog_api = MailhogApi(host='http://185.185.143.231:5025')
    
    login = f'bc_{int(time.time())}'
    email = f"{login}@test.com"
    password = 'qwerty123'
    changed_email = f"changed_{email}"

    # Регистрируемся
    json_data = {
        'login': login,
        'email': email,
        'password': password,
    }
    response = account_api.post_v1_account(json_data=json_data)
    assert response.status_code == 201, f"User has not been created. Response: {response.json()}"
    
    
    # Получаем активационный токен
    response = mailhog_api.get_api_v2_messages()
    assert response.status_code == 200, f"Mails have not been recieved. Response: {response.json()}"    
    token = get_activation_token_by_login(login, response)    
    assert token is not None  
    
    
    # Активируем пользователя
    response = account_api.put_v1_account_token(token=token)
    assert response.status_code == 200, f"User has not been activated. Response: {response.json()}"

    
    # Заходим в приложение
    json_data = {
        'login': login,        
        'password': password,
        'rememberMe': True
    }
    response = login_api.post_v1_account_login(json_data)
    assert response.status_code == 200, f"User has not been logged in. Response: {response.json()}"


    # Меняем емейл
    json_data = {
        'login': login,        
        'password': password,
        'email': changed_email
    }
    response = account_api.put_v1_account_email(json_data)
    assert response.status_code == 200, f"Email has not been updated. Response: {response.json()}"


    # Пытаемся войти, получаем 403
    json_data = {
        'login': login,        
        'password': password,
        'rememberMe': True
    }
    response = login_api.post_v1_account_login(json_data)
    assert response.status_code == 403, f"User has not been logged in. Response: {response.json()}"


    # На почте находим токен по новому емейлу для подтверждения смены емейла
    response = mailhog_api.get_api_v2_messages()
    assert response.status_code == 200, f"Mails have not been recieved. Response: {response.json()}"    
    token = get_activation_token_by_login(login, response)    
    assert token is not None


    # Активируем новый токен
    response = account_api.put_v1_account_token(token=token)
    assert response.status_code == 200, f"User has not been activated. Response: {response.json()}"

    
    # Заходим в приложение активации нового емейла
    json_data = {
        'login': login,        
        'password': password,
        'rememberMe': True
    }
    response = login_api.post_v1_account_login(json_data)
    assert response.status_code == 200, f"User has not been logged in. Response: {response.json()}"


# TODO: move to helpers
def get_activation_token_by_login(login, response):
    token = None
    
    for item in response.json()['items']:
        user_data = loads(item['Content']['Body'])
        user_login = user_data['Login']
        
        if user_login == login:        
            token = user_data['ConfirmationLinkUrl'].split('/')[-1]
            
    return token