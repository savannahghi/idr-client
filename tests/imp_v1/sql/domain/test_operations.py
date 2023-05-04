from typing import cast

from app.imp_v1.sql.domain import (
    SimpleSQLDatabase,
    SimpleSQLDatabaseDescriptor,
)
from tests import TestCase

from ..factories import (
    SimpleSQLDatabaseDescriptorFactory,
    SimpleSQLDatabaseFactory,
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

    def test_dispose_works_as_expected(self) -> None:
        """Assert that the :meth:`SimpleSQLDatabase.dispose` method disposes
        the `Engine` object and that the object is in correct status once
        the method returns.
        """

        assert not self._instance1.is_disposed

        self._instance1.dispose()
        assert self._instance1.is_disposed

    def test_multiple_invocations_of_dispose(self) -> None:
        """Assert that the :meth:`SimpleSQLDatabase.dispose` method can be
        called multiple times without raising any errors.
        """

        self._instance1.dispose()
        self._instance1.dispose()
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

        db: SimpleSQLDatabase = cast(
            SimpleSQLDatabase,
            SimpleSQLDatabaseFactory(
                add_sample_data=True,
                add_sample_data__size=1000,
            ),
        )
        db.start_extraction()
