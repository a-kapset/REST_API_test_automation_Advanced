import allure
from checkers.get_v1_account_checker import GetV1AccountChecker
from checkers.http_checkers import check_status_code_http


@allure.suite("Tests for the method GET v1/account")
@allure.sub_suite("Positive tests")
class TestsGetV1AccountPositive:
    @allure.title("Get account info when client is authenticated")
    async def test_get_v1_account_authenticated(self, account_helper_auth_existing_fxt):
        with check_status_code_http(expected_status_code=200):
            await account_helper_auth_existing_fxt.get_user_info()

    @allure.title(
        "Get account info when client is autheticated and check response properties"
    )
    async def test_get_v1_account_check_properties(
        self, account_helper_auth_existing_fxt
    ):
        response = await account_helper_auth_existing_fxt.get_user_info()
        GetV1AccountChecker.check_response_values(response, login="ab1782550dsd132")
        GetV1AccountChecker.check_response_values_softly(
            response, login="ab1782550dsd132"
        )  # just example of soft assertions utilizing


@allure.suite("Tests for the method GET v1/account")
@allure.sub_suite("Negative tests")
class TestsGetV1AccountNegative:
    @allure.title("Get account info when client is not authenticated")
    async def test_get_v1_account_not_authenticated(self, account_helper_fxt):
        with check_status_code_http(
            expected_status_code=401, expected_message="User must be authenticated"
        ):
            await account_helper_fxt.get_user_info()
