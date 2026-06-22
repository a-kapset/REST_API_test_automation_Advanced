import time
import structlog
from json import loads
from dm_api_account.apis.account_api import AccountApi
from dm_api_account.apis.login_api import LoginApi
from api_mailhog.apis.mailhog_api import MailhogApi
from restclient.configuration import Configuration

structlog.configure(
    processors=[
        structlog.processors.JSONRenderer(indent=4, ensure_ascii=True, sort_keys=True)
    ]
)

def test_post_v1_account():

    dm_api_configuration = Configuration(host='http://185.185.143.231:5051', disable_log=False)
    mailhog_api_configuration = Configuration(host='http://185.185.143.231:5025', disable_log=True)

    account_api = AccountApi(dm_api_configuration)
    login_api = LoginApi(dm_api_configuration)
    mailhog_api = MailhogApi(mailhog_api_configuration)

    login = f'ab{int(time.time())}'
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


# TODO: move to helpers
def get_activation_token_by_login(login, response):
    token = None

    for item in response.json()['items']:
        user_data = loads(item['Content']['Body'])
        user_login = user_data['Login']

        if user_login == login:
            token = user_data['ConfirmationLinkUrl'].split('/')[-1]

    return token
