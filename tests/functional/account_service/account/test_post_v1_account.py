def test_post_v1_account(account_helper_fxt, user_data_fxt):

    account_helper_fxt.create_new_user(
        login=user_data_fxt.login,
        password=user_data_fxt.password,
        email=user_data_fxt.email
    )