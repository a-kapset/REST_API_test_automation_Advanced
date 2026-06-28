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


@pytest.fixture(scope='session')
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


@pytest.fixture(scope='function')
def new_user_data_fxt():
    user = _get_user_data()

    return user


@pytest.fixture(scope='module')
def registered_user_data_fxt():
    user = _get_user_data()

    return user


@pytest.fixture
def auth_account_helper_fxt(mailhog_api_fxt):
    dm_api_configuration = Configuration(host='http://185.185.143.231:5051', disable_log=False)
    account_api_client = DmApiAccount(dm_api_configuration)
    account_helper = AccountHelper(dm_account_api=account_api_client, mailhog_api=mailhog_api_fxt)
    
    # TODO: replace hardcoded values with more flexible logic,
    # or remove this fixture since there is registered_auth_account_helper_fxt
    account_helper._authenticate_client(login="ab1782550dsd132", password='qwerty123')

    return account_helper


@pytest.fixture(scope='module')
def registered_auth_account_helper_fxt(mailhog_api_fxt, registered_user_data_fxt):

    login = registered_user_data_fxt.login
    password = registered_user_data_fxt.password
    email = registered_user_data_fxt.email
    
    dm_api_configuration = Configuration(host='http://185.185.143.231:5051', disable_log=False)
    account_api_client = DmApiAccount(dm_api_configuration)
    account_helper = AccountHelper(dm_account_api=account_api_client, mailhog_api=mailhog_api_fxt)
    
    account_helper.create_new_user(login=login, password=password, email=email)
    account_helper.register_a_user(login=login)
    account_helper._authenticate_client(login=login, password=password)

    # TODO: remove this user after tests?

    return account_helper


def _get_user_data():
    login = f'ab{int(time.time_ns())}'
    email = f"{login}@test.com"
    password = 'qwerty123'
    new_password = 'qwerty456'
    User = namedtuple('User', ['login', 'password', 'email', 'new_password'])
    user = User(login=login, email=email, password=password, new_password=new_password)
    
    return user
    