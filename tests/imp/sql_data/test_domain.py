import os
from collections.abc import Mapping, Sequence
from typing import Any
from unittest import TestCase
from unittest.mock import patch

import pytest
from pandas import DataFrame
from sqlalchemy.engine import Connection
from sqlalchemy.exc import DisconnectionError

from app.imp.sql_data import (
    SQLDataError,
    SQLDataExtractionOperationError,
    SQLDataSource,
    SQLDataSourceDisposedError,
    SQLDataSourceType,
    SQLExtractMetadata,
    SQLUploadChunk,
    SQLUploadMetadata,
    SupportedDBVendors,
)
from app.lib import Config, ImproperlyConfiguredError

from .factories import (
    SQLDataSourceFactory,
    SQLDataSourceTypeFactory,
    SQLExtractMetadataFactory,
    SQLUploadMetadataFactory,
)


class TestSQLDataSource(TestCase):
    """Tests for the :class:`SQLDataSource` class."""

    def setUp(self) -> None:
        super().setUp()
        self._data_source: SQLDataSource = SQLDataSourceFactory.build()
        self._extract_meta_1: SQLExtractMetadata = SQLExtractMetadataFactory()
        self._extract_meta_2: SQLExtractMetadata = SQLExtractMetadataFactory(
            sql_query="select 'Bonjour le monde'"
        )
        self._data_source.extract_metadata = {
            "1": self._extract_meta_1,
            "2": self._extract_meta_2,
        }

    def tearDown(self) -> None:
        super().tearDown()
        self._data_source.dispose()

    def test_a_disposed_data_source_raises_expected_errors(self) -> None:
        """
        Assert that a disposed data source raises
        ``SQLDataSourceDisposedError`` on attempted usage.
        """
        with pytest.raises(
            SQLDataSourceDisposedError, match="Data source is disposed."
        ):
            self._data_source.get_extract_task_args()

    def test_accessors(self) -> None:
        """Assert that accessors return the expected values."""

        self.assertDictEqual(
            self._data_source.extract_metadata,
            {"1": self._extract_meta_1, "2": self._extract_meta_2},
        )
        # This should remain true until after `self.connect_to_db()` is called.
        assert self._data_source.is_disposed
        assert self._data_source.data_source_type is not None

    def test_connect_to_db(self) -> None:
        """Assert that the ``connect_to_db()`` method works as expected."""

        self._data_source.connect_to_db()

        assert not self._data_source.is_disposed

    def test_get_extract_task_args_errors(self) -> None:
        """
        Assert that when an error occurs during a call to
        ``get_extract_task_args()`` method, the error is handled correctly
        and wrapped inside in a ``SQLDataExtractionOperationError``.
        """
        with patch("sqlalchemy.engine.Engine.connect", autospec=True) as c:
            c.side_effect = DisconnectionError
            with pytest.raises(SQLDataExtractionOperationError) as exc_info:
                with self._data_source as ds:
                    ds.get_extract_task_args()

            assert isinstance(exc_info.value.__cause__, DisconnectionError)

    def test_get_extract_task_args_return_value(self) -> None:
        """
        Assert that the ``get_extract_task_args()`` returns the expected value.
        """
        config: Config = Config(settings={"RETRY": {"enable_retries": False}})
        with patch("app.settings", config):
            self._data_source.connect_to_db()
            connection: Connection = self._data_source.get_extract_task_args()
            with connection:
                assert connection is not None

    def test_load_mysql_config_with_valid_config(self) -> None:
        """
        Assert that the MySQL config can be loaded when a valid config is
        given.
        """
        config: Mapping[str, Any] = {
            "MYSQL_DB_INSTANCE": {
                "host": os.environ["MYSQL_TEST_DB_HOST"],
                "port": os.environ["MYSQL_TEST_DB_PORT"],
                "username": os.environ["MYSQL_TEST_DB_USERNAME"],
                "password": os.environ["MYSQL_TEST_DB_PASSWORD"],
            },
            "RETRY": {"enable_retries": False},
        }
        self._data_source.database_name = os.environ["MYSQL_TEST_DB_NAME"]
        self._data_source.database_vendor = SupportedDBVendors.MYSQL

        with patch("app.settings", config):
            self._data_source.connect_to_db()
            assert not self._data_source.is_disposed
            with self._data_source.get_extract_task_args() as connection:
                assert connection is not None

    def test_load_mysql_config_with_invalid_config(self) -> None:
        """
        Assert that the expected exceptions are raised when given an invalid
        MySQL config.
        """
        config1: Mapping[str, Any] = {"RETRY": {"enable_retries": False}}
        config2: Mapping[str, Any] = {
            "MYSQL_DB_INSTANCE": 3,
            "RETRY": {"enable_retries": False},
        }
        config3: Mapping[str, Any] = {"MYSQL_DB_INSTANCE": {}}
        config4: Mapping[str, Any] = {
            "MYSQL_DB_INSTANCE": {
                "host": "localhost",
                "port": "not_an_int",
                "username": "mysql_user",
                "password": "very_strong_password",
            },
            "RETRY": {"enable_retries": False},
        }
        config5: Mapping[str, Any] = {
            "MYSQL_DB_INSTANCE": {
                "host": "localhost",
                "port": -23,  # Negative port
                "username": "mysql_user",
                "password": "very_strong_password",
            },
            "RETRY": {"enable_retries": False},
        }
        config6: Mapping[str, Any] = {
            "MYSQL_DB_INSTANCE": {
                "host": "localhost",
                "port": 70000,  # Port larger than 65535
                "username": "mysql_user",
                "password": "very_strong_password",
            },
            "RETRY": {"enable_retries": False},
        }

        self._data_source.database_vendor = SupportedDBVendors.MYSQL
        with patch("app.settings", config1):
            with pytest.raises(
                ImproperlyConfiguredError, match="is missing or is not valid."
            ):
                self._data_source.connect_to_db()

        with patch("app.settings", config2):
            with pytest.raises(
                ImproperlyConfiguredError, match="is missing or is not valid."
            ):
                self._data_source.connect_to_db()

        with patch("app.settings", config3):
            with pytest.raises(
                ImproperlyConfiguredError, match="is missing in"
            ):
                self._data_source.connect_to_db()
        for _conf in (config4, config5, config6):
            with patch("app.settings", _conf):
                with pytest.raises(
                    ImproperlyConfiguredError, match="is not a valid port."
                ):
                    self._data_source.connect_to_db()

    def test_object_initialization_from_a_mapping(self) -> None:
        """
        Assert that ``SQLDataSource.of_mapping`` initializers and returns an
        ``SQLDataSource`` instance.
        """
        mapping: Mapping[str, Any] = {
            "id": "1234567890",
            "name": "SQL Data Source",
            "description": "Bla bla bla",
            "database_name": "test_db",
            "database_vendor": SupportedDBVendors.SQLITE_MEM,
            "data_source_type": SQLDataSourceTypeFactory(),
        }
        data_source: SQLDataSource = SQLDataSource.of_mapping(mapping)

        self.assertDictEqual(data_source.extract_metadata, {})
        assert data_source is not None
        assert data_source.id == mapping["id"]
        assert data_source.name == mapping["name"]
        assert data_source.description == mapping["description"]
        assert data_source.database_name == mapping["database_name"]

    def test_sql_data_source_as_a_context_manager(self) -> None:
        """Assert that ``SQLDataSource`` can be used as a context manager."""

        config: Config = Config(settings={"RETRY": {"enable_retries": False}})
        with patch("app.settings", config):
            with self._data_source:
                # This should work without raising any errors as using an
                # SQLDataSource as a context manager should automatically
                # result connect_to_db() being called.
                with self._data_source.get_extract_task_args() as connection:
                    assert connection is not None

    def test_sql_data_source_context_manager_nesting_is_disallowed(
        self,
    ) -> None:  # noqa
        """
        Assert that nesting of ``SQLDataSource`` as a context manager is a
        programming error.
        """

        with self._data_source:
            with pytest.raises(SQLDataError, match="Incorrect usage"):
                with self._data_source:
                    ...


