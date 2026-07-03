from dm_api_account.models.login_credentials import LoginCredentials
from dm_api_account.models.user_envelope import UserEnvelope
from dm_api_account.models.bad_request_error import BadRequestError
from dm_api_account.models.problem_details import ProblemDetails
from restclient.client import RestClient


class LoginApi(RestClient):
            
    def post_v1_account_login(self, login_credentials: LoginCredentials, validate_response=True):
        """
        Authenticate via credentials

        Args:
            login_credentials

        Returns:
            _type_: Response
        """

        response = self.post(
            path="/v1/account/login",
            json=login_credentials.model_dump(exclude_none=True, by_alias=True)
        )

        # Validate against the model that matches the returned status code so that
        # error responses are validated too (not just 2xx). This lets tests keep
        # validate_response=True even on negative paths instead of silently
        # skipping validation. 403 uses ProblemDetails because that is the body
        # the server actually returns, even though swagger declares GeneralError.
        # TODO: think about other ways to implement such behavior (e.g. a
        #       status->model registry, or a generic response wrapper that
        #       resolves the model from the swagger spec automatically).
        if validate_response:
            if response.status_code == 200:
                return UserEnvelope(**response.json())
            if response.status_code == 400:
                return BadRequestError(**response.json())
            if response.status_code == 403:
                return ProblemDetails(**response.json())

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