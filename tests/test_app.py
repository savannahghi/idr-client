from typing import Any, Dict, Mapping
from unittest import TestCase

import pytest

import app
from app.lib import ImproperlyConfiguredError, SettingInitializer

# =============================================================================
# HELPERS
# =============================================================================


def _test_config_factory() -> Mapping[str, Any]:
    return {
        "SETTINGS_INITIALIZERS": [
            "tests.test_app.FakeDataSourceTypesConfigInitializer"
        ],
        "SUPPORTED_DATA_SOURCE_TYPES": ["app.imp.sql_data.SQLDataSourceType"],
    }


class FakeDataSourceTypesConfigInitializer(SettingInitializer):
    """A fake settings initializers for testing."""

    @property
    def setting(self) -> str:
        return "SUPPORTED_DATA_SOURCE_TYPES"

    def execute(self, an_input: Any) -> Any:
        # Do nothing
        return an_input


# =============================================================================
# TESTS
# =============================================================================


def test_app_globals_are_set_after_successful_setup() -> None:
    assert app.settings is None
    assert app.registry is None

    # After setup, globals should be not None.
    app.setup(initial_settings=_test_config_factory())

    assert app.settings is not None
    assert app.registry is not None


class TestAppModule(TestCase):
    """Tests for the app module."""

    def setUp(self) -> None:
        super().setUp()
        self._default_config: Dict[str, Any] = dict()
        self._some_state: int = 0

    def test_valid_config_is_successful(self) -> None:
        """Assert that a valid config will be executed successfully."""
        app.setup(initial_settings=self._default_config)

    def test_invalid_settings_initializers_config_causes_error(self) -> None:
        """
        Assert that invalid dotted paths or dotted paths to non
        :config:`setting initializers <SettingInitializer>` on the
        *SETTINGS_INITIALIZERS* setting results in errors.
        """
        config1: Dict[str, Any] = dict(self._default_config)
        config2: Dict[str, Any] = dict(self._default_config)

        config1["SETTINGS_INITIALIZERS"] = ["invalid_dotted_path"]
        config2["SETTINGS_INITIALIZERS"] = ["app.core.Task"]
        with pytest.raises(ImproperlyConfiguredError):
            app.setup(initial_settings=config1)

        # Not an initializer
        with pytest.raises(ImproperlyConfiguredError):
            app.setup(initial_settings=config2)

    def test_invalid_data_source_types_config_causes_error(self) -> None:
        """
        Assert that invalid dotted paths or dotted paths to non
        :config:`data source types <DataSourceType>` on the
        *SUPPORTED_DATA_SOURCE_TYPES* setting result in errors.
        """
        config1: Dict[str, Any] = dict(self._default_config)
        config2: Dict[str, Any] = dict(self._default_config)

        config1["SUPPORTED_DATA_SOURCE_TYPES"] = ["invalid_dotted_path"]
        config2["SUPPORTED_DATA_SOURCE_TYPES"] = ["app.core.Task"]
        with pytest.raises(ImproperlyConfiguredError):
            app.setup(initial_settings=config1)

        # Not a data source type
        with pytest.raises(ImproperlyConfiguredError):
            app.setup(initial_settings=config2)
