import time
from dm_api_account.apis.account_api import AccountApi

def test_post_v1_account():
    
    account_api = AccountApi(host='http://185.185.143.231:5051')
    
    login = f'ab_{int(time.time())}'
    email = f"{login}@test.com"
    password = 'qwerty123'

    # Регистрируемся
    json_data = {
        'login': login,
        'email': email,
        'password': password,
    }
    response = account_api.post_v1_account(json_data=json_data)
    assert response.status_code == 201, f"User has not been created. Response: {response.json()}"