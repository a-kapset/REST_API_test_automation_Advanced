from datetime import datetime

import allure
from assertpy import assert_that as assert_that_fluent
from assertpy import soft_assertions
from hamcrest import (
    all_of,
    assert_that,
    equal_to,
    has_item,
    has_properties,
    has_property,
    instance_of,
    not_none,
)

from clients.http.dm_api_account.models.api_models import UserDetailsEnvelope, UserRole


class GetV1AccountChecker:
    @classmethod
    def check_response_values(cls, response: UserDetailsEnvelope, login: str) -> None:
        with allure.step("Check response values"):
            assert_that(
                response,
                all_of(
                    has_property("resource", not_none()),
                    has_property("resource", has_property("login", equal_to(login))),
                    has_property(
                        "resource",
                        has_property("roles", has_item(equal_to(UserRole.PLAYER))),
                    ),
                    has_property("resource", has_property("registration", instance_of(datetime))),
                    has_property(
                        "resource",
                        has_property(
                            "rating",
                            has_properties(
                                {
                                    "enabled": instance_of(bool),
                                    "quality": instance_of(int),
                                    "quantity": instance_of(int),
                                }
                            ),
                        ),
                    ),
                ),
            )

    @classmethod
    def check_response_values_softly(cls, response: UserDetailsEnvelope, login: str) -> None:
        with allure.step("Check response values softly"):
            assert response.resource is not None, "Response carries no resource to check"

            with soft_assertions():
                assert_that_fluent(response.resource.login).is_equal_to(login)
                assert_that_fluent(response.resource.online).is_instance_of(datetime)
                assert_that_fluent(response.resource.roles).contains(UserRole.GUEST, UserRole.PLAYER)
