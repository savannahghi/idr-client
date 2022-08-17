import logging
from typing import Any, Mapping, Optional, Sequence

from requests.auth import AuthBase
from requests.models import PreparedRequest, Response
from requests.sessions import Session

from app.__version__ import __title__, __version__
from app.core import (
    DataSource,
    DataSourceType,
    ExtractMetadata,
    Transport,
    TransportClosedError,
    TransportError,
    TransportOptions,
    UploadChunk,
    UploadMetadata,
)

from .http_api_dialect import HTTPAPIDialect
from .types import HTTPRequestParams

# =============================================================================
# CONSTANTS
# =============================================================================

_LOGGER = logging.getLogger(__name__)


# =============================================================================
# HTTP TRANSPORT
# =============================================================================


class HTTPTransport(Transport):
    """
    An implementation of the :class:`transport <Transport>` interface that uses
    the HTTP protocol for data transmission between an IDR Server and IDR
    client.
    """

    def __init__(
        self,
        api_dialect: HTTPAPIDialect,
        connect_timeout: Optional[float] = None,
        read_timeout: Optional[float] = None,
    ):
        """
        Initialize a new ``HTTPTransport`` with the given options.

        :param api_dialect: The ``HTTPAPIDialect`` to use.
        :param connect_timeout: An optional connect timeout.
        :param read_timeout: An optional read timeout.
        """
        super().__init__()
        from app.lib import ensure_not_none

        self._api_dialect: HTTPAPIDialect = ensure_not_none(
            api_dialect, '"api_dialect" MUST be provided and not none.'
        )
        self._timeout = (
            (connect_timeout, read_timeout)
            if connect_timeout is not None
            else connect_timeout
        )
        self._session: Session = Session()
        self._session.headers.update(
            {"Accept": "*/*", "User-Agent": "%s/%s" % (__title__, __version__)}
        )
        self._auth: AuthBase = _NoAuth()
        self._is_closed: bool = False

    @property
    def is_disposed(self) -> bool:
        return self._is_closed

    def dispose(self) -> None:
        _LOGGER.debug("Closing transport")
        self._is_closed = True
        self._session.close()

    #  FETCH DATA SOURCE EXTRACTS
    # -------------------------------------------------------------------------
    def fetch_data_source_extracts(
        self,
        data_source_type: DataSourceType,
        data_source: DataSource,
        **options: TransportOptions,
    ) -> Sequence[ExtractMetadata]:
        self._ensure_not_closed()
        response: Response = self._make_request(
            self._api_dialect.fetch_data_source_extracts(
                data_source_type, data_source, **options
            )
        )
        return self._api_dialect.response_to_data_source_extracts(
            response_content=response.content,
            data_source_type=data_source_type,
            data_source=data_source,
            **options,
        )

    #  FETCH DATA SOURCES
    # -------------------------------------------------------------------------
    def fetch_data_sources(
        self, data_source_type: DataSourceType, **options: TransportOptions
    ) -> Sequence[DataSource]:
        self._ensure_not_closed()
        response: Response = self._make_request(
            self._api_dialect.fetch_data_sources(data_source_type, **options)
        )
        return self._api_dialect.response_to_data_sources(
            response_content=response.content,
            data_source_type=data_source_type,
            **options,
        )

    # MARK UPLOAD COMPLETION
    # -------------------------------------------------------------------------
    def mark_upload_as_complete(
        self, upload_metadata: UploadMetadata, **options: TransportOptions
    ) -> None:
        self._ensure_not_closed()
        self._make_request(
            self._api_dialect.mark_upload_as_complete(
                upload_metadata, **options
            )
        )
        return None

    # UPLOAD CHUNK POSTAGE
    # -------------------------------------------------------------------------
    def post_upload_chunk(
        self,
        upload_metadata: UploadMetadata,
        chunk_index: int,
        chunk_content: bytes,
        extra_init_kwargs: Optional[Mapping[str, Any]] = None,
        **options: TransportOptions,
    ) -> UploadChunk:
        self._ensure_not_closed()
        response: Response = self._make_request(
            self._api_dialect.post_upload_chunk(
                upload_metadata=upload_metadata,
                chunk_index=chunk_index,
                chunk_content=chunk_content,
                extra_init_kwargs=extra_init_kwargs,
                **options,
            )
        )
        return self._api_dialect.response_to_upload_chunk(
            response_content=response.content,
            upload_metadata=upload_metadata,
            **options,
        )

    # UPLOAD METADATA POSTAGE
    # -------------------------------------------------------------------------
    def post_upload_metadata(
        self,
        extract_metadata: ExtractMetadata,
        content_type: str,
        org_unit_code: str,
        org_unit_name: str,
        extra_init_kwargs: Optional[Mapping[str, Any]] = None,
        **options: TransportOptions,
    ) -> UploadMetadata:
        self._ensure_not_closed()
        response: Response = self._make_request(
            self._api_dialect.post_upload_metadata(
                extract_metadata=extract_metadata,
                content_type=content_type,
                org_unit_code=org_unit_code,
                org_unit_name=org_unit_name,
                extra_init_kwargs=extra_init_kwargs,
                **options,
            )
        )
        return self._api_dialect.response_to_upload_metadata(
            response_content=response.content,
            extract_metadata=extract_metadata,
            **options,
        )

    # OTHER HELPERS
    # -------------------------------------------------------------------------
    def _authenticate(self) -> AuthBase:
        self._ensure_not_closed()
        _LOGGER.info("Authenticating HTTP transport.")
        request: HTTPRequestParams = self._api_dialect.authenticate()
        response: Response = self._session.request(
            data=request.get("data"),
            headers=request.get("headers"),
            method=request["method"],
            params=request.get("params"),
            url=request["url"],
            timeout=self._timeout,  # type: ignore
        )

        # If authentication was unsuccessful, there is not much that can be
        # done, just log it and raise an exception.
        if response.status_code != request["expected_http_status_code"]:
            error_message: str = (
                "Unable to authenticate the client on IDR Server. Server "
                'says: "%s".' % response.text
            )
            _LOGGER.error(error_message)
            raise TransportError(error_message)
        return _HTTPTransportAuth(
            auth_headers=self._api_dialect.response_to_auth(
                response_content=response.content
            )
        )

    def _ensure_not_closed(self) -> None:
        if self._is_closed:
            raise TransportClosedError()

    def _make_request(self, request: HTTPRequestParams) -> Response:
        self._ensure_not_closed()
        request_message: str = "HTTP Request (%s | %s)" % (
            request["method"],
            request["url"],
        )
        _LOGGER.info(request_message)
        response: Response = self._session.request(
            data=request.get("data"),
            files=request.get("files"),
            headers=request.get("headers"),
            method=request["method"],
            params=request.get("params"),
            url=request["url"],
            auth=self._auth,
            timeout=self._timeout,  # type: ignore
        )
        if response.status_code != request["expected_http_status_code"]:
            _LOGGER.debug(
                'Got an unexpected HTTP status, expected="%d", but got'
                ' "%d" instead.',
                request["expected_http_status_code"],
                response.status_code,
            )
            # If the received response status was not what was expected, check
            # if the status is among the re-authentication trigger status and
            # if so, re-authenticate and then retry this request.
            if response.status_code in self._api_dialect.auth_trigger_statuses:
                _LOGGER.debug(
                    'Encountered an authentication trigger status("%d"), '
                    "re-authenticating.",
                    response.status_code,
                )
                self._auth = self._authenticate()
                _LOGGER.debug(
                    "Re-authentication successful, retrying the request."
                )
                # FIXME: This could lead into a stack overflow, revisit this.
                return self._make_request(request)

            # If not, then an error has occurred, log the error the raise an
            # exception.
            error_message: str = (
                "%s : Failed. Expected response status %d, but got %d."
                % (
                    request_message,
                    request["expected_http_status_code"],
                    response.status_code,
                )
            )
            _LOGGER.error(error_message)
            raise TransportError(message=error_message)
        return response


# =============================================================================
# HTTP TRANSPORT AUTH
# =============================================================================


class _HTTPTransportAuth(AuthBase):
    """
    The ``Auth`` implementation used by the :class:`HTTPTransport` after a
    successful authentication.
    """

    def __init__(self, auth_headers: Mapping[str, str]):
        self._auth_headers = auth_headers

    def __call__(
        self, r: PreparedRequest, *args, **kwargs
    ) -> PreparedRequest:  # pragma: no cover
        r.headers.update(self._auth_headers)
        return r


class _NoAuth(AuthBase):
    """
    An ``Auth`` implementation of an un-authenticated :class:`HTTPTransport`.
    """

    def __call__(
        self, r: PreparedRequest, *args, **kwargs
    ) -> PreparedRequest:  # pragma: no cover
        return r
