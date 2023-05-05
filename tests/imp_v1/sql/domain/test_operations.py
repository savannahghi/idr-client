from typing import cast

from app.imp_v1.sql.domain import (
    SimpleSQLDatabase,
    SimpleSQLDatabaseDescriptor,
    SimpleSQLDataSourceStream,
    SimpleSQLQuery,
)
from tests import TestCase

from ..factories import (
    SimpleSQLDatabaseDescriptorFactory,
    SimpleSQLDatabaseFactory,
    SimpleSQLQueryFactory,
)


class TestSimpleSQLDatabase(TestCase):
    """Tests for the :class:`SimpleSQLDatabase`. class."""

    def setUp(self) -> None:
        super().setUp()
        self._instance1: SimpleSQLDatabase = cast(
            SimpleSQLDatabase,
            SimpleSQLDatabaseFactory(
                name="Test Database 1",
                description="The first test database.",
            ),
        )
        self._instance2: SimpleSQLDatabase = cast(
            SimpleSQLDatabase,
            SimpleSQLDatabaseFactory(
                name="Test Database 2",
                description="The second test database.",
            ),
        )
        self.addCleanup(self._instance1.dispose)
        self.addCleanup(self._instance2.dispose)

    def test_accessors(self) -> None:
        """Ensure accessors return the expected values."""

        assert self._instance1.name == "Test Database 1"
        assert self._instance1.description == "The first test database."
        assert self._instance1.engine is not None
        assert not self._instance1.is_disposed
        assert self._instance2.name == "Test Database 2"
        assert self._instance2.description == "The second test database."
        assert self._instance2.engine is not None
        assert not self._instance2.is_disposed

    def test_dispose_method(self) -> None:
        """Assert that the :meth:`SimpleSQLDatabase.dispose` method disposes
        the `Engine` object and that the object is in correct status once
        the method returns.
        """

        assert not self._instance1.is_disposed

        self._instance1.dispose()
        assert self._instance1.is_disposed

    def test_from_data_source_meta_class_factory_method(self) -> None:
        """Assert that the :meth:`SimpleSQLDatabase.from_data_source_meta`
        creates and returns an instance in the expected state.
        """

        db_descriptor: SimpleSQLDatabaseDescriptor = cast(
            SimpleSQLDatabaseDescriptor,
            SimpleSQLDatabaseDescriptorFactory(
                name="Test Database 1",
                description="An SQLite in memory database for testing.",
                database_url="sqlite+pysqlite:///:memory:",
                isolation_level="READ UNCOMMITTED",
            ),
        )
        db: SimpleSQLDatabase = SimpleSQLDatabase.from_data_source_meta(
            data_source_meta=db_descriptor,
        )

        assert db is not None
        assert db.name == "Test Database 1"
        assert db.description == "An SQLite in memory database for testing."
        assert (
            db.engine.url.render_as_string() == "sqlite+pysqlite:///:memory:"
        )
        assert not db.is_disposed

        db.dispose()

    def test_multiple_invocations_of_dispose(self) -> None:
        """Assert that the :meth:`SimpleSQLDatabase.dispose` method can be
        called multiple times without raising any errors.
        """

        self._instance1.dispose()
        self._instance1.dispose()
        self._instance1.dispose()
        assert self._instance1.is_disposed

    def test_of_sqlite_in_memory_factory_method(self) -> None:
        """Assert that the :meth:`SimpleSQLDatabase.of_sqlite_in_memory` class
        method creates and returns an instance in the expected state.
        """

        db1: SimpleSQLDatabase = SimpleSQLDatabase.of_sqlite_in_memory()
        db2: SimpleSQLDatabase = SimpleSQLDatabase.of_sqlite_in_memory(
            name="Test DB",
            description="A Test database.",
        )

        assert db1.name == "SQLite in Memory"
        assert db1.description == "An SQLite in memory database."
        assert (
            db1.engine.url.render_as_string() == "sqlite+pysqlite:///:memory:"
        )
        assert not db1.is_disposed
        assert db2.name == "Test DB"
        assert db2.description == "A Test database."
        assert (
            db2.engine.url.render_as_string() == "sqlite+pysqlite:///:memory:"
        )
        assert not db2.is_disposed

        db1.dispose()
        db2.dispose()

    def test_start_extraction_method_return_value(self) -> None:
        """Assert that the :meth:`SimpleSQLDatabase.start_extraction` method
        returns the expected value.
        """

        query1: SimpleSQLQuery = cast(
            SimpleSQLQuery,
            SimpleSQLQueryFactory(
                name="Get all XY",
                description="Get all x & y from 'some_table'.",
                raw_sql_query="SELECT x, y FROM some_table",
            ),
        )
        query2: SimpleSQLQuery = cast(
            SimpleSQLQuery,
            SimpleSQLQueryFactory(
                name="Get all YZ",
                description="Get all y & z from 'some_table'",
                raw_sql_query="SELECT y, z FROM some_table",
            ),
        )
        db: SimpleSQLDatabase = cast(
            SimpleSQLDatabase,
            SimpleSQLDatabaseFactory(
                add_sample_data=True,
                add_sample_data__size=1000,
            ),
        )
        stream1: SimpleSQLDataSourceStream = db.start_extraction(query1)
        stream2: SimpleSQLDataSourceStream = db.start_extraction(query2)

        assert stream1 is not None
        assert isinstance(stream1, SimpleSQLDataSourceStream)
        assert stream2 is not None
        assert isinstance(stream2, SimpleSQLDataSourceStream)

        stream1.dispose()
        stream2.dispose()
        db.dispose()


