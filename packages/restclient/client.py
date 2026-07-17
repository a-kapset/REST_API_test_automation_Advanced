import asyncio
import os
import uuid
from collections.abc import Mapping
from json import JSONDecodeError
from typing import Any, TypedDict, Unpack

import curlify2
import httpx
import structlog
from swagger_coverage_py.listener import URI, RequestSchemaHandler

from packages.restclient.configuration import Configuration
from packages.restclient.utilities import allure_attach

# JsonBody stays dict[str, Any] on purpose: a JSON body is arbitrary by nature, and
# this is what pydantic's model_dump(by_alias=True, exclude_none=True) returns. The
# Any is confined to the values inside the body, not to the whole signature.
type JsonBody = dict[str, Any]
type Headers = Mapping[str, str]
type QueryParams = Mapping[str, str | int]


class RequestOptions(TypedDict, total=False):
    """The httpx request options this client forwards.

    Typed **kwargs (PEP 692). This keeps the passthrough flexibility of plain
    **kwargs — callers still write `post(path, json=..., timeout=5)`, and adding
    another httpx option is a one-line change here rather than a new parameter on
    four methods — but unlike `**kwargs: Any` the key names and value types are
    checked, so a misspelled `headrs=` is an error instead of being silently
    dropped on the floor.
    """

    json: JsonBody | None
    params: QueryParams | None
    headers: Headers | None
    # dict, not Mapping: httpx's CookieTypes is invariant here and rejects a
    # plain Mapping. mypy checks these against httpx's real signature, so a wrong
    # type is caught at the TypedDict rather than at the request.
    cookies: dict[str, str] | None
    content: str | bytes | None
    timeout: float
    follow_redirects: bool


# Proxy implementation


class RestClient:
    def __init__(self, configuration: Configuration) -> None:
        self.session = httpx.AsyncClient(verify=configuration.verify)
        self.host = configuration.host
        self.set_headers(configuration.headers)
        self.disable_log = configuration.disable_log
        self.log = structlog.get_logger(__name__).bind(service="api")  # __name__ - logger will have currnet class name
        # service='api' - logger is for 'api' service
        # ...

    def set_headers(self, headers: Mapping[str, str] | None) -> None:
        if headers:
            self.session.headers.update(headers)

    async def post(self, path: str, **kwargs: Unpack[RequestOptions]) -> httpx.Response:
        return await self._send_request(method="POST", path=path, **kwargs)

    async def get(self, path: str, **kwargs: Unpack[RequestOptions]) -> httpx.Response:
        return await self._send_request(method="GET", path=path, **kwargs)

    async def put(self, path: str, **kwargs: Unpack[RequestOptions]) -> httpx.Response:
        return await self._send_request(method="PUT", path=path, **kwargs)

    async def delete(self, path: str, **kwargs: Unpack[RequestOptions]) -> httpx.Response:
        return await self._send_request(method="DELETE", path=path, **kwargs)

    @allure_attach
    async def _send_request(self, method: str, path: str, **kwargs: Unpack[RequestOptions]) -> httpx.Response:
        log = self.log.bind(event_id=str(uuid.uuid4()))
        full_url = self.host + path

        if self.disable_log:
            rest_response = await self.session.request(method=method, url=full_url, **kwargs)
            rest_response.raise_for_status()  # Raises HTTPError, if one occurred (status != 2xx)

            return rest_response

        log.msg(
            event="Request",
            method=method,
            full_url=full_url,
            params=kwargs.get("params"),
            headers=kwargs.get("headers"),
            json=kwargs.get("json"),
        )

        rest_response = await self.session.request(method=method, url=full_url, **kwargs)
        curl = curlify2.Curlify(rest_response.request).to_curl()  # Creates "curl" for performed request
        print(curl)

        # Record the request for swagger coverage only when enabled via the
        # --swagger-coverage flag (see conftest.pytest_configure). Recording
        # creates a swagger-coverage-output/<host:port>/ directory, which fails
        # on Windows because ":" is illegal in paths — so keep it off by default.
        if os.environ.get("SWAGGER_COVERAGE_ENABLED") == "1":
            uri = URI(
                host=self.host,
                base_path="",
                unformatted_path=path,
                uri_params=kwargs.get("params"),
            )
            handler = RequestSchemaHandler(uri, method.lower(), rest_response, dict(kwargs))
            await asyncio.to_thread(handler.write_schema)

        log.msg(
            event="Response",
            status_code=rest_response.status_code,
            headers=rest_response.headers,
            json=self._get_json(rest_response),
        )

        rest_response.raise_for_status()  # Raises HTTPError, if one occurred (status != 2xx)

        return rest_response

    @staticmethod
    def _get_json(rest_response: httpx.Response) -> dict[str, Any]:
        # httpx.Response.json() is typed as returning Any, so the result is
        # narrowed explicitly rather than let Any escape through the signature.
        try:
            body: dict[str, Any] = rest_response.json()
            return body
        except JSONDecodeError:
            return {}
