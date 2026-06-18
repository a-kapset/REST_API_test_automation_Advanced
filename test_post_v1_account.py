import requests
from pprint import pprint
from json import loads

def test_post_v1_account():
    
    login = 'ab1'
    email = f"{login}@test.com"
    password = 'qwerty123'    
    
    # register
    json_data = {
        'login': login,
        'email': email,
        'password': password,
    }

    response = requests.post('http://185.185.143.231:5051/v1/account', json=json_data)    
    assert response.status_code == 201, f"User has not been created. Response: {response.json()}"
    
    
    # get emails
    params = {
        'limit': '50',
    }

    response = requests.get('http://185.185.143.231:5025/api/v2/messages', params=params, verify=False)
    assert response.status_code == 200, f"Mails have not been recieved. Response: {response.json()}"
    
    # get activation token
    for item in response.json()['items']:
        user_data = loads(item['Content']['Body'])
        user_login = user_data['Login']
        
        if user_login == login:        
            token = user_data['ConfirmationLinkUrl'].split('/')[-1]
    
    assert token is not None
    
    
    # activate
    headers = {
        'accept': 'text/plain'
    }
    
    response = requests.put(f"http://185.185.143.231:5051/v1/account/{token}", headers=headers)
    assert response.status_code == 200, f"User has not been activated. Response: {response.json()}"


    # auth
    json_data = {
        'login': login,
        'password': password,
        'rememberMe': True,
    }

    response = requests.post('http://185.185.143.231:5051/v1/account/login', json=json_data)
    assert response.status_code == 200, f"User has not been logged in. Response: {response.json()}"