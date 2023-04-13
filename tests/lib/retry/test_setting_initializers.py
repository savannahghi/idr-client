from unittest import TestCase

import pytest

from app.lib import ImproperlyConfiguredError, RetryInitializer
from app.lib.retry.constants import DEFAULT_RETRY_CONFIG


class TestRetryInitializer(TestCase):
    """Tests for the :class:`RetryInitializer` class."""

    def setUp(self) -> None:
        super().setUp()
        self._instance: RetryInitializer = RetryInitializer()

    def test_execute_return_value_when_no_config_is_provided(self) -> None:
        """
        Assert that the ``execute`` method returns a default configuration
        when one isn't provided.
        """
        assert self._instance.execute(an_input=None) == DEFAULT_RETRY_CONFIG

    def test_execute_when_invalid_config_is_provided(self) -> None:
        """
        Assert that when an invalid config is provided to the ``execute``
        method, the appropriate exception is raised.
        """

        retry_settings = [
            "default_deadline",
            "default_initial_delay",
            "default_maximum_delay",
            "default_multiplicative_factor",
        ]
        with pytest.raises(ImproperlyConfiguredError, match="is invalid"):
            self._instance.execute(an_input=[])  # type: ignore
        for setting in retry_settings:
            with pytest.raises(ImproperlyConfiguredError, match="of float"):
                self._instance.execute({setting: "e"})  # type: ignore
            with pytest.raises(ImproperlyConfiguredError, match="than zero"):
                self._instance.execute({setting: "-0.1"})  # type: ignore

    def test_setting_property_return_value(self) -> None:
        """Assert the the ``setting`` property returns the expected value."""

        assert self._instance.setting == "RETRY"
