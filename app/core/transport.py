from abc import ABCMeta, abstractmethod
from typing import Any, Mapping, Optional, Sequence

from .domain import (
    DataSource,
    DataSourceType,
    ExtractMetadata,
    UploadChunk,
    UploadMetadata,
)
from .mixins import Disposable

# =============================================================================
# TYPES
# =============================================================================

TransportOptions = Mapping[str, Any]


# =============================================================================
# TRANSPORT INTERFACE
# =============================================================================


class Transport(Disposable, metaclass=ABCMeta):
    """Represents the flow of data between an IDR Server and this app."""

    @abstractmethod
    def fetch_data_source_extracts(
        self,
        data_source_type: DataSourceType,
        data_source: DataSource,
        **options: TransportOptions,
    ) -> Sequence[ExtractMetadata]:
        """
        Fetch and return :class:`extracts <ExtractMetadata>` of the given
        :class:`data source <DataSource>` from an IDR Server.

        :param data_source_type: The data source type from which the the data
            source whose extracts are to be fetched belongs to.
        :param data_source: The data source whose extracts are to be fetched.
        :param options: Optional transport options.

        :return: A sequence of the retrieved extract metadata.

        :raise TransportClosedError: If this transport is closed.
        :raise TransportError: If an error occurs during the fetch.
        """
        ...

    @abstractmethod
    def fetch_data_sources(
        self, data_source_type: DataSourceType, **options: TransportOptions
    ) -> Sequence[DataSource]:
        """
        Fetch and return :class:`data sources <DataSource>` of the given
        :class:`data source type <DataSourceType>` from an IDR Server.

        :param data_source_type: The data source type whose data sources are to
            be fetched.
        :param options: Optional transport options.

        :return: A sequence of the retrieved data sources.

        :raise TransportClosedError: If this transport is closed.
        :raise TransportError: If an error occurs during the fetch.
        """
        ...

    @abstractmethod
    def mark_upload_as_complete(
        self, upload_metadata: UploadMetadata, **options: TransportOptions
    ) -> None:
        """
        Mark the given :class:`upload metadata instance <UploadMetadata>` as
        completed on the IDR Server. This should be called after all the chunks
        of the given upload metadata have been uploaded successfully.

        :param upload_metadata: The upload metadata instance to mark as
            completed.
        :param options: Optional transport options.

        :return: None.

        :raise TransportClosedError: If this transport is closed.
        :raise TransportError: If an error occurs during the fetch.
        """
        ...

    @abstractmethod
    def post_upload_chunk(
        self,
        upload_metadata: UploadMetadata,
        chunk_index: int,
        chunk_content: bytes,
        extra_init_kwargs: Optional[Mapping[str, Any]] = None,
        **options: TransportOptions,
    ) -> UploadChunk:
        """
        Register and create a new :class:`upload chunk <UploadChunk>` on the
        IDR Server. Finally, return the new *upload chunk* instance created
        from the given properties if the operation was successful.

        :param upload_metadata: The upload metadata instance whose chunk is to
            be posted/created.
        :param chunk_index: The precedence of the chunk when compared against
            other chunks belonging to the same upload metadata.
        :param chunk_content: The segment of data contained by the chunk.
        :param extra_init_kwargs: Extra initialization keyword arguments to
            pass to the returned upload chunk instance.
        :param options: Optional transport options.

        :return: A new upload chunk instance created using the provided
            properties.

        :raise TransportClosedError: If this transport is closed.
        :raise TransportError: If an error occurs while posting.
        """
        ...

    @abstractmethod
    def post_upload_metadata(
        self,
        extract_metadata: ExtractMetadata,
        content_type: str,
        org_unit_code: str,
        org_unit_name: str,
        extra_init_kwargs: Optional[Mapping[str, Any]] = None,
        **options: TransportOptions,
    ) -> UploadMetadata:
        """
        Register and create a new :class:`upload <UploadMetadata>` on the IDR
        Server. Finally, return the new *upload metadata* instance  created
        from the given properties if the operation was successful.

        .. note::
            This operation should be called after the provided extract metadata
            has been ran successfully against it's parent :class:`data source`
            and there is data available to be uploaded.

        :param extract_metadata: The extract metadata instance whose upload
            metadata instance is to be posted/created.
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

        :return: A new upload metadata instance created using the provided
            properties.

        :raise TransportClosedError: If this transport is closed.
        :raise TransportError: If an error occurs while posting.
        """
        ...
