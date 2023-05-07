from abc import ABCMeta, abstractmethod
from collections.abc import Iterable, Mapping
from typing import Any, Generic, TypeVar

from requests.auth import AuthBase
from requests.models import Request, Response

from app.core_v1 import (
    CleanedData,
    DataSinkMetadata,
    DataSourceMetadata,
    ExtractMetadata,
    UploadMetadata,
)

from ..typings import ResponsePredicate

# =============================================================================
# TYPES
# =============================================================================

_CD = TypeVar("_CD", bound=CleanedData)


# =============================================================================
# API DIALECTS
# =============================================================================


class HTTPAPIDialect(metaclass=ABCMeta):  # noqa: B024
    """Marker interface for HTTP API Dialects.

    Implementations of this interface act as a bridge between the
    :class:`HTTPTransport` and varying HTTP APIs. This can be due to different
    versions of the same API or different APIs all together. As such, these
    implementations map resource requests to correct API endpoints and
    translate responses from those requests to the correct domain objects.
    """

    ...


class HTTPAuthAPIDialect(HTTPAPIDialect, metaclass=ABCMeta):
    """Provide an API to authenticate :class:`HTTPTransport` instances.

    .. note::
        This is considered a special API and is the only one required by
        `HTTPTransport` instances. Authentication to the remote server is
        handled automatically by `HTTPTransport` instances.
    """

    @property
    @abstractmethod
    def re_authenticate_predicate(self) -> ResponsePredicate:
        """A predicate to determine if a re-authentication should be triggered.

        This is accessed during a request attempt by a `HTTPTransport` instance
        (i.e. during a call to the `HTTPTransport.make_request` method)
        whenever a response fails a validity check but before the response is
        returned to the caller. If the predicate returned by this property
        resolves to ``True``, then a re-authentication of the transport is
        performed and if successful, the request is then retried again.

        :return: A predicate to determine if a re-authentication should be
            triggered.
        """
        ...

    # REQUEST FACTORIES
    # -------------------------------------------------------------------------
    @abstractmethod
    def auth_request_factory(self) -> Request:
        """Return a :class:`requests.Request` object to use for authentication.

        :return: a `Request` instance to use for authentication.
        """
        ...

    # RESPONSE HANDLERS
    # -------------------------------------------------------------------------
    @abstractmethod
    def handle_auth_response(self, response: Response) -> AuthBase:
        """Process an authentication response and return usable auth details.

        :param response: A response returned by a remote server from an
            authentication request.

        :return: An instance of `AuthBase` to use on subsequent details.
        """
        ...


class HTTPDataSinkAPIDialect(HTTPAPIDialect, Generic[_CD], metaclass=ABCMeta):
    # REQUEST FACTORIES
    # -------------------------------------------------------------------------
    @abstractmethod
    def consume_request_factory(
        self,
        clean_data: _CD,
        progress: float,
    ) -> Request:
        """

        :param clean_data:
        :param progress:

        :return:
        """
        ...

    # RESPONSE HANDLERS
    # -------------------------------------------------------------------------
    @abstractmethod
    def handle_consume_response(
        self,
        response: Response,
        clean_data: _CD,
        progress: float,
    ) -> None:
        """

        :param response:
        :param clean_data:
        :param progress:

        :return:
        """


class HTTPMetadataSinkAPIDialect(HTTPAPIDialect, metaclass=ABCMeta):
    # REQUEST FACTORIES
    # -------------------------------------------------------------------------
    @abstractmethod
    def consume_upload_meta_request_factory(
        self,
        upload_meta: UploadMetadata,
    ) -> Request:
        """

        :param upload_meta:

        :return:
        """
        ...

    @abstractmethod
    def init_upload_metadata_consumption_request_factory(
        self,
        extract_metadata: ExtractMetadata,
        content_type: str,
        **kwargs: Mapping[str, Any],
    ) -> Request:
        """

        :param extract_metadata:
        :param content_type:
        :param kwargs:

        :return:
        """
        ...

    # RESPONSE HANDLERS
    # -------------------------------------------------------------------------
    @abstractmethod
    def handle_consume_upload_meta_response(
        self,
        response: Response,
        upload_meta: UploadMetadata,
    ) -> None:
        """

        :param response:
        :param upload_meta:

        :return:
        """
        ...

    @abstractmethod
    def handle_init_upload_metadata_consumption_response(
        self,
        response: Response,
        extract_metadata: ExtractMetadata,
        content_type: str,
        **kwargs: Mapping[str, Any],
    ) -> UploadMetadata:
        """

        :param response:
        :param extract_metadata:
        :param content_type:
        :param kwargs:

        :return:
        """
        ...


class HTTPMetadataSourceAPIDialect(HTTPAPIDialect, metaclass=ABCMeta):
    # REQUEST FACTORIES
    # -------------------------------------------------------------------------
    @abstractmethod
    def provide_data_sink_meta_request_factory(self) -> Request:
        """

        :return:
        """
        ...

    @abstractmethod
    def provide_data_source_meta_request_factory(self) -> Request:
        """

        :return:
        """
        ...

    @abstractmethod
    def provide_extract_meta_request_factory(
        self,
        data_source: DataSourceMetadata,
    ) -> Request:
        """

        :param data_source:

        :return:
        """
        ...

    # RESPONSE HANDLERS
    # -------------------------------------------------------------------------

    @abstractmethod
    def handle_provide_data_sink_meta_response(
        self,
        response: Response,
    ) -> Iterable[DataSinkMetadata]:
        """

        :param response:
        :return:
        """

    @abstractmethod
    def handle_provide_data_source_meta_response(
        self,
        response: Response,
    ) -> Iterable[DataSourceMetadata]:
        """

        :param response:
        :return:
        """
        ...

    @abstractmethod
    def handle_provide_extract_meta_response(
        self,
        response: Response,
        data_source: DataSourceMetadata,
    ) -> Iterable[ExtractMetadata]:
        """

        :param response:
        :param data_source:

        :return:
        """
        ...
