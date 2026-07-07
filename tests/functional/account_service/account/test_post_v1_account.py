import allure
import pytest
from checkers.http_checkers import check_status_code_http


@allure.suite('Tests for the method POST v1/account')
@allure.sub_suite('Positive tests')
class TestsPostV1AccountPositive:

    @allure.title('Register a new user')
    def test_post_v1_account(self, account_helper_fxt, user_data_fxt):
        with check_status_code_http(expected_status_code=200):
            account_helper_fxt.register_new_user(
                login=user_data_fxt.login,
                password=user_data_fxt.password,
                email=user_data_fxt.email
            )


@allure.suite('Tests for the method POST v1/account')
@allure.sub_suite('Negative tests')
class TestsPostV1AccountNegative:

    @allure.title('Register a new user with invalid credentials')
    @pytest.mark.parametrize(
        ('field', 'transformer'),
        
        # TODO: consider to simplify parameters without lambdas to improve test readability
        [
            pytest.param('login', lambda v: v[0:1], id='invalid_login'),
            pytest.param('email', lambda v: v.replace('@', '#'), id='invalid_email'),
            pytest.param('password', lambda v: v[0:5], id='invalid_password')
        ]
    )
    def test_post_v1_account_invalid_creds(self, account_helper_fxt, user_data_fxt, field, transformer):
        credentials = {
            'login': user_data_fxt.login,
            'password': user_data_fxt.password,
            'email': user_data_fxt.email
        }

        credentials[field] = transformer(credentials[field])

        with check_status_code_http(expected_status_code=400, expected_message='Validation failed'):
            account_helper_fxt.register_new_user(**credentials)
