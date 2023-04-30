from abc import ABCMeta, abstractmethod
from collections.abc import Iterable, Mapping
from typing import Any

from ...mixins import Disposable
from .base import NamedDomainObject
from .metadata import (
    DataSourceMetadata,
    ExtractMetadata,
    UploadContentMetadata,
    UploadMetadata,
)

# =============================================================================
# PIPELINE TERMINAL INTERFACES
# =============================================================================


class MetadataSink(NamedDomainObject, Disposable, metaclass=ABCMeta):
    """Uploads related metadata consumer.

    An interface representing entities that consume metadata relating to
    uploaded data.
    """
    # TODO: Think🤔 about where are ID's going to come from?
    @abstractmethod
    def consume_upload_meta(self, upload_meta: UploadMetadata) -> None:
        """

        :param upload_meta:
        :return:
        """
        ...

    @abstractmethod
    def consume_upload_content_meta(
            self,
            upload_meta: UploadMetadata,
            upload_content_meta: UploadContentMetadata,
            **kwargs: Mapping[str, Any],
    ) -> None:
        """

        :param upload_meta:
        :param upload_content_meta:
        :return:
        """
        ...

    @abstractmethod
    def init_upload_metadata_consumption(
            self,
            extract_metadata: ExtractMetadata,
            content_type: str,
            **kwargs: Mapping[str, Any],
    ) -> UploadMetadata:
        """

        :param extract_metadata:
        :param content_type:
        :return:
        """
        ...

    @abstractmethod
    def init_upload_metadata_content_consumption(
            self,
            upload_metadata: UploadMetadata,
            **kwargs: Mapping[str, Any],
    ) -> UploadContentMetadata:
        """

        :param upload_metadata:

        :return:
        """
        ...


class MetadataSource(NamedDomainObject, Disposable, metaclass=ABCMeta):
    """Extract(s) related metadata producer/provider.

    An interface representing entities that serve/produce metadata describing
    what data is to be extracted and from where.
    """

    @abstractmethod
    def provide_data_source_meta(self) -> Iterable[DataSourceMetadata]:
        """

        :return:
        """
        ...

    @abstractmethod
    def provide_extract_meta(
            self, data_source: DataSourceMetadata,
    ) -> Iterable[ExtractMetadata]:
        """

        :return:
        """
        ...
