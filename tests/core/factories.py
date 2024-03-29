import uuid
from collections.abc import Mapping, Sequence
from typing import Any

import factory

from app import DataSourceType
from app.core import (
    DataSource,
    ExtractMetadata,
    Task,
    Transport,
    TransportOptions,
    UploadChunk,
    UploadMetadata,
)

# =============================================================================
# MOCK CLASSES
# =============================================================================


class FakeDataSource(DataSource):
    """A fake data source."""

    def __init__(self, **kwargs):
        data_source_type: DataSourceType = kwargs.pop("data_source_type")
        super().__init__(**kwargs)
        self._data_source_type: DataSourceType = data_source_type
        self._extract_metadata: Mapping[str, ExtractMetadata] = {}
        self._is_disposed: bool = False

    @property
    def data_source_type(self) -> DataSourceType:
        return self._data_source_type

    @property
    def extract_metadata(self) -> Mapping[str, "ExtractMetadata"]:
        return self._extract_metadata

    @extract_metadata.setter
    def extract_metadata(
        self,
        extract_metadata: Mapping[str, ExtractMetadata],
    ) -> None:
        self._extract_metadata = extract_metadata

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed

    def dispose(self) -> None:
        self._is_disposed = True

    def get_extract_task_args(self) -> Any:  # noqa: ANN401
        return 0


class FakeDataSourceType(DataSourceType):
    """A fake data source type."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._data_sources: Mapping[str, FakeDataSource] = {}

    @property
    def code(self) -> str:
        return "mock_data"

    @property
    def data_sources(self) -> Mapping[str, FakeDataSource]:
        return self._data_sources

    @data_sources.setter
    def data_sources(self, data_sources: Mapping[str, FakeDataSource]) -> None:
        self._data_sources = data_sources

    @classmethod
    def imp_data_source_klass(cls) -> type[DataSource]:
        return FakeDataSource

    @classmethod
    def imp_extract_metadata_klass(cls) -> type[ExtractMetadata]:
        return FakeExtractMetadata

    @classmethod
    def imp_upload_chunk_klass(cls) -> type[UploadChunk]:
        return FakeUploadChunk

    @classmethod
    def imp_upload_metadata_klass(cls) -> type[UploadMetadata]:
        return FakeUploadMetadata


class FakeExtractMetadata(ExtractMetadata[Any, Any]):
    """A fake extract metadata."""

    def __init__(self, **kwargs):
        data_source: DataSource = kwargs.pop("data_source")
        super().__init__(**kwargs)
        self._data_source: DataSource = data_source

    @property
    def data_source(self) -> DataSource:
        return self._data_source

    def get_upload_meta_extra_init_kwargs(self) -> Any:  # noqa: ANN401
        return None

    def to_task(self) -> Task[Any, Any]:
        return self._FakeExtractTask()

    class _FakeExtractTask(Task[Any, Any]):
        """A fake task that doesn't do anything."""

        def execute(self, an_input: Any) -> Any:  # noqa: ANN401
            return 0


class FakeTransport(Transport):
    """A fake transport that returns dummy data."""

    def __init__(
        self,
        is_closed: bool = False,
        fetch_data_source_extracts_count: int = 0,
        fetch_data_sources_count: int = 0,
    ):
        self._is_closed: bool = is_closed
        self._data_sources_count: int = fetch_data_sources_count
        self._extracts_count: int = fetch_data_source_extracts_count

    @property
    def is_disposed(self) -> bool:
        return self._is_closed

    def dispose(self) -> None:
        self._is_closed = True

    def fetch_data_source_extracts(
        self,
        data_source_type: DataSourceType,
        data_source: DataSource,
        **options: TransportOptions,
    ) -> Sequence[ExtractMetadata]:
        return tuple(
            FakeExtractMetadataFactory.create_batch(
                size=self._extracts_count,
                data_source=data_source,
            ),
        )

    def fetch_data_sources(
        self,
        data_source_type: DataSourceType,
        **options: TransportOptions,
    ) -> Sequence[DataSource]:
        return tuple(
            FakeDataSourceFactory.create_batch(
                size=self._data_sources_count,
                data_source_type=data_source_type,
            ),
        )

    def mark_upload_as_complete(
        self,
        upload_metadata: UploadMetadata,
        **options: TransportOptions,
    ) -> None:
        return

    def post_upload_chunk(
        self,
        upload_metadata: UploadMetadata,
        chunk_index: int,
        chunk_content: bytes,
        extra_init_kwargs: Mapping[str, Any] | None = None,
        **options: TransportOptions,
    ) -> UploadChunk:
        return FakeUploadChunkFactory(
            chunk_index=chunk_index,
            chunk_content=chunk_content,
        )

    def post_upload_metadata(
        self,
        extract_metadata: ExtractMetadata,
        content_type: str,
        org_unit_code: str,
        org_unit_name: str,
        extra_init_kwargs: Mapping[str, Any] | None = None,
        **options: TransportOptions,
    ) -> UploadMetadata:
        return FakeUploadMetadataFactory(
            extract_metadata=extract_metadata,
            content_type=content_type,
            org_unit_code=org_unit_code,
            org_unit_name=org_unit_name,
        )


