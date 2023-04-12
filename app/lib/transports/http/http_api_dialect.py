from abc import ABCMeta, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any

from app.core import (
    DataSource,
    DataSourceType,
    ExtractMetadata,
    TransportOptions,
    UploadChunk,
    UploadMetadata,
)

from .types import HTTPRequestParams


class HTTPAPIDialect(metaclass=ABCMeta):
    """
    This interface acts as a bridge between a :class:`HTTPTransport` and
    varying IDR Server API implementations. It maps resource requests to
    correct API endpoints and translates responses for those requests to
    correct domain objects.
    """

    # AUTHENTICATION
    # -------------------------------------------------------------------------
    @property
    @abstractmethod
    def auth_trigger_statuses(self) -> Sequence[int]:
        """
        Return a sequence of HTTP status codes that when encountered on
        responses should trigger a re-authentication.

        :return: A sequence of HTTP status codes that should trigger a
            re-authentication.
        """
        ...

    @abstractmethod
    def authenticate(self, **options: TransportOptions) -> HTTPRequestParams:
        """
        Return a request object that can be used to authenticate this client
        on an IDR Server.

        :param options: Option transport options.

        :return: A request object to use when authenticating this client with
            an IDR Server.
        """
        ...

    @abstractmethod
    def response_to_auth(
        self,
        response_content: bytes,
        **options: TransportOptions,
    ) -> Mapping[str, str]:
        """
        Process the contents of an authentication response and return a mapping
        of HTTP headers to be included on subsequent requests to the server.

        :param response_content: The contents of an authentication response.
        :param options: Optional transport options.

        :return: A mapping of HTTP headers to be included on subsequent
            requests to the server.
        """
        ...

    # DATA SOURCE EXTRACTS RETRIEVAL
    # -------------------------------------------------------------------------
    @abstractmethod
    def fetch_data_source_extracts(
        self,
        data_source_type: DataSourceType,
        data_source: DataSource,
        **options: TransportOptions,
    ) -> HTTPRequestParams:
        """
        Construct and return a request object to fetch all
        :class: `extract metadata <app.core.ExtractMetadata>` relating to the
        given :class:`data source <app.core.DataSource>` from an IDR Server.

        :param data_source_type: The data source type from which the data
            source whose extracts are being fetched belongs.
        :param data_source: The data source whose extract metadata is to be
            retrieved from an IDR Server.
        :param options: Optional transport options.

        :return: A request object to fetch all extract metadata relating to the
            given data source.
        """
        ...

    @abstractmethod
    def response_to_data_source_extracts(
        self,
        response_content: bytes,
        data_source_type: DataSourceType,
        data_source: DataSource,
        **options: TransportOptions,
    ) -> Sequence[ExtractMetadata]:
        """
        Process the contents of a *fetch data source extracts* response and
        return a sequence of the retrieved extracts.

        :param response_content: The contents of a fetch data source extracts
            response.
        :param data_source_type: The data source type from which the data
            source whose extracts are being fetched belongs.
        :param data_source: The data source whose extracts are being retrieved.
        :param options: Optional transport options.

        :return: A sequence of the retrieved data source extracts.
        """
        ...

    # DATA SOURCES RETRIEVAL
    # -------------------------------------------------------------------------
    @abstractmethod
    def fetch_data_sources(
        self,
        data_source_type: DataSourceType,
        **options: TransportOptions,
    ) -> HTTPRequestParams:
        """
        Construct and return a request object to fetch all
        :class:`data sources <app.core.DataSource>` relating to the given
        :class:`data source type <app.core.DataSourceType>` from an IDR Server.

        :param data_source_type: The data source type whose data sources are to
            be retrieved from an IDR Server.
        :param options: Optional transport options.

        :return: A request object to fetch all data sources relating to the
            given data source type.
        """
        ...

    @abstractmethod
    def response_to_data_sources(
        self,
        response_content: bytes,
        data_source_type: DataSourceType,
        **options: TransportOptions,
    ) -> Sequence[DataSource]:
        """
        Process the contents of a *fetch data sources* response and return a
        sequence of the retrieved data sources.

        :param response_content: The contents of a fetch data sources response.
        :param data_source_type: The data source type whose data sources are
            being retrieved.
        :param options: Optional transport options.

        :return: A sequence of the retrieved data sources.
        """
        ...

    # MARK UPLOAD COMPLETION
    # -------------------------------------------------------------------------
    @abstractmethod
    def mark_upload_as_complete(
        self,
        upload_metadata: UploadMetadata,
        **options: TransportOptions,
    ) -> HTTPRequestParams:
        """
        Construct and return a request object used to mark an
        :class:`upload metadata instance <UploadMetadata>` as completed.

        :param upload_metadata: The upload metadata instance to be marked as
            completed.
        :param options: Optional transport options.

        :return: A request object to mark an upload metadata instance as
            completed.
        """
        ...

    # TODO: Consider adding `response_to_mark_upload_as_completed` method.

    # UPLOAD CHUNK POSTAGE
    # -------------------------------------------------------------------------
    @abstractmethod
    def post_upload_chunk(
        self,
        upload_metadata: UploadMetadata,
        chunk_index: int,
        chunk_content: Any,  # noqa: ANN401
        extra_init_kwargs: Mapping[str, Any] | None = None,
        **options: TransportOptions,
    ) -> HTTPRequestParams:
        """
        Construct and return a request object used to register and create a new
        :class:`upload chunk <app.core.UploadChunk>` on the IDR Server.

        :param upload_metadata: The upload metadata instance whose chunk is to
            be posted/created.
        :param chunk_index: The precedence of the chunk when compared against
            other chunks belonging to the same upload metadata.
        :param chunk_content: The segment of data contained by the chunk.
        :param extra_init_kwargs: Extra initialization keyword arguments to
            pass to the returned upload chunk instance.
        :param options: Optional transport options.

        :return: A request object to create and register a new chunk instance
            with the given properties.
        """
        ...

    @abstractmethod
    def response_to_upload_chunk(
        self,
        response_content: bytes,
        upload_metadata: UploadMetadata,
        **options: TransportOptions,
    ) -> UploadChunk:
        """
        Process the contents of a *post upload chunk* response and construct
        and return an :class:`upload chunk <app.core.UploadChunk>` instance.

        :param response_content: The contents of a post upload chunk response.
        :param upload_metadata: The upload metadata instance whose chunk is
            being posted.
        :param options: Optional transport options.

        :return: An upload chunk instance created after a successful posting.
        """
        ...

    # UPLOAD METADATA POSTAGE
    # -------------------------------------------------------------------------
    @abstractmethod
    def post_upload_metadata(
        self,
        extract_metadata: ExtractMetadata,
        content_type: str,
        org_unit_code: str,
        org_unit_name: str,
        extra_init_kwargs: Mapping[str, Any] | None = None,
        **options: TransportOptions,
    ) -> HTTPRequestParams:
        """
        Construct and return a request object used to register and create a new
        :class:`upload metadata <app.core.UploadMetadata>` on the IDR Server.

        :param extract_metadata: The extract metadata instance whose upload
            metadata instance is being posted/created.
        :param content_type: The final format that the (chunked) data will have
            when it's finally uploaded to the IDR Server.
        :param org_unit_code: A unique code that identifies the location where
            the data being uploaded was extracted from. This is most likely the
            same location that the IDR Client process is running on.
        :param org_unit_name: A human readable identifying the location where
            the data being uploaded was extracted from. This is most likely the
            same location that the IDR Client process is running on.
        :param extra_init_kwargs: Extra initialization keyword arguments to
            pass to the returned upload metadata.
        :param options: Optional transport options.

        :return: A request object to create and register a new upload metadata
            instance with the given properties.
        """
        ...

    @abstractmethod
    def response_to_upload_metadata(
        self,
        response_content: bytes,
        extract_metadata: ExtractMetadata,
        **options: TransportOptions,
    ) -> UploadMetadata:
        """
        Process the contents of a *post upload metadata* response and construct
        and return an :class:`upload metadata <app.core.UploadMetadata>`
        instance.

        :param response_content: The contents of a post upload metadata
            response.
        :param extract_metadata: The extract metadata instance whose upload
            metadata instance is being posted/created.
        :param options: Optional transport options.

        :return: An upload metadata instance created after a successful
            posting.
        """
        ...
