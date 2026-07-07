import allure
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
from assertpy import soft_assertions, assert_that


class GetV1AccountChecker:

    @classmethod
    def check_response_values(cls, response, **kwargs):
        with allure.step("Check response values"):
            assert_that(
                response, all_of(
                    has_property('resource', not_none()),
                    has_property('resource', has_property('login', equal_to(kwargs['login']))),
                    has_property('resource', has_property('roles', has_item(equal_to(UserRole.PLAYER)))),            
                    has_property('resource', has_property('registration', instance_of(datetime))),            
                    has_property('resource', has_property('rating', has_properties({
                        'enabled': instance_of(bool),
                        'quality': instance_of(int),
                        'quantity': instance_of(int),
                    }))),
                )
            )
    
    @classmethod
    def check_response_values_softly(cls, response, **kwargs):
        with allure.step("Check response values softly"):
            with soft_assertions():
                assert_that(response.resource.login).is_equal_to(kwargs['login'])
                assert_that(response.resource.online).is_instance_of(datetime)
                assert_that(response.resource.roles).contains(UserRole.GUEST, UserRole.PLAYER)
