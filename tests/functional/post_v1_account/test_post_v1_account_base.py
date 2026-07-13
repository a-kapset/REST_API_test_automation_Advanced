import allure
from checkers.post_v1_account_checker import PostV1AccountChecker


@allure.suite('Tests for the method POST v1/account')
@allure.sub_suite('Positive tests')
class TestsPostV1Account_BaseTest:

    @allure.title('Check new user registration')
    async def test_post_v1_account_base(self, account_helper_fxt, user_data_fxt):
        login = user_data_fxt.login
        password = user_data_fxt.password
        email = user_data_fxt.email

        await account_helper_fxt.register_new_user(login=login, password=password, email=email)
        await account_helper_fxt.activate_user(login=login)
        response = await account_helper_fxt.user_login(login=login, password=password, remember_me=True, validate_response=True)
        
        PostV1AccountChecker.check_response_values(
            response=response,
            login_starts_with='ab',
            rating_is_enabled=True,
            rating_quality=0,
            rating_quantity=0
        )
    
    