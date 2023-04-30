from abc import ABCMeta, abstractmethod
from collections.abc import Iterable, Mapping
from typing import Any, Generic, TypeVar

from requests.auth import AuthBase
from requests.models import Request, Response

from app.core_v1 import (
    CleanedData,
    DataSourceMetadata,
    ExtractMetadata,
    UploadContentMetadata,
    UploadMetadata,
)

from ..typings import ResponsePredicate

# =============================================================================
# TYPES
# =============================================================================

_CD = TypeVar("_CD", bound=CleanedData)
_UC = TypeVar("_UC", bound=UploadContentMetadata)


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


class HTTPDataSinkAPIDialect(
    HTTPAPIDialect, Generic[_UC, _CD], metaclass=ABCMeta,
):

    # REQUEST FACTORIES
    # -------------------------------------------------------------------------
    @abstractmethod
    def consume_request_factory(
            self,
            upload_content_meta: _UC,
            clean_data: _CD,
            progress: float,
    ) -> Request:
        """

        :param upload_content_meta:
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
            upload_content_meta: _UC,
            clean_data: _CD,
            progress: float,
    ) -> None:
        """

        :param response:
        :param upload_content_meta:
        :param clean_data:
        :param progress:

        :return:
        """


class HTTPMetadataSinkAPIDialect(HTTPAPIDialect, metaclass=ABCMeta):

    # REQUEST FACTORIES
    # -------------------------------------------------------------------------
    @abstractmethod
    def consume_upload_meta_request_factory(
            self, upload_meta: UploadMetadata,
    ) -> Request:
        """

        :param upload_meta:

        :return:
        """
        ...

    @abstractmethod
    def consume_upload_content_meta_request_factory(
            self,
            upload_meta: UploadMetadata,
            upload_content_meta: UploadContentMetadata,
    ) -> Request:
        """

        :param upload_meta:
        :param upload_content_meta:

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

    @abstractmethod
    def init_upload_metadata_content_consumption_request_factory(
            self, upload_metadata: UploadMetadata, **kwargs: Mapping[str, Any],
    ) -> Request:
        """

        :param upload_metadata:
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
    def handle_consume_upload_content_meta_response(
            self,
            response: Response,
            upload_meta: UploadMetadata,
            upload_content_meta: UploadContentMetadata,
    ) -> None:
        """

        :param response:
        :param upload_meta:
        :param upload_content_meta:

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

    @abstractmethod
    def handle_init_upload_metadata_content_consumption_response(
            self,
            response: Response,
            upload_metadata: UploadMetadata,
            **kwargs: Mapping[str, Any],
    ) -> UploadContentMetadata:
        """

        :param response:
        :param upload_metadata:
        :param kwargs:

        :return:
        """
        ...


class HTTPMetadataSourceAPIDialect(HTTPAPIDialect, metaclass=ABCMeta):

    # REQUEST FACTORIES
    # -------------------------------------------------------------------------
    @abstractmethod
    def provide_metadata_source_request_factory(self) -> Request:
        """

        :return:
        """
        ...

    @abstractmethod
    def provide_extract_meta_request_factory(
            self, data_source: DataSourceMetadata,
    ) -> Request:
        """

        :param data_source:

        :return:
        """
        ...

    # RESPONSE HANDLERS
    # -------------------------------------------------------------------------

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

    @abstractmethod
    def handle_init_upload_metadata_content_consumption_response(
            self,
            response: Response,
            upload_metadata: UploadMetadata,
            **kwargs: Mapping[str, Any],
    ) -> UploadContentMetadata:
        """

        :param response:
        :param upload_metadata:
        :param kwargs:

        :return:
        """
        ...

    @abstractmethod
    def handle_provide_data_source_response(
            self, response: Response,
    ) -> Iterable[DataSourceMetadata]:
        """

        :param response:
        :return:
        """
        ...

    @abstractmethod
    def handle_provide_extract_meta_response(
            self, response: Response, data_source: DataSourceMetadata,
    ) -> Iterable[ExtractMetadata]:
        """

        :param response:
        :param data_source:

        :return:
        """
        ...
