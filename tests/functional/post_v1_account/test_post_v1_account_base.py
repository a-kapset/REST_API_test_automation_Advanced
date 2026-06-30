def test_post_v1_account_base(account_helper_fxt, new_user_data_fxt):
    login = new_user_data_fxt.login
    password = new_user_data_fxt.password
    email = new_user_data_fxt.email
    
    account_helper_fxt.create_new_user(login=login, password=password, email=email) 
    account_helper_fxt.register_a_user(login=login)
    account_helper_fxt.user_login(login=login, password=password, rememberMe=True)