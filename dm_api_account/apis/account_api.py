from dm_api_account.models.registration import Registration
from restclient.client import RestClient

class AccountApi(RestClient):
        
    def post_v1_account(self, registration: Registration):
        """
        Register new user

        Args:
            json_data

        Returns:
            _type_: Response
        """
        
        response = self.post(
            path="/v1/account",
            json=registration.model_dump(exclude_none=True, by_alias=True)
        )
        
        return response
    
    
    def put_v1_account_token(self, token):
        """
        Activate registered user

        Args:
            token

        Returns:
            _type_: Response
        """
        
        headers = {
            "accept": "text/plain"
        }
        
        response = self.put(
            path=f"/v1/account/{token}",
            headers=headers
        )
        
        return response
    
    
    def put_v1_account_email(self, json_data):
        """
        Change registered user email

        Args:
            json_data

        Returns:
            _type_: Response
        """
        
        response = self.put(
            path="/v1/account/email",
            json=json_data
        )

        return response
    
    
    def get_v1_account(self, **kwargs):
        """
        Get current user

        Args:
            **kwargs

        Returns:
            _type_: Response
        """
        
        response = self.get(
            path="/v1/account",
            **kwargs
        )
        
        return response
    

    def post_v1_account_password(self, json_data):
        """
        Reset registered user password

        Args:
            json_data

        Returns:
            _type_: Response
        """
        
        response = self.post(
            path="/v1/account/password",
            json=json_data
        )
        
        return response
    

    def put_v1_account_password(self, json_data):
        """
        Change registered user password

        Args:
            json_data

        Returns:
            _type_: Response
        """
        
        response = self.put(
            path="/v1/account/password",
            json=json_data
        )
        
        return response    