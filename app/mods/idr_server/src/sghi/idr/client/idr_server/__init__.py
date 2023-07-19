from collections.abc import Iterable

from sghi.idr.client.common.domain import SimpleETLProtocol
from sghi.idr.client.core.domain import ETLProtocolSupplier
from sghi.idr.client.http import (
    HTTPDataSink,
    HTTPDrainMetadataFactory,
    HTTPMetadataConsumer,
    HTTPMetadataSupplier,
    SimpleHTTPDataSinkMetadata,
)
from sghi.idr.client.sql import (
    PDDataFrame,
    SimpleSQLDatabase,
    SimpleSQLDatabaseDescriptor,
    SimpleSQLQuery,
)

from .domain import *  # noqa: F403
from .domain import (
    IDRServerDataProcessor,
    IDRServerV1APIDrainMetadata,
    ParquetData,
)
from .domain import __all__ as _all_domain
from .lib import *  # noqa: F403
from .lib import __all__ as _all_lib
from .lib import http_transport_factory, idr_server_api_factory

FYJCBSETLProtocol = SimpleETLProtocol[
    SimpleSQLDatabaseDescriptor,
    SimpleSQLQuery,
    PDDataFrame,
    ParquetData,
    IDRServerV1APIDrainMetadata,
    SimpleHTTPDataSinkMetadata,
]


# =============================================================================
# HELPERS
# =============================================================================


def fyj_cbs_etl_protocol_factory() -> FYJCBSETLProtocol:
    return SimpleETLProtocol(
        id="fyj-cbs",  # pyright: ignore
        name="FyJ CBS ETL Protocol",  # pyright: ignore
        description="Fahari ya Jamii, CBS ETL Protocol",  # pyright: ignore
        data_sink_factory=HTTPDataSink.of_data_sink_meta,  # pyright: ignore
        data_source_factory=SimpleSQLDatabase.of_data_source_meta,  # pyright: ignore  # noqa: E501
        data_processor_factory=IDRServerDataProcessor,  # pyright: ignore
        drain_metadata_factory=fyj_cbs_drain_meta_factory(),  # pyright: ignore
        metadata_consumer=fyj_cbs_metadata_consumer_factory(),  # pyright: ignore  # noqa: E501
        metadata_supplier=fyj_cbs_metadata_supplier_factory(),  # pyright: ignore  # noqa: E501
    )


def fyj_cbs_metadata_consumer_factory() -> HTTPMetadataConsumer:
    return HTTPMetadataConsumer(
        name="FyJ IDR Server Metadata Consumer",  # pyright: ignore
        api_dialect=idr_server_api_factory(),  # pyright: ignore
        transport=http_transport_factory(),  # pyright: ignore
    )


def fyj_cbs_metadata_supplier_factory() -> HTTPMetadataSupplier:
    return HTTPMetadataSupplier(
        name="FyJ IDR Server Metadata Supplier",  # pyright: ignore
        api_dialect=idr_server_api_factory(),  # pyright: ignore
        transport=http_transport_factory(),  # pyright: ignore
    )


def fyj_cbs_drain_meta_factory() -> HTTPDrainMetadataFactory:
    return HTTPDrainMetadataFactory(
        api_dialect=idr_server_api_factory(),  # pyright: ignore
        transport=http_transport_factory(),  # pyright: ignore
    )


# =============================================================================
# ETL PROTOCOL SUPPLIERS
# =============================================================================


class IDRServerETLProtocolSupplier(ETLProtocolSupplier):
    def get_protocols(
        self,
    ) -> Iterable[FYJCBSETLProtocol]:
        return (fyj_cbs_etl_protocol_factory(),)


__all__ = [
    "fyj_cbs_etl_protocol_factory",
    "fyj_cbs_metadata_consumer_factory",
    "fyj_cbs_metadata_supplier_factory",
    "fyj_cbs_drain_meta_factory",
]
__all__ += _all_domain  # type: ignore
__all__ += _all_lib  # type: ignore
