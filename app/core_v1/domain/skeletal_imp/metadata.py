from abc import ABCMeta
from collections.abc import Mapping

from attrs import define, field

from ..interfaces import (
    DataSinkMetadata,
    DataSourceMetadata,
    ExtractMetadata,
    IdentifiableMetadataObject,
    MetadataObject,
    UploadMetadata,
)
from .base import (
    BaseDomainObject,
    BaseIdentifiableDomainObject,
    BaseNamedDomainObject,
)


@define(slots=False)
class BaseMetadataObject(BaseDomainObject, MetadataObject, metaclass=ABCMeta):
    """Base skeletal implementation for most :class:`MetadataObject` s."""

    ...


@define(slots=False)
class BaseIdentifiableMetadataObject(
    BaseIdentifiableDomainObject,
    BaseMetadataObject,
    IdentifiableMetadataObject,
    metaclass=ABCMeta,
):
    """
    Base skeletal implementation for most
    :class:`IdentifiableMetadataObject` implementations.
    """

    ...


@define(slots=False)
class BaseDataSinkMetadata(
    BaseNamedDomainObject,
    BaseIdentifiableMetadataObject,
    DataSinkMetadata,
    metaclass=ABCMeta,
):
    """
    Base skeletal implementation for most :class:`DataSinkMetadata`
    implementations.
    """

    ...


@define(slots=False)
class BaseDataSourceMetadata(
    BaseNamedDomainObject,
    BaseIdentifiableMetadataObject,
    DataSourceMetadata,
    metaclass=ABCMeta,
):
    """
    Base skeletal implementation for most :class:`DataSourceMetadata`
    implementations.
    """

    _extract_metadata: Mapping[str, ExtractMetadata] = field(
        factory=dict,
        kw_only=True,
    )

    @property
    def extract_metadata(self) -> Mapping[str, ExtractMetadata]:
        return self._extract_metadata

    @extract_metadata.setter
    def extract_metadata(
        self,
        extract_metas: Mapping[str, ExtractMetadata],
    ) -> None:
        self._extract_metadata = extract_metas


@define(slots=False)
class BaseExtractMetadata(
    BaseNamedDomainObject,
    BaseIdentifiableMetadataObject,
    ExtractMetadata,
    metaclass=ABCMeta,
):
    """
    Base skeletal implementation for most :class:`ExtractMetadata`
    implementations.
    """

    _data_source_metadata: DataSourceMetadata = field()

    @property
    def data_source_metadata(self) -> DataSourceMetadata:
        return self._data_source_metadata


@define(slots=False)
class BaseUploadMetadata(
    BaseIdentifiableMetadataObject,
    UploadMetadata,
    metaclass=ABCMeta,
):
    """
    Base skeletal implementation for most :class:`UploadMetadata`
    implementations.
    """

    _content_type: str = field()
    _extract_metadata: ExtractMetadata = field()

    @property
    def content_type(self) -> str:
        return self._content_type

    @property
    def extract_metadata(self) -> ExtractMetadata:
        return self._extract_metadata
