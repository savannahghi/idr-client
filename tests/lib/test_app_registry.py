from typing import Dict, Mapping
from unittest import TestCase

from app.core import DataSourceType
from app.imp.sql_data import SQLDataSourceType
from app.lib import AppRegistry


class TestAppRegistry(TestCase):
    """Tests for the :class:`AppRegistry` class."""

    def setUp(self) -> None:
        super().setUp()
        self._app_registry: AppRegistry = AppRegistry()
        self._data_source_types: Mapping[str, DataSourceType] = {
            "sql_data": SQLDataSourceType()
        }

    def test_immutability_of_data_source_types_property_content(self) -> None:
        """
        Assert that once set, the contents of the ``data_source_types``
        property cannot be modified by modifying the original mapping.
        """
        data_source_types: Dict[str, DataSourceType] = {
            **self._data_source_types
        }
        self._app_registry.data_source_types = data_source_types

        data_source_types["sql_data_2"] = SQLDataSourceType()

        assert "sql_data_2" not in self._app_registry.data_source_types
        assert len(self._app_registry.data_source_types) == 1

    def test_retrieval_of_data_source_types(self) -> None:
        """
        Assert that the ``data_source_types`` property returns the expected
        value.
        """
        self._app_registry.data_source_types = self._data_source_types
        self.assertDictEqual(
            self._app_registry.data_source_types, self._data_source_types
        )

        self._app_registry.data_source_types = {}
        self.assertDictEqual(self._app_registry.data_source_types, {})
