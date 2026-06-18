import requests

def test_post_v1_account():
    
    login = 'a22'
    email = f"{login}@test.com"
    password = 'qwerty123'    
    
    # register
    json_data = {
        'login': login,
        'email': email,
        'password': password,
    }

    response = requests.post('http://185.185.143.231:5051/v1/account', json=json_data)
    print('\n>>>',response.status_code)
    
    
    # get emails
    params = {
        'limit': '50',
    }

    response = requests.get('http://185.185.143.231:5025/api/v2/messages', params=params, verify=False)
    print('>>>',response.status_code)
    
    
    # TODO: get activation token
    # ...
    
    
    # activate
    response = requests.put('http://185.185.143.231:5051/v1/account/32ebc26a-9f97-41e5-bf7b-090527d91da2')
    print('>>>',response.status_code)


    # auth
    json_data = {
        'login': 'a22',
        'password': 'qwerty123',
        'rememberMe': True,
    }

    response = requests.post('http://185.185.143.231:5051/v1/account/login', json=json_data)
    print('>>>',response.status_code)