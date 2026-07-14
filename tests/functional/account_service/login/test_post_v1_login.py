import allure
from helpers.account_helper import AccountHelper
from tests.user import User


@allure.suite("Tests for the method POST v1/account/login")
@allure.sub_suite("Positive tests")
class TestsPostV1Login:
    @allure.title("Login with a registered and activated user")
    async def test_post_v1_login(self, account_helper_fxt: AccountHelper, user_data_fxt: User) -> None:
        login = user_data_fxt.login
        password = user_data_fxt.password
        email = user_data_fxt.email

        await account_helper_fxt.register_new_user(login=login, password=password, email=email)
        await account_helper_fxt.activate_user(login=login)
        await account_helper_fxt.user_login(login=login, password=password, remember_me=True)
