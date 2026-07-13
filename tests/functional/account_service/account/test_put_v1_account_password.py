import allure


@allure.suite('Tests for the method PUT v1/account/password')
@allure.sub_suite('Positive tests')
class TestsPutV1AccountPassword:

    @allure.title('Change password and login with the new password')
    async def test_put_v1_account_password(
            self,
            account_helper_auth_new_fxt,
            user_data_fxt
    ):
        account_api = account_helper_auth_new_fxt
        user_data = user_data_fxt

        await account_api.change_password(
            login=user_data.login,
            email=user_data.email,
            old_password=user_data.password,
            new_password=user_data.new_password
        )

        await account_api.user_login(
            login=user_data.login,
            password=user_data.new_password
        )
