def test_put_v1_account_password(
        account_helper_auth_new_fxt,
        user_data_fxt
):
    account_api = account_helper_auth_new_fxt
    user_data = user_data_fxt

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
    