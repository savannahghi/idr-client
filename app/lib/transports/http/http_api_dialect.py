from abc import ABCMeta, abstractmethod
from typing import Mapping, Sequence

from app.core import (
    DataSource,
    DataSourceType,
    ExtractMetadata,
    TransportOptions,
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
        self, response_content: bytes, **options: TransportOptions
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
        self, data_source_type: DataSourceType, **options: TransportOptions
    ) -> HTTPRequestParams:
        """
        Construct and return a request object to fetch all
        :class:`data sources <app.core.DataSource>` relating to the given
        :class:`data source type <app.core.DataSourceType>` from an IDR server.

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
