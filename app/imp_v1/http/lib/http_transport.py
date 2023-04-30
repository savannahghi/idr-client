from collections.abc import Mapping
from typing import Any

from attrs import define, field
from requests.auth import AuthBase
from requests.exceptions import RequestException
from requests.models import PreparedRequest, Request, Response
from requests.sessions import Session

from app.core_v1 import Disposable

from ..exceptions import (
    HTTPTransportDisposedError,
    HTTPTransportTransientError,
)
from ..typings import ResponsePredicate
from .common import if_request_accepted, to_appropriate_domain_error
from .http_api_dialects import HTTPAuthAPIDialect

# =============================================================================
# HELPERS
# =============================================================================


class _NoAuth(AuthBase):
    """No Authentication.

    This is the default :class:`HTTPTransport` authentication which when
    added to a :class:`Request object<requests.Request>` implies that the
    `Request` is un-authenticated.
    """

    def __call__(self, r: PreparedRequest, *args, **kwargs) -> PreparedRequest:
        return r

# =============================================================================
# HTTP TRANSPORT AUTH
# =============================================================================


@define(order=False)
class HTTPTransport(Disposable):
    """A wrapper around common HTTP APIs functionality.

    These include:

    * Authentication and re-authentication.
    * Resource disposal and de-allocation.
    * Error handling and recovery.

    All these help to ensure a consistent behaviour between APIs.
    """

    _auth_api_dialect: HTTPAuthAPIDialect = field()
    _auth: AuthBase = field(factory=_NoAuth, kw_only=True)
    _connect_timeout: float = field(default=60, kw_only=True)
    _is_disposed: bool = field(default=False, init=False)
    _read_timeout: float = field(default=60, kw_only=True)
    _session: Session = field(factory=Session, kw_only=True)

    @property
    def auth_api_dialect(self) -> HTTPAuthAPIDialect:
        return self._auth_api_dialect

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed

    def authenticate(self) -> None:
        """Authenticate this `HTTPTransport` instance.

        :return: None.

        :raise HTTPTransportError: If an error occurs while authenticating to
            a remote server.
        """
        self._ensure_not_disposed()

        prepared_request: PreparedRequest
        settings: Mapping[str, Any]
        prepared_request, settings = self._prepare_request(
            self._auth_api_dialect.auth_request_factory(),
        )
        try:
            response: Response = self._session.send(
                request=prepared_request,
                timeout=(self._connect_timeout, self._read_timeout),
                **settings,
            )
        except RequestException as exp:
            err_msg: str = "Error: unable to authenticate."
            raise to_appropriate_domain_error(exp, message=err_msg) from exp

        self._auth = self._auth_api_dialect.handle_auth_response(response)

    def dispose(self) -> None:
        self._is_disposed = True
        self._auth = _NoAuth()
        self._session.close()

    def make_request(
            self,
            request: Request,
            valid_response_predicate: ResponsePredicate = if_request_accepted,
    ) -> Response:
        """Make an HTTP request to a remote server and return the response.

        :param request:
        :param valid_response_predicate:

        :return: The HTTP Response returned by the server.

        :raise HTTPTransportError: If an error occurs while making the request
            to the remote server.
        """
        self._ensure_not_disposed()
        request.auth = self._auth

        prepared_request: PreparedRequest
        settings: Mapping[str, Any]
        prepared_request, settings = self._prepare_request(request)
        try:
            response: Response = self._session.send(
                request=prepared_request,
                timeout=(self._connect_timeout, self._read_timeout),
                **settings,
            )
        except RequestException as exp:
            err_msg: str = "Error: unable to make request to remote server."
            raise to_appropriate_domain_error(exp, message=err_msg) from exp

        # Return the Response immediately if valid.
        if valid_response_predicate(response):
            return response

        # If the response doesn't qualify for a re-authentication, raise an
        # exception and stop further processing.
        if not self._auth_api_dialect.re_authenticate_predicate(response):
            err_msg: str = (
                "Error: Invalid response received from the remote server"
            )
            raise HTTPTransportTransientError(message=err_msg)

        # Else authenticate and retry the request again with the new auth
        # details.
        self.authenticate()
        return self.make_request(
            request=request,
            valid_response_predicate=valid_response_predicate,
        )

    def _ensure_not_disposed(self) -> None:
        """Check that this `HTTPTransport` instance is not disposed.

        If this instance is disposed, raise a `HTTPTransportDisposedError`,
        else return quietly.
        """
        if self._is_disposed:
            raise HTTPTransportDisposedError()

    def _prepare_request(
            self, request: Request,
    ) -> tuple[PreparedRequest, Mapping[str, Any]]:
        """Prepare a `Request` for sending and return it and its new settings.

        :param request: A `Request` instance to prep with this transports
            session settings.

        :return: The new prepared request together with the new merged settings
            that should be used when sending it.
        """

        req: PreparedRequest = self._session.prepare_request(request=request)
        settings: Mapping[str, Any] = self._session.merge_environment_settings(
            req.url, {}, None, None, None,
        )
        return req, settings
