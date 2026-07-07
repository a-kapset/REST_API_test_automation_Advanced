from checkers.get_v1_account_checker import GetV1AccountChecker
from checkers.http_checkers import check_status_code_http


def test_get_v1_account_authenticated(account_helper_auth_existing_fxt):
    with check_status_code_http(expected_status_code=200):
        account_helper_auth_existing_fxt.get_user_info()


def test_get_v1_account_not_authenticated(account_helper_fxt):
    with check_status_code_http(expected_status_code=401, expected_message='User must be authenticated'):
        account_helper_fxt.get_user_info()


def test_get_v1_account_check_properties(account_helper_auth_existing_fxt):
    response = account_helper_auth_existing_fxt.get_user_info(validate_response=True)
    GetV1AccountChecker.check_response_values(response, login="ab1782550dsd132")
    GetV1AccountChecker.check_response_values_softly(response, login="ab1782550dsd132") # just example of soft assertions utilizing