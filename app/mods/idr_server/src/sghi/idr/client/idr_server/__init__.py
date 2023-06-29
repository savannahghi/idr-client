from sghi.idr.client.common.domain import SimpleETLProtocol
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


def fyj_cbs_etl_protocol_factory() -> FYJCBSETLProtocol:
    return SimpleETLProtocol(
        id="fyj-cbs",
        name="FYJ CBS ETL Protocol",
        description="Fahari ya Jamii, CBS ETL Protocol",
        data_sink_factory=HTTPDataSink.from_data_sink_meta,
        data_source_factory=SimpleSQLDatabase.from_data_source_meta,
        extract_processor_factory=IDRServerExtractProcessor,
        metadata_consumer=HTTPMetadataConsumer(
            name="FyJ IDR Server Metadata Consumer",  # pyright: ignore
            api_dialect=idr_server_api_factory(),  # pyright: ignore
            transport=http_transport_factory(),  # pyright: ignore
        ),
        metadata_supplier=HTTPMetadataSupplier(  # pyright: ignore
            name="FyJ IDR Server Metadata Supplier",  # pyright: ignore
            api_dialect=idr_server_api_factory(),  # pyright: ignore
            transport=http_transport_factory(),  # pyright: ignore
        ),
        upload_metadata_factory=HTTPUploadMetadataFactory(  # pyright: ignore
            api_dialect=idr_server_api_factory(),  # pyright: ignore
            transport=http_transport_factory(),  # pyright: ignore
        ),
    )


__all__ = ["fyj_cbs_etl_protocol_factory"]
__all__ += _all_domain  # type: ignore
__all__ += _all_lib  # type: ignore
