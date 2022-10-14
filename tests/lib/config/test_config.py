from collections.abc import Mapping, Sequence
from typing import Any
from unittest import TestCase

import pytest

from app.lib import Config, MissingSettingError, SettingInitializer

# =============================================================================
# HELPERS
# =============================================================================


class _Setting1Initializer(SettingInitializer):
    """
    A simple initializer that takes a setting raw value and returns it's string
    representation.
    """

    @property
    def setting(self) -> str:
        return "SETTING_1"

    def execute(self, an_input: Any) -> str:
        return str(an_input)


class _Setting2Initializer(SettingInitializer):
    """
    A simple initializer that takes an integer setting value and returns the
    value + 1 or 0 if the the value is None.
    """

    @property
    def setting(self) -> str:
        return "SETTING_2"

    def execute(self, an_input: int) -> int:
        return an_input + 1 if an_input is not None else 0


# =============================================================================
# TEST CASES
# =============================================================================


class TestConfig(TestCase):
    """Tests for the :class:`Config` class."""

    def setUp(self) -> None:
        super().setUp()
        # Settings
        self._setting_1_value: int = 0
        self._setting_2_value: int = 0
        self._settings: Mapping[str, Any] = {
            "SETTING_1": self._setting_1_value,
            "SETTING_2": self._setting_2_value,
        }

        # Setting Initializers
        self._setting_1_initializer = _Setting1Initializer()
        self._setting_2_initializer = _Setting2Initializer()
        self._initializers: Sequence[SettingInitializer] = (
            self._setting_1_initializer,
            self._setting_2_initializer,
        )

    def test_initializers_are_run(self) -> None:
        """
        Assert that initializers are run and the settings value are updated.
        """
        config = Config(
            settings=self._settings, settings_initializers=self._initializers
        )

        assert config.SETTING_1 == "0"
        assert config.SETTING_2 == 1

    def test_initializers_can_set_default_values(self) -> None:
        """
        Assert that when a setting is not provided but an initializer for the
        setting exists, the value returned after running the initializer
        becomes the new value of the setting.
        """
        self._settings = {"SETTING_1": self._setting_1_value}
        config = Config(
            settings=self._settings, settings_initializers=self._initializers
        )

        assert config.SETTING_1 == "0"
        assert config.SETTING_2 == 0  # SETTING_2 now has a default

    def test_missing_settings_retrieval_using_dot_notation(self) -> None:
        """
        Assert that retrieval of missing settings using the dot notation
        results in a :class:`MissingSettingError` being raised.
        """
        config = Config(settings={})
        with pytest.raises(MissingSettingError) as exp:
            _: Any = config.INVALID_SETTING

        assert exp.value.setting == "INVALID_SETTING"

    def test_settings_retrieval_using_get_method(self) -> None:
        """
        Assert that retrieval of settings using the method returns the
        expected setting or the default value when the setting is missing.
        """
        self._settings = {
            **self._settings,
            "weird::setting::name": "some value",
        }
        config = Config(
            settings=self._settings, settings_initializers=self._initializers
        )

        assert config.get("SETTING_1") == "0"
        assert config.get("weird::setting::name") == "some value"
        assert config.get("MISSING", default="default") == "default"
        assert config.get("MISSING") is None

    def test_settings_without_initializers_are_not_modified(self) -> None:
        """
        Assert that settings without initializers are not modified when
        initializers run and are returned as is.
        """
        setting_3_value: str = "Do not modify!"
        self._settings = {**self._settings, "SETTING_3": setting_3_value}
        config = Config(
            settings=self._settings, settings_initializers=self._initializers
        )

        assert config.SETTING_3 == setting_3_value
