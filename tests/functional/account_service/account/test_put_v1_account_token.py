def test_put_v1_account_token(account_helper_fxt, new_user_data_fxt):
    account_helper = account_helper_fxt
    login = new_user_data_fxt.login
    email = new_user_data_fxt.email
    password = new_user_data_fxt.password
    
    account_helper.create_new_user(login=login, password=password, email=email)
    account_helper.register_a_user(login=login)