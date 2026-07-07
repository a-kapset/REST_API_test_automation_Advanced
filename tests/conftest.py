import os
import time
import pytest
import structlog
from collections import namedtuple
from pathlib import Path
from vyper import v
from swagger_coverage_py.reporter import CoverageReporter
from helpers.account_helper import AccountHelper
from restclient.configuration import Configuration
from services.dm_api_account import DmApiAccount
from services.api_mailhog import MailHogApi

structlog.configure(
    processors=[
        structlog.processors.JSONRenderer(indent=4, ensure_ascii=True, sort_keys=True)
    ]
)


options = (
    'service.dm_api_account',
    'service.mailhog',
    'user.login',
    'user.password',
    'user.new_password'
)


@pytest.fixture(scope='session', autouse=True)
def set_config(request):
    """
    Loads config for the environment given by --env and layers CLI overrides.

    Reads the matching config file from the config/ directory into Vyper, then
    overrides each option with its --<option> command-line value when provided.
    Session-scoped and autouse, so it runs once before any test.
    """

    config = Path(__file__).joinpath('../../').joinpath('config')
    config_name = request.config.getoption('--env')
    v.set_config_name(config_name)
    v.add_config_path(config)
    v.read_in_config()
    
    for option in options:
        v.set(f"{option}", request.config.getoption(f"--{option}"))
    

def pytest_addoption(parser):
    """
    Registers custom pytest CLI options.

    Adds --env to pick the config environment (default 'stg') plus one
    --<option> for each entry in `options`, allowing config values to be
    overridden from the command line.
    """

    parser.addoption('--env', action='store', default='stg', help='run stg')

    parser.addoption(
        '--swagger-coverage',
        action='store_true',
        default=False,
        help='Collect requests and generate a swagger coverage report. '
             'Requires a Java runtime and a filesystem that allows ":" in '
             'paths (i.e. run in Docker via Dockerfile-sw-coverage, not on Windows).'
    )

    for option in options:
        parser.addoption(f"--{option}", action='store', default=None)


def pytest_configure(config):
    """
    Exposes the --swagger-coverage flag to the RestClient via an env var so it
    only records requests (which creates the swagger-coverage-output directory)
    when the report is actually wanted. Read at request time, so setting it here
    is early enough.
    """

    os.environ['SWAGGER_COVERAGE_ENABLED'] = (
        '1' if config.getoption('--swagger-coverage') else '0'
    )


@pytest.fixture(scope="session", autouse=True)
def setup_swagger_coverage(request):
    """
    Session-scoped swagger coverage reporter, enabled only with --swagger-coverage.

    When the flag is absent (the default), this fixture is a no-op so tests run
    anywhere, including Windows. When enabled, it sets up the reporter before the
    session and generates the HTML report afterwards.
    """

    if not request.config.getoption('--swagger-coverage'):
        yield
        return

    reporter = CoverageReporter(api_name="dm-api-reporter", host="http://185.185.143.231:5051")
    reporter.cleanup_input_files()
    reporter.setup("/swagger/Account/swagger.json")
    yield
    reporter.generate_report()


@pytest.fixture(scope='session')
def mailhog_api_fxt():
    """Session-scoped MailHog API client, used to read activation emails."""
    
    mailhog_api_configuration = Configuration(host=v.get('service.mailhog'), disable_log=True)
    mailhog_client = MailHogApi(mailhog_api_configuration)

    return mailhog_client


@pytest.fixture
def dm_account_api_fxt():
    """Returns a low-level DmApiAccount client for the account service API."""
    
    dm_api_configuration = Configuration(host=v.get('service.dm_api_account'), disable_log=False)
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

    dm_api_configuration = Configuration(host=v.get('service.dm_api_account'), disable_log=False)
    account_api_client = DmApiAccount(dm_api_configuration)
    account_helper = AccountHelper(dm_account_api=account_api_client, mailhog_api=mailhog_api_fxt)
    account_helper.authenticate_client(login=v.get('user.login'), password=v.get('user.password'))

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
    
    dm_api_configuration = Configuration(host=v.get('service.dm_api_account'), disable_log=False)
    account_api_client = DmApiAccount(dm_api_configuration)
    account_helper = AccountHelper(dm_account_api=account_api_client, mailhog_api=mailhog_api_fxt)
    
    account_helper.register_new_user(login=login, password=password, email=email)
    account_helper.activate_user(login=login)
    account_helper.authenticate_client(login=login, password=password)

    # TODO: remove this user after tests?

    return account_helper


def _get_user_data():
    login = f'ab{int(time.time_ns())}'
    email = f"{login}@test.com"
    updated_email = f"upd_{login}@test.com"
    password = v.get('user.password')
    new_password = v.get('user.new_password')

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
    