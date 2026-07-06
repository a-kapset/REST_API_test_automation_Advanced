import allure


@allure.suite('Tests for the method DELETE v1/account/login/all')
@allure.sub_suite('Positive tests')
class TestsDeleteV1AccountLoginAll:

    @allure.title('Logout an authenticated user from all devices')
    def test_delete_v1_account_login_logout_all(self, account_helper_auth_new_fxt):
        account_helper_auth_new_fxt.user_logout_all()