class TestSQLDataSourceType(TestCase):
    """Tests for the :class:`TestSQLDataSourceType` class."""

    def setUp(self) -> None:
        super().setUp()
        self._data_source_type: SQLDataSourceType = SQLDataSourceTypeFactory()

    def test_accessors(self) -> None:
        """Assert that accessors return the expected value."""

        assert self._data_source_type.code == "sql_data"
        assert len(self._data_source_type.data_sources) == 5
        assert self._data_source_type.imp_data_source_klass() == SQLDataSource
        assert (
            self._data_source_type.imp_extract_metadata_klass()
            == SQLExtractMetadata
        )  # noqa
        assert (
            self._data_source_type.imp_upload_chunk_klass() == SQLUploadChunk
        )
        assert (
            self._data_source_type.imp_upload_metadata_klass()
            == SQLUploadMetadata
        )


class TestSQLExtractMetadata(TestCase):
    """Test for the :class:`SQLExtractMetadata` class."""

    def setUp(self) -> None:
        super().setUp()
        self._extract_meta: SQLExtractMetadata = SQLExtractMetadataFactory()

    def test_accessors(self) -> None:
        """Assert that accessors return the expected value."""

        task = self._extract_meta.to_task()
        assert task is not None
        assert self._extract_meta.data_source is not None


class TestSQLUploadMetadata(TestCase):
    """Test for the :class:`SQLUploadMetadata` class."""

    def setUp(self) -> None:
        super().setUp()
        self._upload_meta: SQLUploadMetadata = SQLUploadMetadataFactory()

    def test_accessors(self) -> None:
        """Assert that accessors return the expected value."""

        content_type = "application/vnd.apache-parquet"
        assert self._upload_meta.extract_metadata is not None
        assert isinstance(
            self._upload_meta.extract_metadata, SQLExtractMetadata
        )
        assert self._upload_meta.get_content_type() == content_type
        assert self._upload_meta.to_task() is not None

    def test_to_task(self) -> None:
        """
        Assert that the ``SQLUploadMetadata.to_task()`` method returns a task
        with the expected implementation.
        """

        extract_meta: SQLExtractMetadata = self._upload_meta.extract_metadata
        data_source: SQLDataSource = extract_meta.data_source
        with data_source:
            extracted_data: DataFrame = extract_meta.to_task().execute(
                data_source.get_extract_task_args()
            )

        upload_task = self._upload_meta.to_task()
        processed_extract: Sequence[bytes] = upload_task.execute(
            extracted_data
        )

        assert len(processed_extract) > 0
        assert isinstance(processed_extract[0], bytes)
