def test_post_v1_login(account_helper_fxt, user_data_fxt):
    login = user_data_fxt.login
    password = user_data_fxt.password
    email = user_data_fxt.email

    account_helper_fxt.register_new_user(login=login, password=password, email=email)
    account_helper_fxt.activate_user(login=login)
    account_helper_fxt.user_login(login=login, password=password, remember_me=True)
    