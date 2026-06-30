def test_post_v1_account(account_helper_fxt, new_user_data_fxt):

    account_helper_fxt.create_new_user(
        login=new_user_data_fxt.login,
        password=new_user_data_fxt.password,
        email=new_user_data_fxt.email
    )