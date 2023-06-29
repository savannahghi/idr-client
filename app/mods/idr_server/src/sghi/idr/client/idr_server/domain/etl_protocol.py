from collections.abc import Iterable, Mapping
from functools import cache
from typing import TYPE_CHECKING

import sghi.idr.client.core as app
from sghi.idr.client.common.domain import SimpleETLProtocol
from sghi.idr.client.http import (
    HTTPDataSink,
    HTTPMetadataConsumer,
    HTTPMetadataSupplier,
    HTTPTransport,
    HTTPUploadMetadataFactory,
    SimpleHTTPDataSinkMetadata,
)
from sghi.idr.client.sql import (
    PDDataFrame,
    SimpleSQLDatabase,
    SimpleSQLDatabaseDescriptor,
    SimpleSQLQuery,
)

from .metadata import IDRServerV1APIUploadMetadata
from .operations import IDRServerExtractProcessor, ParquetData

if TYPE_CHECKING:
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
    http_transport_settings: Mapping[str, int | float]
    http_transport_settings = app.settings.get("HTTP_TRANSPORT", {})
    return HTTPTransport(
        auth_api_dialect=_idr_server_api_factory(),  # pyright: ignore
        connect_timeout=http_transport_settings.get(  # pyright: ignore
            "connect_timeout",
            60,
        ),
        read_timeout=http_transport_settings.get(  # pyright: ignore
            "read_timeout",
            60,
        ),
    )


@cache
def _idr_server_api_factory() -> "IDRServerV1API":
    from ..lib import IDRServerV1API

    idr_server_settings: Mapping[str, str] = app.settings.IDR_SERVER_SETTINGS
    return IDRServerV1API(
        server_url=idr_server_settings["host"],  # pyright: ignore
        username=idr_server_settings["username"],  # pyright: ignore
        password=idr_server_settings["password"],  # pyright: ignore
    )


def _metadata_sinks_supplier() -> (
    Iterable[HTTPMetadataConsumer[IDRServerV1APIUploadMetadata]]
):
    return (
        HTTPMetadataConsumer(
            name="FyJ IDR Server Metadata Sink",  # pyright: ignore
            api_dialect=_idr_server_api_factory(),  # pyright: ignore
            transport=_http_transport_factory(),  # pyright: ignore
        ),
    )


def _metadata_sources_supplier() -> (
    Iterable[
        HTTPMetadataSupplier[
            SimpleHTTPDataSinkMetadata,
            SimpleSQLDatabaseDescriptor,
            SimpleSQLQuery,
        ]
    ]
):
    return (
        HTTPMetadataSupplier(  # pyright: ignore
            name="FyJ IDR Server Metadata Source",  # pyright: ignore
            api_dialect=_idr_server_api_factory(),  # pyright: ignore
            transport=_http_transport_factory(),  # pyright: ignore
        ),
    )


def fyj_cbs_etl_protocol_factory() -> FYJCBSETLProtocol:
    return SimpleETLProtocol(
        id="fyj-cbs",
        name="FYJ CBS ETL Protocol",
        description="Fahari ya Jamii, CBS ETL Protocol",
        data_sink_factory=HTTPDataSink.from_data_sink_meta,
        data_source_factory=SimpleSQLDatabase.from_data_source_meta,
        extract_processor_factory=IDRServerExtractProcessor,
        metadata_sinks=_metadata_sinks_supplier(),
        metadata_sources=_metadata_sources_supplier(),
        upload_metadata_factory=HTTPUploadMetadataFactory(  # pyright: ignore
            api_dialect=_idr_server_api_factory(),  # pyright: ignore
            transport=_http_transport_factory(),  # pyright: ignore
        ),
    )