class FakeUploadChunk(UploadChunk):
    """A mock upload chunk implementation."""

    ...


class FakeUploadMetadata(UploadMetadata[Any]):
    """A mock upload metadata implementation."""

    def __init__(self, chunk_count: int = 0, **kwargs):
        extract_metadata: FakeExtractMetadata = kwargs.pop("extract_metadata")
        super().__init__(**kwargs)
        self._chunk_count: int = chunk_count
        self._extract_metadata: FakeExtractMetadata = extract_metadata

    @property
    def extract_metadata(self) -> FakeExtractMetadata:
        return self._extract_metadata

    def to_task(self) -> Task[Any, Sequence[bytes]]:
        return self._FakeUploadTask(chunk_count=self._chunk_count)

    @classmethod
    def get_content_type(cls) -> str:
        return "text/csv"

    class _FakeUploadTask(Task[Any, Sequence[bytes]]):
        """A fake task that returns a sequence of random bytes."""

        def __init__(self, chunk_count: int):
            self._chunk_count: int = chunk_count

        def execute(self, an_input: Any) -> Sequence[bytes]:  # noqa: ANN401
            return tuple(
                f"Bla bla bla {_index} ...".encode()
                for _index in range(self._chunk_count)
            )


# =============================================================================
# ABSTRACT FACTORIES
# =============================================================================


class AbstractDomainObjectFactory(factory.Factory):
    """The base Test Factory for ``AbstractDomainObject``."""

    class Meta:
        abstract = True


class IdentifiableDomainObjectFactory(AbstractDomainObjectFactory):
    """A base factory for ``IdentifiableDomainObject`` implementations."""

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))  # noqa: A003

    class Meta:
        abstract = True


class DataSourceFactory(IdentifiableDomainObjectFactory):
    """A base factory for ``DataSource`` implementations."""

    name = factory.Sequence(lambda _n: "Data Source %d" % _n)
    description = factory.Faker("sentence")

    class Meta:
        abstract = True


class DataSourceTypeFactory(AbstractDomainObjectFactory):
    """A base factory for ``DataSourceType`` implementations."""

    description = factory.Faker("sentence")

    class Meta:
        abstract = True


class ExtractMetadataFactory(IdentifiableDomainObjectFactory):
    """A base factory for ``ExtractMetadata`` implementations."""

    name = factory.Sequence(lambda _n: "Extract Metadata %d" % _n)
    description = factory.Faker("sentence")
    preferred_uploads_name = factory.LazyAttribute(
        lambda _o: "%s" % _o.name.lower().replace(" ", "_"),
    )

    class Meta:
        abstract = True


class UploadChunkFactory(IdentifiableDomainObjectFactory):
    """A base factory for ``UploadChunk`` implementations."""

    chunk_index = factory.Sequence(lambda _n: _n)
    chunk_content = factory.Faker("csv")

    class Meta:
        abstract = True


class UploadMetadataFactory(IdentifiableDomainObjectFactory):
    """A base factory for ``UploadMetadata`` implementations."""

    org_unit_code = factory.Sequence(lambda _n: "%1234d" % _n)
    org_unit_name = factory.Sequence(lambda _n: "Facility %d" % _n)
    content_type = "text/csv"

    class Meta:
        abstract = True


# =============================================================================
# FAKE FACTORIES
# =============================================================================


class FakeDataSourceFactory(DataSourceFactory):
    """A factory for creating mock data source instances."""

    name = factory.Sequence(lambda _n: "Fake Data Source %d" % _n)
    data_source_type = factory.SubFactory(
        "tests.core.factories.FakeDataSourceTypeFactory",
    )

    class Meta:
        model = FakeDataSource


class FakeDataSourceTypeFactory(DataSourceTypeFactory):
    """A factory for creating mock data source instances."""

    name = factory.Sequence(lambda _n: "Fake Data Source Type %d" % _n)
    description = factory.Faker("sentence")

    class Meta:
        model = FakeDataSourceType


class FakeExtractMetadataFactory(ExtractMetadataFactory):
    """A factory for creating fake extract metadata instances."""

    name = factory.Sequence(lambda _n: "Fake Extract Metadata %d" % _n)
    description = factory.Faker("sentence")
    preferred_uploads_name = factory.LazyAttribute(
        lambda _o: "%s" % _o.name.lower().replace(" ", "_"),
    )
    data_source = factory.SubFactory(FakeDataSourceFactory)

    class Meta:
        model = FakeExtractMetadata


class FakeTransportFactory(factory.Factory):
    """
    A factory for creating fake transport instances that return empty results.
    """

    is_closed: bool = False
    fetch_data_source_extracts_count: int = 0
    fetch_data_sources_count: int = 0

    class Meta:
        model = FakeTransport


class FakeUploadChunkFactory(UploadChunkFactory):
    """A factory for creating fake upload chunk instances."""

    chunk_content = b"Bla bla bla ..."

    class Meta:
        model = FakeUploadChunk


class FakeUploadMetadataFactory(UploadMetadataFactory):
    """A factory for creating fake upload metadata instances."""

    chunk_count = 0
    extract_metadata = factory.SubFactory(FakeExtractMetadataFactory)

    class Meta:
        model = FakeUploadMetadata
