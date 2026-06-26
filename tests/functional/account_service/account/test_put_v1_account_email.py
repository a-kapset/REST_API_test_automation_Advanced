import time
import structlog
from helpers.account_helper import AccountHelper
from restclient.configuration import Configuration
from services.dm_api_account import DmApiAccount
from services.api_mailhog import MailHogApi

structlog.configure(
    processors=[
        structlog.processors.JSONRenderer(indent=4, ensure_ascii=True, sort_keys=True)
    ]
)

def test_put_v1_account_email():
    
    dm_api_configuration = Configuration(host='http://185.185.143.231:5051', disable_log=False)
    mailhog_api_configuration = Configuration(host='http://185.185.143.231:5025', disable_log=True)

    account = DmApiAccount(dm_api_configuration)
    mailhog = MailHogApi(mailhog_api_configuration)

    account_helper = AccountHelper(dm_account_api=account, mailhog_api=mailhog)

    login = f'bc{int(time.time())}'
    email = f"{login}@test.com"
    password = 'qwerty123'
    changed_email = f"changed_{email}"

    account_helper.create_new_user(login=login, password=password, email=email)
    account_helper.register_a_user(login=login)
    account_helper.user_login(login=login, password=password)
    account_helper.change_email(login=login, password=password, email=changed_email)
    account_helper.user_login(login=login, password=password, status_code=403)
    account_helper.register_a_user(login=login)
    account_helper.user_login(login=login, password=password)