from restclient.client import RestClient


class MailhogApi(RestClient):
    def get_api_v2_messages(self, limit=50):
        """
        Get users emails
        
        Args:
            limit

        Returns:
            _type_: Response
        """
        
        params = {
            'limit': limit,
        }

        response = self.get(
            path="/api/v2/messages",
            params=params,
            verify=False
        )
        
        return response