import time
import pytest
import structlog
from collections import namedtuple
from helpers.account_helper import AccountHelper
from restclient.configuration import Configuration
from services.dm_api_account import DmApiAccount
from services.api_mailhog import MailHogApi

structlog.configure(
    processors=[
        structlog.processors.JSONRenderer(indent=4, ensure_ascii=True, sort_keys=True)
    ]
)


@pytest.fixture
def mailhog_api_fxt():
    mailhog_api_configuration = Configuration(host='http://185.185.143.231:5025', disable_log=True)
    mailhog_client = MailHogApi(mailhog_api_configuration)

    return mailhog_client


@pytest.fixture
def dm_account_api_fxt():
    dm_api_configuration = Configuration(host='http://185.185.143.231:5051', disable_log=False)
    account_client = DmApiAccount(dm_api_configuration)

    return account_client


@pytest.fixture
def account_helper_fxt(dm_account_api_fxt, mailhog_api_fxt):
    account_helper = AccountHelper(dm_account_api=dm_account_api_fxt, mailhog_api=mailhog_api_fxt)

    return account_helper


@pytest.fixture
def user_data_fxt():
    login = f'ab{int(time.time())}'
    email = f"{login}@test.com"
    password = 'qwerty123'
    User = namedtuple('User', ['login', 'password', 'email'])
    user = User(login=login, password=password, email=email)
    
    return user