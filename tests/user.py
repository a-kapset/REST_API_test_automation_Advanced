from typing import NamedTuple


class User(NamedTuple):
    """Credentials for a single test user."""

    login: str
    email: str
    updated_email: str
    password: str
    new_password: str
