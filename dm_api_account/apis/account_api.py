from dm_api_account.models.registration import Registration
from dm_api_account.models.user_envelope import UserEnvelope
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
    
    
    def put_v1_account_token(self, token, validate_response=True):
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

        if validate_response:
            return UserEnvelope(**response.json())

        return response
    
    
    def put_v1_account_email(self, json_data, validate_response=True):
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

        if validate_response:
            return UserEnvelope(**response.json())

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
    

    def post_v1_account_password(self, json_data, validate_response=True):
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

        if validate_response:
            return UserEnvelope(**response.json())

        return response
    

    def put_v1_account_password(self, json_data, validate_response=True):
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

        if validate_response:
            return UserEnvelope(**response.json())

        return response