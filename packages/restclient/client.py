import asyncio
import os
import structlog
import uuid
import curlify2
import httpx

from json import JSONDecodeError
from swagger_coverage_py.listener import URI, RequestSchemaHandler
from packages.restclient.configuration import Configuration
from packages.restclient.utilities import allure_attach

# Proxy implementation

class RestClient:
    def __init__(self, configuration: Configuration):
        self.session = httpx.AsyncClient(verify=configuration.verify)
        self.host = configuration.host
        self.set_headers(configuration.headers)
        self.disable_log = configuration.disable_log        
        self.log = structlog.get_logger(__name__).bind(service='api')   # __name__ - logger will have currnet class name
                                                                        # service='api' - logger is for 'api' service
        #...
    

    def set_headers(self, headers):
        if headers:
            self.session.headers.update(headers)

    async def post(self, path, **kwargs):
        return await self._send_request(method='POST', path=path, **kwargs)
    
    async def get(self, path, **kwargs):
        return await self._send_request(method='GET', path=path, **kwargs)
    
    async def put(self, path, **kwargs):
        return await self._send_request(method='PUT', path=path, **kwargs)
    
    async def delete(self, path, **kwargs):
        return await self._send_request(method='DELETE', path=path, **kwargs)
    
    @allure_attach 
    async def _send_request(self, method, path, **kwargs):
        log = self.log.bind(event_id=str(uuid.uuid4()))
        full_url = self.host + path

        if self.disable_log:
            rest_response = await self.session.request(method=method, url=full_url, **kwargs)
            rest_response.raise_for_status() # Raises HTTPError, if one occurred (status != 2xx)
            
            return rest_response          
        
        log.msg(
            event='Request',
            method=method,
            full_url=full_url,
            params=kwargs.get('params'),
            headers=kwargs.get('headers'),
            json=kwargs.get('json'),
            data=kwargs.get('data')
        )
        
        rest_response = await self.session.request(method=method, url=full_url, **kwargs)
        curl = curlify2.Curlify(rest_response.request).to_curl() # Creates "curl" for performed request
        print(curl)
        
        # Record the request for swagger coverage only when enabled via the
        # --swagger-coverage flag (see conftest.pytest_configure). Recording
        # creates a swagger-coverage-output/<host:port>/ directory, which fails
        # on Windows because ":" is illegal in paths — so keep it off by default.
        if os.environ.get('SWAGGER_COVERAGE_ENABLED') == '1':
            uri = URI(host=self.host, base_path="", unformatted_path=path, uri_params=kwargs.get('params'))
            handler = RequestSchemaHandler(uri, method.lower(), rest_response, kwargs)
            await asyncio.to_thread(handler.write_schema)
        
        log.msg(
            event="Response",
            status_code=rest_response.status_code,
            headers=rest_response.headers,
            json=self._get_json(rest_response)
        )
        
        rest_response.raise_for_status() # Raises HTTPError, if one occurred (status != 2xx)
        
        return rest_response
    
    @staticmethod
    def _get_json(rest_response):
        try:
            return rest_response.json()
        except JSONDecodeError:
            return {}