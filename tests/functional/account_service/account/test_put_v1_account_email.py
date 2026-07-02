from dm_api_account.models.user_envelope import UserEnvelope


def test_put_v1_account_email(account_helper_fxt, user_data_fxt):
    account_helper = account_helper_fxt
    login = user_data_fxt.login
    email = user_data_fxt.email
    password = user_data_fxt.password
    changed_email = user_data_fxt.updated_email

    account_helper.register_new_user(login=login, password=password, email=email)
    account_helper.activate_user(login=login)
    account_helper.user_login(login=login, password=password)
    response = account_helper.change_email(login=login, password=password, email=changed_email)
    UserEnvelope(**response.json())
    # After the email change the account is deactivated, so login is rejected (403).
    account_helper.user_login(login=login, password=password, status_code=403)
    account_helper.activate_user(login=login)
    account_helper.user_login(login=login, password=password)