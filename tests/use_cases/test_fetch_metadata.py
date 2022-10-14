from collections.abc import Sequence
from unittest import TestCase

from app.core import DataSource, DataSourceType, Transport
from app.use_cases.fetch_metadata import (
    DoFetchDataSources,
    DoFetchExtractMetadata,
    FetchDataSources,
    FetchExtractMetadata,
)
from tests.core.factories import (
    FakeDataSourceFactory,
    FakeDataSourceTypeFactory,
    FakeTransportFactory,
)


class TestDoFetchDataSources(TestCase):
    """Tests for the :class:`DoFetchDataSources` class."""

    def setUp(self) -> None:
        super().setUp()
        self._data_source_type: DataSourceType = FakeDataSourceTypeFactory()
        self._instance: DoFetchDataSources = DoFetchDataSources(
            data_source_type=self._data_source_type
        )
        self._transport: Transport = FakeTransportFactory(
            fetch_data_sources_count=5
        )

    def test_execute_return_value(self) -> None:
        """Assert that the ``execute()`` method returns the expected value."""
        data_sources = self._instance.execute(self._transport)

        assert len(data_sources) == 5

    def test_execute_side_effects(self) -> None:
        """
        Assert that the ``execute()`` method results in the ``data_sources``
        property of the target *data source type* being set.
        """
        self._instance.execute(self._transport)

        assert len(self._data_source_type.data_sources) == 5


class TestDoFetchExtractMetadata(TestCase):
    """Tests for the :class:`DoFetchExtractMetadata` class."""

    def setUp(self) -> None:
        super().setUp()
        self._data_source: DataSource = FakeDataSourceFactory()
        self._instance: DoFetchExtractMetadata = DoFetchExtractMetadata(
            data_source=self._data_source
        )
        self._transport: Transport = FakeTransportFactory(
            fetch_data_source_extracts_count=5
        )

    def test_execute_return_value(self) -> None:
        """Assert that the ``execute()`` method returns the expected value."""
        extracts = self._instance.execute(self._transport)

        assert len(extracts) == 5

    def test_execute_side_effects(self) -> None:
        """
        Assert that the ``execute()`` method results in the
        ``extract_metadata`` property of the target *data source* being set.
        """
        self._instance.execute(self._transport)

        assert len(self._data_source.extract_metadata) == 5


class TestFetchDataSources(TestCase):
    """Tests for the :class:`FetchDataSources` class."""

    def setUp(self) -> None:
        super().setUp()
        self._max_data_source_types: int = 5
        self._max_data_sources: int = 3
        self._data_source_types: Sequence[DataSourceType]
        self._data_source_types = tuple(
            FakeDataSourceTypeFactory.create_batch(
                size=self._max_data_source_types
            )
        )
        self._transport: Transport = FakeTransportFactory(
            fetch_data_sources_count=self._max_data_sources
        )
        self._instance: FetchDataSources = FetchDataSources(
            transport=self._transport
        )

    def test_execute_return_value(self) -> None:
        """Assert that the ``execute()`` method returns the expected value."""
        data_sources = self._instance.execute(self._data_source_types)

        assert (
            len(data_sources)
            == self._max_data_sources * self._max_data_source_types
        )

    def test_execute_side_effects(self) -> None:
        """
        Assert that the ``execute()`` method results in the ``data_sources``
        property of each target *data source type* being set.
        """
        self._instance.execute(self._data_source_types)
        for _ds_type in self._data_source_types:
            assert len(_ds_type.data_sources) == self._max_data_sources


class TestFetchExtractMetadata(TestCase):
    """Tests for the :class:`FetchExtractMetadata` class."""

    def setUp(self) -> None:
        super().setUp()
        self._max_data_sources: int = 4
        self._max_extracts: int = 7
        self._data_sources: Sequence[DataSource]
        self._data_sources = tuple(
            FakeDataSourceFactory.create_batch(size=self._max_data_sources)
        )
        self._transport: Transport = FakeTransportFactory(
            fetch_data_source_extracts_count=self._max_extracts
        )
        self._instance: FetchExtractMetadata = FetchExtractMetadata(
            transport=self._transport
        )

    def test_execute_return_value(self) -> None:
        """Assert that the ``execute()`` method returns the expected value."""
        extracts = self._instance.execute(self._data_sources)

        assert len(extracts) == self._max_data_sources * self._max_extracts

    def test_execute_side_effects(self) -> None:
        """
        Assert that the ``execute()`` method results in the
        ``extract_metadata`` property of each target *data source* being set.
        """
        self._instance.execute(self._data_sources)
        for _data_source in self._data_sources:
            assert len(_data_source.extract_metadata) == self._max_extracts
