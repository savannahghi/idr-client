from collections.abc import Iterable
from functools import cache

from app import settings
from app.imp_v1.common.domain import SimpleETLProtocol
from app.imp_v1.http import (
    HTTPDataSink,
    HTTPMetadataSink,
    HTTPMetadataSource,
    HTTPTransport,
    HTTPUploadMetadataFactory,
    SimpleHTTPDataSinkMetadata,
)
from app.imp_v1.sql import (
    PDDataFrame,
    SimpleSQLDatabase,
    SimpleSQLDatabaseDescriptor,
    SimpleSQLQuery,
)

from ..domain import IDRServerV1APIUploadMetadata, ParquetData
from ..lib import IDRServerV1API

FYJCBSETLProtocol = SimpleETLProtocol[
    SimpleSQLDatabaseDescriptor,
    SimpleSQLQuery,
    PDDataFrame,
    ParquetData,
    IDRServerV1APIUploadMetadata,
    SimpleHTTPDataSinkMetadata,
]


def _http_transport_factory() -> HTTPTransport:
    return HTTPTransport(
        auth_api_dialect=_idr_server_api_factory(),
        connect_timeout=settings.HTTP_TRANSPORT.get("connect_timeout", 60),
        read_timeout=settings.HTTP_TRANSPORT.get("read_timeout", 60),
    )


@cache
def _idr_server_api_factory() -> IDRServerV1API:
    return IDRServerV1API(
        server_url=settings.REMOTE_SERVER["host"],
        username=settings.REMOTE_SERVER["username"],
        password=settings.REMOTE_SERVER["password"],
    )


def _metadata_sinks_supplier() -> (
    Iterable[HTTPMetadataSink[IDRServerV1APIUploadMetadata]]
):
    return (
        HTTPMetadataSink(
            name="FyJ IDR Server",
            api_dialect=_idr_server_api_factory(),
            transport=_http_transport_factory(),
        ),
    )


def _metadata_sources_supplier() -> (
    Iterable[
        HTTPMetadataSource[
            SimpleHTTPDataSinkMetadata,
            SimpleSQLDatabaseDescriptor,
            SimpleSQLQuery,
        ]
    ]
):
    return (
        HTTPMetadataSource(
            name="FyJ IDR Server",
            api_dialect=_idr_server_api_factory(),
            transport=_http_transport_factory(),
        ),
    )


def fyj_cbs_etl_protocol_factory() -> FYJCBSETLProtocol:
    return SimpleETLProtocol(
        id="fyj-cbs",
        name="FYJ CBS ETL Protocol",
        description="Fahari ya Jamii, CBS ETL Protocol",
        data_sink_factory=HTTPDataSink.from_data_sink_meta,
        data_source_factory=SimpleSQLDatabase.from_data_source_meta,
        metadata_sinks=_metadata_sinks_supplier(),
        metadata_sources=_metadata_sources_supplier(),
        upload_metadata_factory=HTTPUploadMetadataFactory(
            api_dialect=_idr_server_api_factory(),
            transport=_http_transport_factory(),
        ),
    )