class TestSimpleSQLDataSourceStream(TestCase):
    """Tests for the :class:`SimpleSQLDataSourceStream` class."""

    def setUp(self) -> None:
        super().setUp()
        self.query1: SimpleSQLQuery = cast(
            SimpleSQLQuery,
            SimpleSQLQueryFactory(
                name="Get all XY",
                description="Get all x & y from 'some_table'.",
                raw_sql_query="SELECT x, y FROM some_table",
                yield_per=10_000,
            ),
        )
        self.query2: SimpleSQLQuery = cast(
            SimpleSQLQuery,
            SimpleSQLQueryFactory(
                name="Get all YZ",
                description="Get all y & z from 'some_table'",
                raw_sql_query="SELECT y, z FROM some_table",
                yield_per=100,
            ),
        )
        self.db: SimpleSQLDatabase = cast(
            SimpleSQLDatabase,
            SimpleSQLDatabaseFactory(
                add_sample_data=True,
                add_sample_data__size=1000,
            ),
        )
        self.addCleanup(self.db.dispose)

    def test_accessors(self) -> None:
        """Ensure accessors reflect the current status of a
        :class:`SimpleSQLDataSourceStream` instance.
        """
        stream: SimpleSQLDataSourceStream = self.db.start_extraction(
            self.query1,
        )

        assert stream.data_source is self.db
        assert not stream.is_disposed

        stream.dispose()
        assert stream.is_disposed

    def test_dispose_method(self) -> None:
        """Assert that the :meth:`SimpleSQLDataSourceStream.dispose` method
        leaves an instance in the expected state.
        """

        stream1: SimpleSQLDataSourceStream = self.db.start_extraction(
            self.query1,
        )
        stream2: SimpleSQLDataSourceStream = self.db.start_extraction(
            self.query2,
        )

        stream1.dispose()
        stream2.dispose()

        assert stream1.is_disposed
        assert stream2.is_disposed

    def test_extract_method_implementation(self) -> None:
        """Assert that the :meth:`SimpleSQLDataSourceStream.extract` method
        implementation results in the expected behaviour.

        That is, that the method will return db rows in batches based on the
        :attr:`SimpleSQLQuery.yield_per` attribute.
        """

        stream1_extractions_count: int = 0
        stream2_extractions_count: int = 0

        stream1: SimpleSQLDataSourceStream
        stream2: SimpleSQLDataSourceStream
        with self.db.start_extraction(self.query1) as stream1:
            for data, progress in stream1:
                assert len(data.content) <= self.query1.yield_per
                assert progress == -1
                stream1_extractions_count += 1

        with self.db.start_extraction(self.query2) as stream2:
            for data, progress in stream2:
                assert len(data.content) <= self.query2.yield_per
                assert progress == -1
                stream2_extractions_count += 1

        assert stream1.is_disposed
        assert stream1_extractions_count == 1
        assert stream2.is_disposed
        assert stream2_extractions_count == 10

    def test_multiple_invocations_of_dispose(self) -> None:
        """Assert that the :meth:`SimpleSQLDataSourceStream.dispose` method
        can be called multiple times without raising any errors.
        """

        stream: SimpleSQLDataSourceStream = self.db.start_extraction(
            self.query2,
        )

        stream.dispose()
        stream.dispose()
        stream.dispose()
        stream.dispose()

        assert stream.is_disposed
