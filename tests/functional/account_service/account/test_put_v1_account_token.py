def test_put_v1_account_token(account_helper_fxt, user_data_fxt):
    account_helper = account_helper_fxt
    login = user_data_fxt.login
    email = user_data_fxt.email
    password = user_data_fxt.password

    account_helper.register_new_user(login=login, password=password, email=email)
    account_helper.activate_user(login=login)