from clients.http.dm_api_account.apis.account_api import AccountApi
from clients.http.dm_api_account.apis.login_api import LoginApi
from clients.http.rest_client.client_async import Configuration, ApiClient

# Facade implementation


class DmApiAccount:
    def __init__(self, configuration: Configuration):
        self.configuration = configuration
        self.api_client = ApiClient(configuration=self.configuration)
        self.account_api = AccountApi(self.api_client)
        self.login_api = LoginApi(self.api_client)
