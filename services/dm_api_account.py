from restclient.configuration import Configuration

from clients.http.dm_api_account.apis.account_api import AccountApi
from clients.http.dm_api_account.apis.login_api import LoginApi

# Facade implementation


class DmApiAccount:
    def __init__(self, configuration: Configuration) -> None:
        self.configuration = configuration
        self.account_api = AccountApi(configuration=self.configuration)
        self.login_api = LoginApi(configuration=self.configuration)
