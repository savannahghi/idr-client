from typing import Any, Dict
from unittest import TestCase
from unittest.mock import patch

import pytest

import app
from app.lib import ImproperlyConfiguredError
from app.lib.transports.http import HTTPTransport, http_transport_factory
from tests.factories import config_factory


class TestHTTPModule(TestCase):
    """Test the http module."""

    def setUp(self) -> None:
        super().setUp()
        self._app_config: Dict[str, Any] = config_factory()
        self._api_dialect_config_key: str = "default_http_api_dialect_factory"
        self._http_config_key: str = "HTTP_TRANSPORT"
        self._http_config: Dict[str, Any] = {
            self._api_dialect_config_key: (
                "tests.lib.transports.http.factories.FakeHTTPAPIDialectFactory"
            ),
            "connect_timeout": 10,  # 10 seconds
            "read_timeout": 60,  # 1 minute
        }
        self._app_config[self._http_config_key] = self._http_config

    def test_http_transport_factory_with_valid_settings_works(self) -> None:
        """
        Assert that a http transport factory returns the expected value with
        a valid config.
        """
        app.setup(initial_settings=self._app_config)
        transport: HTTPTransport = http_transport_factory()

        assert transport is not None

    def test_http_transport_factory_with_invalid_settings_fails(self) -> None:
        """
        Assert that an invalid config results in the expected errors being
        raised.
        """
        config1: Dict[str, Any] = dict(self._app_config)
        del config1[self._http_config_key]
        with patch("app.settings", config1):
            with pytest.raises(ImproperlyConfiguredError):
                http_transport_factory()

        config2: Dict[str, Any] = dict(self._app_config)
        config2[self._http_config_key] = 3
        with patch("app.settings", config2):
            with pytest.raises(ImproperlyConfiguredError):
                http_transport_factory()

        config3: Dict[str, Any] = dict(self._app_config)
        del config3[self._http_config_key][self._api_dialect_config_key]
        with patch("app.settings", config3):
            with pytest.raises(ImproperlyConfiguredError):
                http_transport_factory()

        config4: Dict[str, Any] = dict(self._app_config)
        config4[self._http_config_key][self._api_dialect_config_key] = None
        with patch("app.settings", config4):
            with pytest.raises(ImproperlyConfiguredError):
                http_transport_factory()

        config5: Dict[str, Any] = dict(self._app_config)
        config5[self._http_config_key][self._api_dialect_config_key] = "12345"
        with patch("app.settings", config5):
            with pytest.raises(ImproperlyConfiguredError):
                http_transport_factory()
