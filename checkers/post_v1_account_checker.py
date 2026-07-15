import allure
from datetime import datetime
from typing import Any
from hamcrest import (
    assert_that,
    has_property,
    has_properties,
    starts_with,
    all_of,
    instance_of,
    equal_to,
)


class PostV1AccountChecker:
    @classmethod
    def check_response_values(cls, response: Any, **kwargs: Any) -> None:
        with allure.step("Check response values"):
            today = datetime.now().strftime("%Y-%m-%d")
            assert_that(str(response.resource.registration), starts_with(today))

            assert_that(
                response,
                all_of(
                    has_property(
                        "resource",
                        has_property("login", starts_with(kwargs["login_starts_with"])),
                    ),
                    has_property("resource", has_property("registration", instance_of(datetime))),
                    has_property(
                        "resource",
                        has_properties(
                            {
                                "rating": has_properties(
                                    {
                                        "enabled": equal_to(kwargs["rating_is_enabled"]),
                                        "quality": equal_to(kwargs["rating_quality"]),
                                        "quantity": equal_to(kwargs["rating_quantity"]),
                                    }
                                )
                            }
                        ),
                    ),
                ),
            )
