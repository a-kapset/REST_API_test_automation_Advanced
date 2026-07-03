from contextlib import contextmanager
from requests.exceptions import HTTPError
from requests import codes


@contextmanager
def check_status_code_http(
    expected_status_code: codes = codes.OK,
    expected_message: str = ''
):
    try:
        yield
        
        if expected_status_code != codes.OK:
            raise AssertionError(f"Status code '{expected_status_code}' should be recieved, but actual is '{codes.OK}'")
        
        if expected_message:
            raise AssertionError(f"Message '{expected_message}' should be recieved")
        
    except HTTPError as err:
        assert err.response.status_code == expected_status_code, \
            f"Expected status code is {expected_status_code}, but actual is {err.response.status_code}"
            
        assert err.response.json()['title'] == expected_message, \
            f"Expected message is '{expected_message}', but actual is '{err.response.json()['title']}'"