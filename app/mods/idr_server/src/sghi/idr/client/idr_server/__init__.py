from collections.abc import Iterable

from sghi.idr.client.common.domain import SimpleETLProtocol
from sghi.idr.client.core.domain import ETLProtocolSupplier
from sghi.idr.client.http import (
    HTTPDataSink,
    HTTPMetadataConsumer,
    HTTPMetadataSupplier,
    HTTPUploadMetadataFactory,
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
    IDRServerExtractProcessor,
    IDRServerV1APIUploadMetadata,
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
    IDRServerV1APIUploadMetadata,
    SimpleHTTPDataSinkMetadata,
]


# =============================================================================
# HELPERS
# =============================================================================


def fyj_cbs_etl_protocol_factory() -> FYJCBSETLProtocol:
    return SimpleETLProtocol(
        id="fyj-cbs",
        name="FyJ CBS ETL Protocol",
        description="Fahari ya Jamii, CBS ETL Protocol",
        data_sink_factory=HTTPDataSink.from_data_sink_meta,
        data_source_factory=SimpleSQLDatabase.from_data_source_meta,
        extract_processor_factory=IDRServerExtractProcessor,
        metadata_consumer=fyj_cbs_metadata_consumer_factory(),
        metadata_supplier=fyj_cbs_metadata_supplier_factory(),
        upload_metadata_factory=fyj_cbs_upload_meta_factory(),
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


def fyj_cbs_upload_meta_factory() -> HTTPUploadMetadataFactory:
    return HTTPUploadMetadataFactory(
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
    "fyj_cbs_upload_meta_factory",
]
__all__ += _all_domain  # type: ignore
__all__ += _all_lib  # type: ignore
