from clients.http.api_mailhog.apis.mailhog_api import MailhogApi
from packages.restclient.configuration import Configuration

# Facade implementation


class MailHogApi:
    def __init__(self, configuration: Configuration) -> None:
        self.configuration = configuration
        self.mailhog_api = MailhogApi(configuration=self.configuration)
