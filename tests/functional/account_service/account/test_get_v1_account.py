from datetime import datetime
from hamcrest import (
    assert_that,
    all_of,
    has_property,
    has_properties,
    has_item,
    instance_of,
    equal_to,
    not_none,
)
from dm_api_account.models.user_envelope import UserRole
from checkers.http_checkers import check_status_code_http
from assertpy import soft_assertions, assert_that


def test_get_v1_account_authenticated(account_helper_auth_existing_fxt):
    response = account_helper_auth_existing_fxt.get_user_info()
    
    with soft_assertions():
        assert_that(response.resource.login).is_equal_to('ab1782550dsd132')
        assert_that(response.resource.online).is_instance_of(datetime)
        assert_that(response.resource.roles).contains(UserRole.GUEST, UserRole.PLAYER)


def test_get_v1_account_not_authenticated(account_helper_fxt):
    with check_status_code_http(expected_status_code=401, expected_message='User must be authenticated'):
        account_helper_fxt.get_user_info()


def test_get_v1_account_check_properties(account_helper_auth_existing_fxt):
    response = account_helper_auth_existing_fxt.get_user_info(validate_response=True)

    assert_that(
        response, all_of(
            has_property('resource', not_none()),
            has_property('resource', has_property('login', equal_to('ab1782550dsd132'))),
            has_property('resource', has_property('roles', has_item(equal_to(UserRole.PLAYER)))),            
            has_property('resource', has_property('registration', instance_of(datetime))),            
            has_property('resource', has_property('rating', has_properties({
                'enabled': instance_of(bool),
                'quality': instance_of(int),
                'quantity': instance_of(int),
            }))),
        )
    )