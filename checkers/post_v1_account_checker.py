from datetime import datetime

import allure
from hamcrest import (
    all_of,
    assert_that,
    equal_to,
    has_properties,
    has_property,
    instance_of,
    starts_with,
)

from clients.http.dm_api_account.models.api_models import UserEnvelope


class PostV1AccountChecker:
    @classmethod
    def check_response_values(
        cls,
        response: UserEnvelope,
        login_starts_with: str,
        rating_is_enabled: bool,
        rating_quality: int,
        rating_quantity: int,
    ) -> None:
        with allure.step("Check response values"):
            assert response.resource is not None, "Response carries no resource to check"

            today = datetime.now().strftime("%Y-%m-%d")
            assert_that(str(response.resource.registration), starts_with(today))

            assert_that(
                response,
                all_of(
                    has_property(
                        "resource",
                        has_property("login", starts_with(login_starts_with)),
                    ),
                    has_property("resource", has_property("registration", instance_of(datetime))),
                    has_property(
                        "resource",
                        has_properties(
                            {
                                "rating": has_properties(
                                    {
                                        "enabled": equal_to(rating_is_enabled),
                                        "quality": equal_to(rating_quality),
                                        "quantity": equal_to(rating_quantity),
                                    }
                                )
                            }
                        ),
                    ),
                ),
            )
