from packages.restclient.configuration import Configuration
from clients.http.api_mailhog.apis.mailhog_api import MailhogApi

# Facade implementation

class MailHogApi:
    def __init__(self, configuration: Configuration):
        self.configuration = configuration
        self.mailhog_api = MailhogApi(configuration=self.configuration)