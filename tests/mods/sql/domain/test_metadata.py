from typing import TYPE_CHECKING, cast

from sqlalchemy import text

from app.mods.sql import SimpleSQLDatabaseDescriptor, SimpleSQLQuery
from tests import TestCase

from ..factories import (
    SimpleSQLDatabaseDescriptorFactory,
    SimpleSQLQueryFactory,
)

if TYPE_CHECKING:
    from sqlalchemy.sql.elements import TextClause


class TestSimpleSQLDatabaseDescriptor(TestCase):
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
        self._instance1 = cast(
            SimpleSQLQuery,
            SimpleSQLQueryFactory(
                name="Test Query 1",
                description="A test query to extract all x and y.",
                raw_sql_query="SELECT x, y FROM test",
                yield_per=None,
                logging_token="Query One",  # noqa: S106
                isolation_level=None,
            ),
        )
        self._instance2 = cast(
            SimpleSQLQuery,
            SimpleSQLQueryFactory(
                name="Test Query 2",
                description="A test query to extract all y and z.",
                raw_sql_query="SELECT y, z FROM test",
                yield_per=100,
                logging_token=None,
                isolation_level="READ COMMITTED",
            ),
        )

    def test_accessors(self) -> None:
        """Ensure accessors return the expected values."""

        description1: str = "A test query to extract all x and y."
        description2: str = "A test query to extract all y and z."
        clause1: TextClause = text("SELECT x, y FROM test")
        clause2: TextClause = text("SELECT y, z FROM test")
        assert self._instance1.name == "Test Query 1"
        assert self._instance1.description == description1
        assert self._instance1.raw_sql_query == "SELECT x, y FROM test"
        assert self._instance1.yield_per is None
        assert self._instance1.logging_token == "Query One"  # noqa: S105
        assert self._instance1.isolation_level is None
        assert self._instance1.select_clause.compare(clause1)
        assert self._instance2.name == "Test Query 2"
        assert self._instance2.description == description2
        assert self._instance2.raw_sql_query == "SELECT y, z FROM test"
        assert self._instance2.yield_per == 100
        assert self._instance2.logging_token == self._instance2.name
        assert self._instance2.isolation_level == "READ COMMITTED"
        assert self._instance2.select_clause.compare(clause2)
