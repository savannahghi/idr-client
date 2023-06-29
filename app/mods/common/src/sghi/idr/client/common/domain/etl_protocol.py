from collections.abc import Callable
from typing import Generic, TypeVar

from attrs import define, field

from sghi.idr.client.core.domain import (
    BaseIdentifiableDomainObject,
    BaseNamedDomainObject,
    CleanedData,
    DataSink,
    DataSinkMetadata,
    DataSource,
    DataSourceMetadata,
    ETLProtocol,
    ExtractMetadata,
    ExtractProcessor,
    MetadataConsumer,
    MetadataSupplier,
    RawData,
    UploadMetadata,
    UploadMetadataFactory,
)

# =============================================================================
# TYPES
# =============================================================================

_CD = TypeVar("_CD", bound=CleanedData)
_DM = TypeVar("_DM", bound=DataSourceMetadata)
_DS = TypeVar("_DS", bound=DataSinkMetadata)
_EM = TypeVar("_EM", bound=ExtractMetadata)
_RD = TypeVar("_RD", bound=RawData)
_UM = TypeVar("_UM", bound=UploadMetadata)


# =============================================================================
# CONCRETE ETL PROTOCOL DEFINITION
# =============================================================================


@define(slots=True, order=False)
class SimpleETLProtocol(
    BaseIdentifiableDomainObject,
    BaseNamedDomainObject,
    ETLProtocol[_DM, _EM, _RD, _CD, _UM, _DS],
    Generic[_DM, _EM, _RD, _CD, _UM, _DS],
):
    """A simple implementation of an :class:`ETLProtocol`."""

    _data_sink_factory: Callable[[_DS], DataSink] = field()
    _data_source_factory: Callable[[_DM], DataSource] = field()
    _extract_processor_factory: Callable[
        [],
        ExtractProcessor[_EM, _RD, _CD],
    ] = field()
    _metadata_consumer: MetadataConsumer[_UM] = field()
    _metadata_supplier: MetadataSupplier[_DS, _DM, _EM] = field()
    _upload_metadata_factory: UploadMetadataFactory[_UM, _EM] = field()

    @property
    def data_sink_factory(self) -> Callable[[_DS], DataSink]:
        return self._data_sink_factory

    @property
    def data_source_factory(self) -> Callable[[_DM], DataSource]:
        return self._data_source_factory

    @property
    def extract_processor_factory(
        self,
    ) -> Callable[[], ExtractProcessor[_EM, _RD, _CD]]:
        return self._extract_processor_factory

    @property
    def metadata_consumer(self) -> MetadataConsumer[_UM]:
        return self._metadata_consumer

    @property
    def metadata_supplier(self) -> MetadataSupplier[_DS, _DM, _EM]:
        return self._metadata_supplier

    @property
    def upload_metadata_factory(self) -> UploadMetadataFactory[_UM, _EM]:
        return self._upload_metadata_factory