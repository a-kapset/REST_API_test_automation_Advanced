def test_put_v1_account_password(
        registered_auth_account_helper_fxt,
        registered_user_data_fxt
):
    account_api = registered_auth_account_helper_fxt
    user_data = registered_user_data_fxt

    account_api.change_password(
        login=user_data.login,
        email=user_data.email,
        old_password=user_data.password,
        new_password=user_data.new_password
    )

    account_api.user_login(
        login=user_data.login,
        password=user_data.new_password
    )