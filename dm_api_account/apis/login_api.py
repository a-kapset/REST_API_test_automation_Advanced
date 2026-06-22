from restclient.client import RestClient


class LoginApi(RestClient):
            
    def post_v1_account_login(self, json_data):
        """
        Authenticate via credentials

        Args:
            json_data

        Returns:
            _type_: Response
        """

        response = self.post(
            path="/v1/account/login",
            json=json_data
        )
        
        return response