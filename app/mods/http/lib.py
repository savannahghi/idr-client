from abc import ABCMeta, abstractmethod
from collections.abc import Sequence

from requests.auth import AuthBase
from requests.models import Request, Response


class HTTPAPIDialect(metaclass=ABCMeta):
    @property
    @abstractmethod
    def auth_trigger_status(self) -> Sequence[int]:
        """Return HTTP status codes that trigger a re-authentication.

        Return a sequence of HTTP status codes that when encountered on a
        response should trigger a re-authentication.

        :return: A sequence of HTTP status codes that should trigger a
            re-authentication.
        """
        ...

    @abstractmethod
    def request_authentication(self) -> Request:
        """

        :return:
        """

    @abstractmethod
    def handle_auth_response(self, response: Response) -> AuthBase:
        """

        :param response:
        :return:
        """
        ...
