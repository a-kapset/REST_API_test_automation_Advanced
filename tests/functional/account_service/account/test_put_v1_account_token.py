import allure


@allure.suite("Tests for the method PUT v1/account/{token}")
@allure.sub_suite("Positive tests")
class TestsPutV1AccountToken:
    @allure.title("Register a new user and activate it via token")
    async def test_put_v1_account_token(self, account_helper_fxt, user_data_fxt):
        account_helper = account_helper_fxt
        login = user_data_fxt.login
        email = user_data_fxt.email
        password = user_data_fxt.password

        await account_helper.register_new_user(
            login=login, password=password, email=email
        )
        await account_helper.activate_user(login=login)
