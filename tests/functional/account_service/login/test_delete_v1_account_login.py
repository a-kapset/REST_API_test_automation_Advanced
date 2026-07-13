import allure


@allure.suite('Tests for the method DELETE v1/account/login')
@allure.sub_suite('Positive tests')
class TestsDeleteV1AccountLogin:

    @allure.title('Logout an authenticated user')
    async def test_delete_v1_account_login_logout(self, account_helper_auth_new_fxt):
        await account_helper_auth_new_fxt.user_logout()
