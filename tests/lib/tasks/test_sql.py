from unittest import TestCase
from unittest.mock import patch

import pytest
from pandas import DataFrame
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DisconnectionError

from app.core import ExtractionOperationError
from app.lib import SimpleSQLSelect


class TestSimpleSQLSelect(TestCase):
    """Tests for the ``SimpleSQLSelect`` task."""

    def setUp(self) -> None:
        super().setUp()
        self._engine: Engine = create_engine("sqlite+pysqlite:///:memory:")
        self._sql_select: SimpleSQLSelect = SimpleSQLSelect(
            sql_query="select 'hello world'"
        )

    def tearDown(self) -> None:
        super().tearDown()
        self._engine.dispose()

    def test_execute(self) -> None:
        """
        Assert that a ``SimpleSQLSelect`` task can connect and pull data from
        a database.
        """
        with self._engine.connect() as connection:
            result: DataFrame = self._sql_select.execute(connection=connection)

            assert result is not None

    def test_execute_errors(self) -> None:
        """
        Assert that when an error occurs during a call to the ``execute``
        method, the error is handled correctly and wrapped inside in a
        ``ExtractionOperationError``.
        """
        with patch("pandas.read_sql", autospec=True) as r:
            r.side_effect = DisconnectionError
            with pytest.raises(ExtractionOperationError) as exc_info:
                with self._engine.connect() as connection:
                    self._sql_select.execute(connection=connection)

            assert isinstance(exc_info.value.__cause__, DisconnectionError)
