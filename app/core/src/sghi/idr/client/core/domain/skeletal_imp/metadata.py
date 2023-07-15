from abc import ABCMeta
from collections.abc import Mapping

from attrs import define, field

from ..interfaces import (
    DataSinkMetadata,
    DataSourceMetadata,
    DrainMetadata,
    DrawMetadata,
    IdentifiableMetadataObject,
    MetadataObject,
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

    _draw_metadata: Mapping[str, DrawMetadata] = field(
        factory=dict,
        kw_only=True,
        repr=False,
    )

    @property
    def draw_metadata(self) -> Mapping[str, DrawMetadata]:
        return self._draw_metadata

    @draw_metadata.setter
    def draw_metadata(
        self,
        draw_metadata: Mapping[str, DrawMetadata],
    ) -> None:
        self._draw_metadata = draw_metadata


@define(slots=False)
class BaseDrawMetadata(
    BaseNamedDomainObject,
    BaseIdentifiableMetadataObject,
    DrawMetadata,
    metaclass=ABCMeta,
):
    """
    Base skeletal implementation for most :class:`DrawMetadata`
    implementations.
    """

    _data_source_metadata: DataSourceMetadata = field()

    @property
    def data_source_metadata(self) -> DataSourceMetadata:
        return self._data_source_metadata


@define(slots=False)
class BaseDrainMetadata(
    BaseIdentifiableMetadataObject,
    DrainMetadata,
    metaclass=ABCMeta,
):
    """
    Base skeletal implementation for most :class:`UploadMetadata`
    implementations.
    """

    _draw_metadata: DrawMetadata = field()

    @property
    def draw_metadata(self) -> DrawMetadata:
        return self._draw_metadata
