def test_get_v1_account(registered_auth_account_helper_fxt):
    account_api = registered_auth_account_helper_fxt
    account_api.get_user_info()