"""Runtime async client for the restcodegen-generated API clients.

restcodegen is a code generator: it emits the typed API classes (``AccountApi``,
``LoginApi``) and the pydantic models, but does NOT ship a runtime client. Per
its README you pass your own ``httpx.AsyncClient`` (with ``base_url`` set) to the
generated API classes.

``ApiClient`` is that client. It is a thin ``httpx.AsyncClient`` subclass that
adds only what this framework needs on top of plain httpx:

- ``raise_for_status()`` on every response, so non-2xx surfaces as
  ``httpx.HTTPStatusError`` — the whole test suite's ``check_status_code_http``
  checker relies on that.
- ``set_headers()`` to persist the auth token across requests (see
  ``AccountHelper.authenticate_client``).
"""

from typing import Any

import httpx

# Re-exported so the generated services can import Configuration and ApiClient
# from one module (restcodegen ships neither).
from restclient.configuration import Configuration

__all__ = ["ApiClient", "Configuration"]


class ApiClient(httpx.AsyncClient):
    def __init__(self, configuration: Configuration) -> None:
        super().__init__(
            base_url=configuration.host,
            verify=configuration.verify,
            headers=configuration.headers or {},
        )
        self.configuration = configuration

    def set_headers(self, headers: dict | None) -> None:
        """Persist headers (e.g. the auth token) on every subsequent request."""

        if headers:
            self.headers.update(headers)

    async def request(self, method: str, url: Any, **kwargs: Any) -> httpx.Response:
        # Drop headers the generated code emits with the literal value "None":
        # it stringifies unset optional header params (e.g. x_dm_bb_render_mode)
        # before filtering, so "None" would otherwise be sent on every request.
        headers = kwargs.get("headers")
        if headers:
            kwargs["headers"] = {k: v for k, v in headers.items() if v != "None"}

        response = await super().request(method, url, **kwargs)
        # Raise on non-2xx so callers/checkers see httpx.HTTPStatusError.
        response.raise_for_status()

        return response
