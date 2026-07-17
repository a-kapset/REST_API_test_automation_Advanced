from restclient.client import RestClient
from restclient.configuration import Configuration

from clients.http.dm_api_account.apis.account_api import AccountApi
from clients.http.dm_api_account.apis.login_api import LoginApi

# Facade implementation


class DmApiAccount:
    def __init__(self, configuration: Configuration) -> None:
        self.configuration = configuration
        self.api_client = RestClient(configuration)
        self.account_api = AccountApi(api_client=self.api_client)
        self.login_api = LoginApi(api_client=self.api_client)
