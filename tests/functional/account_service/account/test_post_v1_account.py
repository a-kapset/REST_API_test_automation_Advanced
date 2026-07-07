import pytest
from checkers.http_checkers import check_status_code_http

def test_post_v1_account(account_helper_fxt, user_data_fxt):
    with check_status_code_http(expected_status_code=200):
        account_helper_fxt.register_new_user(
            login=user_data_fxt.login,
            password=user_data_fxt.password,
            email=user_data_fxt.email
        )
    

# def test_post_v1_account_invalid_password(account_helper_fxt, user_data_fxt):
#     with check_status_code_http(expected_status_code=400, expected_message='Validation failed'):
#         account_helper_fxt.register_new_user(
#             login=user_data_fxt.login,
#             password=user_data_fxt.password[0:5],
#             email=user_data_fxt.email
#         )

# def test_post_v1_account_invalid_email(account_helper_fxt, user_data_fxt):
#     with check_status_code_http(expected_status_code=400, expected_message='Validation failed'):
#         account_helper_fxt.register_new_user(
#             login=user_data_fxt.login,
#             password=user_data_fxt.password,
#             email=user_data_fxt.email.replace('@', '#')
#         )

# def test_post_v1_account_invalid_login(account_helper_fxt, user_data_fxt):
#     with check_status_code_http(expected_status_code=400, expected_message='Validation failed'):
#         account_helper_fxt.register_new_user(
#             login=user_data_fxt.login[0:1],
#             password=user_data_fxt.password,
#             email=user_data_fxt.email
#         )

@pytest.mark.parametrize(
    ('field', 'transformer'),
    [
        pytest.param('login', lambda v: v[0:1], id='invalid_login'),
        pytest.param('email', lambda v: v.replace('@', '#'), id='invalid_email'),
        pytest.param('password', lambda v: v[0:5], id='invalid_password')
    ]
)
def test_post_v1_account_invalid_creds(account_helper_fxt, user_data_fxt, field, transformer):
    credentials = {
        'login': user_data_fxt.login,
        'password': user_data_fxt.password,
        'email': user_data_fxt.email
    }
    
    credentials[field] = transformer(credentials[field])
    
    with check_status_code_http(expected_status_code=400, expected_message='Validation failed'):
        account_helper_fxt.register_new_user(**credentials)