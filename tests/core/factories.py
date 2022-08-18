import uuid
from typing import Any, Mapping, Sequence, Type

import factory

from app import DataSourceType
from app.core import (
    DataSource,
    ExtractMetadata,
    Task,
    Transport,
    TransportOptions,
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
        self._extract_metadata: Mapping[str, ExtractMetadata] = dict()
        self._is_disposed: bool = False

    @property
    def data_source_type(self) -> DataSourceType:
        return self._data_source_type

    @property
    def extract_metadata(self) -> Mapping[str, "ExtractMetadata"]:
        return self._extract_metadata

    @extract_metadata.setter
    def extract_metadata(
        self, extract_metadata: Mapping[str, ExtractMetadata]
    ) -> None:
        self._extract_metadata = extract_metadata

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed

    def dispose(self) -> None:
        self._is_disposed = True

    def get_extract_task_args(self) -> Any:
        return 0


class FakeDataSourceType(DataSourceType):
    """A fake data source type."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._data_sources: Mapping[str, FakeDataSource] = dict()

    @property
    def code(self) -> str:
        return "mock_data"

    @property
    def data_sources(self) -> Mapping[str, FakeDataSource]:
        return self._data_sources

    @data_sources.setter
    def data_sources(self, data_sources: Mapping[str, FakeDataSource]):
        self._data_sources = data_sources

    @classmethod
    def imp_data_source_klass(cls) -> Type[DataSource]:
        return FakeDataSource

    @classmethod
    def imp_extract_metadata_klass(cls) -> Type[ExtractMetadata]:
        return FakeExtractMetadata


class FakeExtractMetadata(ExtractMetadata[Any, Any]):
    """A fake extract metadata."""

    def __init__(self, **kwargs):
        data_source: DataSource = kwargs.pop("data_source")
        super().__init__(**kwargs)
        self._data_source: DataSource = data_source

    @property
    def data_source(self) -> DataSource:
        return self._data_source

    def to_task(self) -> Task[Any, Any]:
        return self._FakeExtractTask()

    class _FakeExtractTask(Task[Any, Any]):
        """A fake task that doesn't do anything."""

        def execute(self, an_input: Any) -> Any:
            return 0


class FakeTransport(Transport):
    """A fake transport that returns empty results."""

    def __init__(self):
        self._is_closed: bool = False

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
        return tuple()

    def fetch_data_sources(
        self, data_source_type: DataSourceType, **options: TransportOptions
    ) -> Sequence[DataSource]:
        return tuple()


# =============================================================================
# ABSTRACT FACTORIES
# =============================================================================


class AbstractDomainObjectFactory(factory.Factory):
    """The base Test Factory for ``AbstractDomainObject``."""

    class Meta:
        abstract = True


class IdentifiableDomainObjectFactory(AbstractDomainObjectFactory):
    """A base factory for ``IdentifiableDomainObject`` implementations."""

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))

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
    """
    A base factory for ``ExtractMetadata`` implementations.
    """

    name = factory.Sequence(lambda _n: "Extract Metadata %d" % _n)
    description = factory.Faker("sentence")
    preferred_uploads_name = factory.LazyAttribute(
        lambda _o: "%s" % _o.name.lower().replace(" ", "_")
    )

    class Meta:
        abstract = True


# =============================================================================
# FAKE FACTORIES
# =============================================================================


class FakeDataSourceFactory(DataSourceFactory):
    """A factory for creating mock data source instances."""

    name = factory.Sequence(lambda _n: "Fake Data Source %d" % _n)
    data_source_type = factory.SubFactory(
        "tests.core.factories.FakeDataSourceTypeFactory"
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
    """
    A factory for creating fake extract metadata instances.
    """

    name = factory.Sequence(lambda _n: "Fake Extract Metadata %d" % _n)
    description = factory.Faker("sentence")
    preferred_uploads_name = factory.LazyAttribute(
        lambda _o: "%s" % _o.name.lower().replace(" ", "_")
    )
    data_source = factory.SubFactory(FakeDataSource)

    class Meta:
        model = FakeExtractMetadata


class FakeTransportFactory(factory.Factory):
    """
    A factory for creating fake transport instances that return empty results.
    """

    class Meta:
        model = FakeTransport
