from typing import Sequence, Tuple
from unittest import TestCase

from app.core import DataSource, ExtractMetadata
from app.use_cases.run_extraction import (
    DoExtract,
    GroupSiblingExtracts,
    RunDataSourceExtracts,
)
from tests.core.factories import (
    FakeDataSourceFactory,
    FakeExtractMetadataFactory,
)


class TestDoExtract(TestCase):
    """Tests for the :class:`DoExtract` class."""

    def setUp(self) -> None:
        super().setUp()
        self._extract_meta: ExtractMetadata = FakeExtractMetadataFactory()
        self._instance: DoExtract = DoExtract(self._extract_meta)

    def test_execute_return_value(self) -> None:
        """Assert that the ``execute()`` method returns the expected value."""
        result = self._instance.execute(self._extract_meta.data_source)

        assert len(result) == 2
        assert result[0] == self._extract_meta


class TestGroupSiblingExtracts(TestCase):
    """Tests for the :class:`GroupSiblingExtracts` class."""

    def setUp(self) -> None:
        super().setUp()
        self._data_source1: DataSource = FakeDataSourceFactory(id="1")
        self._data_source2: DataSource = FakeDataSourceFactory(id="2")
        self._ds1_extracts: Sequence[ExtractMetadata]
        self._ds1_extracts = tuple(
            FakeExtractMetadataFactory.create_batch(
                size=5, data_source=self._data_source1
            )
        )
        self._ds2_extracts: Sequence[ExtractMetadata]
        self._ds2_extracts = tuple(
            FakeExtractMetadataFactory.create_batch(
                size=7, data_source=self._data_source2
            )
        )
        self._all_extracts: Sequence[ExtractMetadata]
        self._all_extracts = self._ds1_extracts + self._ds2_extracts
        self._instance: GroupSiblingExtracts = GroupSiblingExtracts()

    def test_execute_return_value(self) -> None:
        """Assert that the ``execute()`` method returns the expected value."""
        results = self._instance.execute(self._all_extracts)

        assert results  # Should not be None or empty.
        assert len(results) == 2
        assert results[0][0] == self._data_source1
        assert results[1][0] == self._data_source2
        self.assertTupleEqual(tuple(results[0][1]), tuple(self._ds1_extracts))
        self.assertTupleEqual(tuple(results[1][1]), tuple(self._ds2_extracts))


class TestRunDataSourceExtracts(TestGroupSiblingExtracts):
    """Tests for the :class:`RunDataSourceExtracts` class."""

    def setUp(self) -> None:
        super().setUp()
        self._grouped_extracts: Sequence[
            Tuple[DataSource, Sequence[ExtractMetadata]]
        ] = GroupSiblingExtracts().execute(self._all_extracts)
        self._instance: RunDataSourceExtracts = RunDataSourceExtracts()

    def test_execute_return_value(self) -> None:
        """Assert that the ``execute()`` method returns the expected value."""
        results = self._instance.execute(self._grouped_extracts)

        assert results  # Should not be None or empty.
        assert len(results[0]) == 2
        assert len(results) == len(self._all_extracts)
