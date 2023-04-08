from collections.abc import Generator
from typing import Any

import factory

from app.imp.sql_data import (
    SQLDataSource,
    SQLDataSourceType,
    SQLExtractMetadata,
    SQLUploadChunk,
    SQLUploadMetadata,
    SupportedDBVendors,
)
from tests.core.factories import (
    DataSourceFactory,
    DataSourceTypeFactory,
    ExtractMetadataFactory,
    UploadChunkFactory,
    UploadMetadataFactory,
)


class SQLDataSourceFactory(DataSourceFactory):
    """A factory for ``SQLDataSource`` instances."""

    database_name = factory.Sequence(lambda _n: "Database %d" % _n)
    database_vendor = SupportedDBVendors.SQLITE_MEM
    data_source_type = factory.SubFactory(
        "tests.imp.sql_data.factories.SQLDataSourceTypeFactory"
    )

    @factory.post_generation
    def extract_metadata(
        obj: SQLDataSource,  # noqa
        created: bool,
        extracted: SQLDataSource | None,
        **kwargs,
    ) -> None:
        extract_metadata_count: int = kwargs.setdefault(
            "extract_metadata_count", 5
        )
        extract_metadata: Generator[SQLExtractMetadata, Any, Any] = (
            SQLExtractMetadataFactory(data_source=obj)
            for _ in range(extract_metadata_count)
        )
        obj.extract_metadata = {  # noqa
            _extract_meta.id: _extract_meta
            for _extract_meta in extract_metadata
        }

    class Meta:
        model = SQLDataSource

    class Params:
        extract_metadata_count = 5


class SQLDataSourceTypeFactory(DataSourceTypeFactory):
    """A factory for ``SQLDataSourceTypeFactory`` instances."""

    @factory.post_generation
    def data_sources(
        obj: SQLDataSourceType,  # noqa
        created: bool,
        extracted: SQLDataSourceType | None,
        **kwargs,
    ) -> None:
        data_sources_count: int = kwargs.setdefault("data_sources_count", 5)
        data_sources: Generator[SQLDataSource, Any, Any] = (
            SQLDataSourceFactory(data_source_type=obj)
            for _ in range(data_sources_count)
        )
        obj.data_sources = {  # noqa
            _data_source.id: _data_source for _data_source in data_sources
        }

    class Meta:
        model = SQLDataSourceType

    class Params:
        data_sources_count = 5


class SQLExtractMetadataFactory(ExtractMetadataFactory):
    """A factory for ``SQLExtractMetadata`` instances."""

    sql_query = "select 'hello world'"
    applicable_source_versions = tuple()
    data_source = factory.SubFactory(SQLDataSourceFactory)

    class Meta:
        model = SQLExtractMetadata


class SQLUploadChunkFactory(UploadChunkFactory):
    """A factory for ``SQLUploadChunk`` instances."""

    class Meta:
        model = SQLUploadChunk


class SQLUploadMetadataFactory(UploadMetadataFactory):
    """A factory for ``SQLUploadMetadata`` instances."""

    extract_metadata = factory.SubFactory(SQLExtractMetadataFactory)

    class Meta:
        model = SQLUploadMetadata
