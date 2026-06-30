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
    """Session-scoped MailHog API client, used to read activation emails."""
    
    mailhog_api_configuration = Configuration(host='http://185.185.143.231:5025', disable_log=True)
    mailhog_client = MailHogApi(mailhog_api_configuration)

    return mailhog_client


@pytest.fixture
def dm_account_api_fxt():
    """Returns a low-level DmApiAccount client for the account service API."""
    
    dm_api_configuration = Configuration(host='http://185.185.143.231:5051', disable_log=False)
    account_client = DmApiAccount(dm_api_configuration)

    return account_client


@pytest.fixture
def account_helper_fxt(dm_account_api_fxt, mailhog_api_fxt):
    """
    Returns an unauthenticated AccountHelper wrapping the account and MailHog
    clients. Use when the test drives user creation/registration/login itself.
    """
    
    account_helper = AccountHelper(dm_account_api=dm_account_api_fxt, mailhog_api=mailhog_api_fxt)

    return account_helper


@pytest.fixture()
def user_data_fxt():
    """
    Returns data for a single test user (see _get_user_data() for details).

    Function-scoped, so each test gets a unique user. Two usage patterns:

    - Paired with account_helper_fxt: the test drives user
      creation/registration itself using these values.
    - Paired with account_helper_auth_new_fxt: that fixture consumes this one
      internally to create, register, and authenticate the user. Request
      user_data_fxt in the same test to access that registered user's
      credentials (e.g. to log in again or change its password). Both share
      the same function-scoped instance, so the values match.
    """
    
    user = _get_user_data()

    return user


@pytest.fixture
def account_helper_auth_existing_fxt(mailhog_api_fxt):
    """
    Returns an AccountHelper authenticated as a pre-existing user.

    Builds its own DmApiAccount client and logs in with hardcoded credentials
    of a user that must already exist on the server. It does NOT create or
    register a user. Use when a test just needs an authenticated client and
    doesn't care about the specific account.
    """

    dm_api_configuration = Configuration(host='http://185.185.143.231:5051', disable_log=False)
    account_api_client = DmApiAccount(dm_api_configuration)
    account_helper = AccountHelper(dm_account_api=account_api_client, mailhog_api=mailhog_api_fxt)

    # TODO: replace hardcoded values with more flexible logic,
    # or remove this fixture since there is account_helper_auth_new_fxt
    account_helper.authenticate_client(login="ab1782550dsd132", password='qwerty123')

    return account_helper


@pytest.fixture()
def account_helper_auth_new_fxt(mailhog_api_fxt, user_data_fxt):
    """
    Returns an AccountHelper authenticated as a fresh, per-test user.

    Takes the credentials from user_data_fxt, then on the server: creates the
    user, confirms registration (via the activation email), and logs in.
    The returned helper is ready to make authenticated requests.

    Request user_data_fxt alongside this fixture in a test to access the same
    user's credentials (both share one function-scoped instance).
    """

    login = user_data_fxt.login
    password = user_data_fxt.password
    email = user_data_fxt.email
    
    dm_api_configuration = Configuration(host='http://185.185.143.231:5051', disable_log=False)
    account_api_client = DmApiAccount(dm_api_configuration)
    account_helper = AccountHelper(dm_account_api=account_api_client, mailhog_api=mailhog_api_fxt)
    
    account_helper.create_new_user(login=login, password=password, email=email)
    account_helper.register_a_user(login=login)
    account_helper.authenticate_client(login=login, password=password)

    # TODO: remove this user after tests?

    return account_helper


def _get_user_data():
    login = f'ab{int(time.time_ns())}'
    email = f"{login}@test.com"
    updated_email = f"upd_{login}@test.com"
    password = 'qwerty123'
    new_password = 'qwerty456'

    User = namedtuple(
        'User',
        ['login', 'email', 'updated_email', 'password','new_password']
    )

    user = User(
        login=login,
        email=email,
        updated_email=updated_email,
        password=password,
        new_password=new_password        
    )
    
    return user
    