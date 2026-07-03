from datetime import datetime
from hamcrest import (
    assert_that,
    has_property,
    has_properties,
    starts_with,
    all_of,
    instance_of,
    equal_to
)


def test_post_v1_account_base(account_helper_fxt, user_data_fxt):
    login = user_data_fxt.login
    password = user_data_fxt.password
    email = user_data_fxt.email

    account_helper_fxt.register_new_user(login=login, password=password, email=email)
    account_helper_fxt.activate_user(login=login)
    response = account_helper_fxt.user_login(login=login, password=password, remember_me=True, validate_response=True)

    assert_that(
        response, all_of(
            has_property('resource', has_property('login', starts_with('ab'))),
            has_property('resource', has_property('registration', instance_of(datetime))),
            has_property('resource', has_properties({
                        'rating': has_properties(
                            {
                                'enabled': equal_to(True),
                                'quality': equal_to(0),
                                'quantity': equal_to(0)
                            }
                        )
                    }
                )
            )
        )
    )
