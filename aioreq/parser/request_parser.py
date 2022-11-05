import json as _json

from abc import ABCMeta
from abc import abstractmethod

from typing import Iterable

class BaseRequestParser(ABCMeta):
    """
    Change me
    """

    @abstractmethod
    def parse(cls: type, 
              request: 'Request') -> str: # type: ignore
        ...


class RequestParser(BaseRequestParser):
    """
    For parsing Request object to raw data which can be sent
    via socket
    """
    
    @classmethod
    def sum_path_parameters(cls: type, 
                            parameters: Iterable[Iterable[str]]):
        return "&".join([f"{key}={value}" for key, value in parameters])

    @classmethod
    def parse(cls, request: 'Request') -> str: # type: ignore 
        """
        Parsing object type of request to string representing HTTP message

        :returns: raw http request text
        :rtype: str
        """

        if request.path_parameters:
            request.path += '?' + \
                cls.sum_path_parameters(request.path_parameters)

        if request.json:
            request.body = _json.dumps(request.json)
            request.headers['Content-Type'] = "application/json"

        elif request.body:
            request.headers['Content-Length'] = len(request.body) 
    
        message = ('\r\n'.join((
            f'{request.method} {request.path} {request.scheme}/{request.version}',
            f'host:  {request.host.split("://", 1)[1]}',
            *(f"{key}:  {value}" for key, value in request.headers.items()),
        )) + ('\r\n\r\n'))
        
        if type(request.body) in (bytes, bytearray):
            request.body = request.body.decode()
        message += request.body or ''

        return message
