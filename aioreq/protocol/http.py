import asyncio
import logging
import json as _json

from ..parser.response_parser import ResponseParser
from ..parser.url_parser import UrlParser
from ..parser.response_parser import ResponseParser
from ..socket.connection import resolve_domain
from ..socket.connection import HttpClientProtocol
from ..settings import LOGGER_NAME
from ..settings import DEFAULT_CONNECTION_TIMEOUT

log = logging.getLogger(LOGGER_NAME)

class HttpProtocol:
    """
    Abstract class for all Http units representing HTTP/1.1 protocol
    with the general attributes
    """

    safe_methods = (
            "GET",
            "HEAD"
            )

class BaseRequest(HttpProtocol):
    ...

class Request(BaseRequest):
    """
    Http request Class

    Request class contains all HTTP properties for requesting
    as object attributes.
    Also gives raw encoded data which used to send bytes via socket
    """

    def __init__(
            self,
            method : str,
            host: str,
            headers: dict | None,
            path: str,
            raw_request: None | str = None,
            body: str = '',
            json: str = '',
            path_parameters = (),
            scheme_and_version: str = 'HTTP/1.1'
    ) -> None:
        """
        Request initialization method

        :param method: HTTP method (GET, POST, PUT, PATCH)
        :param host: HTTP header host which contains host's domain
        :param headers: HTTP headers
        :param path: HTTP server endpoint path specified after top-level domain
        :scheme_and_version: HTTP scheme and version where HTTP is scheme 1.1 is a version
        :returns: None
        """

        self.host = host
        self.headers = headers
        self.method = method
        self.path = path
        self.body = body
        self.json = json
        self.path_parameters = path_parameters
        self.scheme_and_version = scheme_and_version
        self.__raw_request = raw_request
        self.parser = None


    def get_raw_request(self) -> bytes:
        """
        Getter method for raw_request private attribute
        """

        if self.__raw_request:
            return self.__raw_request

        if self.parser is None:
            from ..parser import request_parser
            self.parser = request_parser.RequestParser

        message = self.parser.parse(self)
        return message.encode('utf-8')

    def __repr__(self) -> str:
        return '\n'.join((
            f"Request(",
            f"\tscheme_and_version='{self.scheme_and_version}'",
            f"\thost= '{self.host}'",
            f"\tmethod= '{self.method}'",
            f"\tpath= '{self.path}'",
            f"\tHeaders:",
            *(
                f"\t\t{key}: {value}" for key, value in self.headers.items()
            ),
            f"\tBody: {len(self.body)} length"
            ')'
        ))

class BaseResponse(HttpProtocol):
    ...

class Response(BaseResponse):
    """
    Http response Class

    Response class which is one of the first types that
    user using this library can see, it's result for all
    http requests methods like GET, PUT, PATCH, POST
    """

    def __init__(
            self,
            scheme_and_version: str,
            status: int,
            status_message: str,
            headers: dict,
            body: str,
            request: Request = None):
        """
        Response initalization method

        :param scheme_and_version: Version and scheme for http. For example HTTP/1.1
        :param status: response code returned with response
        :param status_message: message returned with response status code
        :param headers: response headers for example, Connection : Keep-Alive if version lower than HTTP/1.1
        :param body: response body
        :param request: request which response is self
        :returns: None
        """
        self.scheme_and_version = scheme_and_version
        self.status = status
        self.status_message = status_message
        self.headers = headers
        self.body = body
        self.request = request

    def __repr__(self):
        return '\n'.join((
            f"Response(",
            f"\tscheme_and_version='{self.scheme_and_version}'",
            f"\tstatus = {self.status}",
            f"\tstatus_message = '{self.status_message}'",
            f"\tHeaders:",
            *(
                f"\t\t{key}: {value}" for key, value in self.headers.items()
            ),
            f"\tBody: {len(self.body)} length"
            ')'
        ))

class Client:
    """
    Session like class Client

    Client used to send requests with same headers or 
    send requests using same connections which are stored in
    the Client's connection pool 
    """

    def __init__(self, headers=None):
        """
        Initalization method for Client, session like object

        :param headers: HTTP headers that should be sent with each request in this session
        """

        if headers is None:
            headers = {
                    'User-Agent' : 'Mozilla/5.0',
                    'Accept'     : 'text/html',
                    'Accept-Language': 'en-us',
                    'Accept-Charser': 'ISO-8859-1,utf-8',
                    'Connection' : 'keep-alive'
                    }
        self.connection_mapper = {}
        self.headers = headers

    async def send_request(self,
                           url: str, 
                           method: str, 
                           body: str | bytearray | bytes = '', 
                           path_parameters: tuple = (),
                           headers: None | dict = None, 
                           json: str | None = '') -> Response:
        """
        Simulates http request 

        :param url: Url where should be request send
        :param headers: Http headers which should be used in this GET request
        :param body: Http body part
        :returns: Response object which represents returned by server response 
        """

        if headers is None:
            headers = {}
        splited_url = UrlParser.parse(url)
        transport, protocol = await self.make_connection(splited_url)

        json = _json.dumps(json)
        request = Request(
            method=method,
            host=splited_url.get_url_without_path(),
            headers=self.headers | headers,
            path=splited_url.path,
            path_parameters = path_parameters,
            json=json,
            body=body
        )
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        protocol.send_http_request(request, future)
        raw_response = await future

        if isinstance(raw_response, Exception):
            raise raw_response
        response = ResponseParser.parse(raw_response)
        response.request = request
        return response



    async def get(self, url, body='', headers=None, json='') -> Response:
        return await self.send_request(
                url=url,
                method="GET",
                body=body,
                headers=headers,
                json=json,
                )

    async def post(self, url, body='', headers=None, json='') -> Response:
        return await self.send_request(
                url=url,
                method="POST",
                body=body,
                headers=headers,
                json=json,
                )

    async def make_connection(self, splited_url):
        """
        Getting connection from already opened connections, to perform Keep-Alive logic,
        if these connections exists or create the new one and save into connection pool

        :param splited_url: Url object which contains all url parts (scheme, version, subdomain, domain, ...)
        :returns: (transport, protocol) which are objects returned by loop.create_connection method
        """

        transport, protocol = self.connection_mapper.get(splited_url.get_url_for_dns(), (None, None))

        if transport and transport.is_closing():
            transport, protocol = None, None

        if not transport:
            ip, port = resolve_domain(splited_url.get_url_for_dns())
            loop = asyncio.get_event_loop()
            connection_coroutine = loop.create_connection(
                lambda: HttpClientProtocol(),
                host=ip,
                port=port
            )
            try:
                transport, protocol = await asyncio.wait_for(connection_coroutine, timeout=DEFAULT_CONNECTION_TIMEOUT)
            except asyncio.exceptions.TimeoutError as err:
                raise Exception('Timeout Error') from err

            self.connection_mapper[splited_url.get_url_for_dns()] = transport, protocol
        else:
            log.info("Using previous connection")
        return transport, protocol

    async def __aenter__(self):
        """
        Implements startpoint for Client
        for keyword <with> supporting

        :returns: Client object
        """
        return self

    async def __aexit__(self, *args, **kwargs):
        """
        Closes session resources which are all transport
        connections into connection pool
        """

        for host, (transport, protocol) in self.connection_mapper.items():
            transport.close()
            log.info(f"Transport closed {transport=}")
