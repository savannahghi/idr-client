import uuid
from typing import Mapping

import factory

from app import DataSourceType
from app.core import DataSource, ExtractMetadata, Transport, TransportOptions

# =============================================================================
# MOCK CLASSES
# =============================================================================


class _FakeDataSource(DataSource):
    """A fake data source."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._extract_metadata: Mapping[str, ExtractMetadata] = dict()

    @property
    def extract_metadata(self) -> Mapping[str, "ExtractMetadata"]:
        return self._extract_metadata

    @extract_metadata.setter
    def extract_metadata(
        self, extract_metadata: Mapping[str, ExtractMetadata]
    ) -> None:
        self._extract_metadata = extract_metadata


class _FakeDataSourceType(DataSourceType[_FakeDataSource]):
    """A fake data source type."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._data_sources: Mapping[str, _FakeDataSource] = dict()

    @property
    def code(self) -> str:
        return "mock_data"

    @property
    def data_sources(self) -> Mapping[str, _FakeDataSource]:
        return self._data_sources

    @data_sources.setter
    def data_sources(self, data_sources: Mapping[str, _FakeDataSource]):
        self._data_sources = data_sources


class _FakeExtractMetadata(ExtractMetadata[_FakeDataSource]):
    """A fake extract metadata."""


class _FakeTransport(Transport):
    """A fake transport that returns empty results."""

    def close(self) -> None:
        pass

    def fetch_data_source_extracts(
        self, data_source: DataSource, **options: TransportOptions
    ) -> Mapping[str, ExtractMetadata]:
        return dict()

    def fetch_data_sources(
        self, data_source_type: DataSourceType, **options: TransportOptions
    ) -> Mapping[str, DataSource]:
        return dict()


# =============================================================================
# FACTORIES
# =============================================================================


class AbstractDomainObjectFactory(factory.Factory):
    """The base Test Factory for AbstractObject."""

    class Meta:
        abstract = True


class FakeDataSourceFactory(AbstractDomainObjectFactory):
    """A factory for creating mock data source instances."""

    class Meta:
        model = _FakeDataSource

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda _n: "Fake Data Source %d" % _n)
    description = factory.Faker("sentence")


class FakeDataSourceTypeFactory(AbstractDomainObjectFactory):
    """A factory for creating mock data source instances."""

    name = factory.Sequence(lambda _n: "Fake Data Source Type %d" % _n)
    description = factory.Faker("sentence")

    class Meta:
        model = _FakeDataSourceType


class FakeExtractMetadataFactory(AbstractDomainObjectFactory):
    """
    A factory for creating fake extract metadata instances.
    """

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda _n: "Fake Extract Metadata %d" % _n)
    description = factory.Faker("sentence")
    preferred_uploads_name = factory.LazyAttribute(
        lambda _o: "%s" % _o.name.lower().replace(" ", "_")
    )

    class Meta:
        model = _FakeExtractMetadata


class FakeTransportFactory(AbstractDomainObjectFactory):
    """
    A factory for creating fake transport instances that return empty results.
    """

    class Meta:
        model = _FakeTransport
