from dm_api_account.models.user_details_envelope import UserDetailsEnvelope


def test_get_v1_account(account_helper_auth_existing_fxt):
    response = account_helper_auth_existing_fxt.get_user_info()
    UserDetailsEnvelope(**response.json())