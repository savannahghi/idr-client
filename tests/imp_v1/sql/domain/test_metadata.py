from typing import cast

from app.imp_v1.sql import SimpleSQLDatabaseDescriptor, SimpleSQLQuery
from tests import TestCase

from ..factories import SimpleSQLDatabaseDescriptorFactory


class TestSimpleSQLDatabase(TestCase):
    """Tests for the :class:`SimpleSQLDatabaseDescriptor` class."""

    def setUp(self) -> None:
        super().setUp()
        self._instance1 = cast(
            SimpleSQLDatabaseDescriptor,
            SimpleSQLDatabaseDescriptorFactory(
                name="Test Database 1",
                description="An SQL Lite in memory database for testing.",
                database_url="sqlite+pysqlite:///:memory:",
                logging_name="Test DB 1 Logger",
            ),
        )
        self._instance2 = cast(
            SimpleSQLDatabaseDescriptor,
            SimpleSQLDatabaseDescriptorFactory(
                name="Test Database 2",
                description="An SQL Lite in memory database for testing.",
                database_url="sqlite+pysqlite:///:memory:",
                isolation_level="READ COMMITTED",
            ),
        )

    def test_accessors(self) -> None:
        """Ensure accessors return the expected values."""

        description: str = "An SQL Lite in memory database for testing."
        assert self._instance1.database_url == "sqlite+pysqlite:///:memory:"
        assert self._instance1.description == description
        assert self._instance1.name == "Test Database 1"
        assert self._instance1.logging_name == "Test DB 1 Logger"
        assert self._instance1.isolation_level == "REPEATABLE READ"
        assert self._instance2.database_url == "sqlite+pysqlite:///:memory:"
        assert self._instance2.description == description
        assert self._instance2.name == "Test Database 2"
        assert self._instance2.logging_name == "Test Database 2"
        assert self._instance2.isolation_level == "READ COMMITTED"


class TestSimpleSQLQuery(TestCase):
    """Tests of the :class:`SimpleSQLQuery` class."""

    def setUp(self) -> None:
        super().setUp()
        self._instance: SimpleSQLQuery
