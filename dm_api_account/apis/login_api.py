from dm_api_account.models.login_credentials import LoginCredentials
from dm_api_account.models.user_envelope import UserEnvelope
from restclient.client import RestClient


class LoginApi(RestClient):
            
    def post_v1_account_login(self, login_credentials: LoginCredentials, validate_response=True):
        """
        Authenticate via credentials

        Args:
            json_data

        Returns:
            _type_: Response
        """

        response = self.post(
            path="/v1/account/login",
            json=login_credentials.model_dump(exclude=None, by_alias=True)
        )

        # UserEnvelope is only the success (2xx) response shape per swagger;
        # error responses (400/403) use BadRequestError/GeneralError, so callers
        # expecting an error must pass validate_response=False.
        if validate_response:
            return UserEnvelope(**response.json())

        return response
    

    def delete_v1_account_login(self, **kwargs):
        """
        Logout as current user

        Returns:
            _type_: Response
        """

        response = self.delete(
            path="/v1/account/login",
            **kwargs
        )
        
        return response
    
    
    def delete_v1_account_login_all(self, **kwargs):
        """
        Logout from every device

        Returns:
            _type_: Response
        """

        response = self.delete(
            path="/v1/account/login/all",
            **kwargs
        )
        
        return response  