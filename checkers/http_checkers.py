import allure
from contextlib import contextmanager
from json import JSONDecodeError

import httpx
from httpx import codes


# Implemented as a context manager rather than a helper that calls the API itself:
#   - Readability: the `with` block clearly wraps the code under check.
#   - Reuse: works with ANY client method, not one hard-coded call.
#   - Single responsibility: only validates the result; the test decides what to call.
#
# TODO: allow checking the exact status code inside the block. The success branch
#       currently only knows the request returned some 2xx (no HTTPError), so
#       "expected 200, got 201/204" is not caught. Idea: yield a holder the test
#       assigns the response to, then assert response.status_code == expected.
@contextmanager
def check_status_code_http(
    expected_status_code=codes.OK,
    expected_message: str = ''
):
    with allure.step("Check response values"):
        try:
            yield

            # No HTTPError means the request succeeded with some 2xx status.
            # If we expected an error (non-2xx), the request unexpectedly passed - fail.
            if expected_status_code not in range(200, 300):
                raise AssertionError(f"Status code '{expected_status_code}' was expected, but the request succeeded with a 2xx status")

            if expected_message:
                raise AssertionError(f"Message '{expected_message}' should be received")

        except httpx.HTTPStatusError as err:
            response = err.response
            assert response is not None, "HTTPStatusError raised without a response"

            assert response.status_code == expected_status_code, \
                f"Expected status code is {expected_status_code}, but actual is {response.status_code}"

            try:
                actual_message = response.json().get('title', '')
            except JSONDecodeError:
                actual_message = ''
            assert actual_message == expected_message, \
                f"Expected message is '{expected_message}', but actual is '{actual_message}'"
