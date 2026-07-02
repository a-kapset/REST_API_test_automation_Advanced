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


def test_get_v1_account(account_helper_auth_existing_fxt):
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
