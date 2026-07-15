import allure
from checkers.http_checkers import check_status_code_http
from helpers.account_helper import AccountHelper
from tests.user import User


@allure.suite("Tests for the method PUT v1/account/email")
@allure.sub_suite("Positive tests")
class TestsPutV1AccountEmail:
    @allure.title("Change email and re-activate the user")
    async def test_put_v1_account_email(self, account_helper_fxt: AccountHelper, user_data_fxt: User) -> None:
        account_helper = account_helper_fxt
        login = user_data_fxt.login
        email = user_data_fxt.email
        password = user_data_fxt.password
        changed_email = user_data_fxt.updated_email

        with check_status_code_http(expected_status_code=200):
            await account_helper.register_new_user(login=login, password=password, email=email)
            await account_helper.activate_user(login=login)
            await account_helper.user_login(login=login, password=password)
            await account_helper.change_email(login=login, password=password, email=changed_email)

        with check_status_code_http(
            expected_status_code=403,
            expected_message="User is inactive. Address the technical support for more details",
        ):
            await account_helper.user_login(login=login, password=password)

        with check_status_code_http(expected_status_code=200):
            await account_helper.activate_user(login=login)
            await account_helper.user_login(login=login, password=password)
