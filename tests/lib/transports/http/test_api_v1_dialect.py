import json
from typing import Any, Mapping
from unittest import TestCase
from unittest.mock import patch

import pytest

from app.lib.config import ImproperlyConfiguredError
from app.lib.transports.http import (
    IDRServerAPIv1,
    idr_server_api_v1_dialect_factory,
)
from tests.core.factories import (
    FakeDataSourceFactory,
    FakeDataSourceTypeFactory,
)


def test_idr_server_api_v1_dialect_factory_results_on_valid_config() -> None:
    """
    Assert that the ``idr_server_api_v1_dialect_factory()`` method returns
    expected value(s) when the app is correctly configured.
    """
    config: Mapping[str, Any] = {
        "REMOTE_SERVER": {
            "host": "http://test.example.com",
            "username": "admin",
            "password": "pa$$word",
        }
    }
    with patch("app.settings", config):
        api_dialect = idr_server_api_v1_dialect_factory()
        assert api_dialect is not None


def test_idr_server_api_v1_dialect_factor_fails_with_invalid_config() -> None:
    """
    Assert that the ``idr_server_api_dialect_factory()`` raises the expected
    errors when the app has missing settings or is incorrectly configured.
    """

    with patch("app.settings", {}):
        with pytest.raises(ImproperlyConfiguredError):
            idr_server_api_v1_dialect_factory()

    with patch("app.settings", {"REMOTE_SERVER": []}):
        with pytest.raises(ImproperlyConfiguredError):
            idr_server_api_v1_dialect_factory()

    with patch("app.settings", {"REMOTE_SERVER": {}}):
        with pytest.raises(ImproperlyConfiguredError):
            idr_server_api_v1_dialect_factory()

    with patch("app.settings", {"REMOTE_SERVER": {"host": "http://test.com"}}):
        with pytest.raises(ImproperlyConfiguredError):
            idr_server_api_v1_dialect_factory()


class TestIDRServerAPIv1(TestCase):
    """Tests for the :class:`IDRServerAPIv1` class."""

    def setUp(self) -> None:
        super().setUp()
        self._host: str = "http://test.example.com"
        self._username: str = "user1"
        self._password: str = "some_user"
        self._api_dialect: IDRServerAPIv1 = IDRServerAPIv1(
            server_url=self._host,
            username=self._username,
            password=self._password,
        )

    def test_auth_trigger_statuses_property_return_value(self) -> None:
        """
        Assert that the ``auth_trigger_status`` property returns the expected
        value.
        """
        assert 401 in self._api_dialect.auth_trigger_statuses

    def test_authenticate_method_return_value(self) -> None:
        """
        Assert that the ``authenticate()`` method returns the expected value.
        """
        request_params = self._api_dialect.authenticate()

        assert request_params  # Should not be None or empty.
        assert request_params["expected_http_status_code"] == 200
        assert request_params["method"].upper() == "POST"
        assert request_params["url"] == "%s/api/auth/login/" % self._host

    def test_response_to_auth_return_value(self) -> None:
        """
        Assert that the ``response_to_auth()`` method returns the expected
        value.
        """
        token: str = "a_very_secure_token!!@@"

        self.assertDictEqual(
            self._api_dialect.response_to_auth(
                json.dumps({"token": token}).encode("ascii")
            ),
            {"Authorization": "Token %s" % token},
        )

    def test_fetch_data_source_extracts_return_value(self) -> None:
        """
        Assert that the ``fetch_data_source_extracts()`` method returns the
        expected value.
        """
        data_source = FakeDataSourceFactory()
        request_params = self._api_dialect.fetch_data_source_extracts(
            data_source=data_source
        )

        assert request_params  # Should not be None or empty.
        assert request_params["expected_http_status_code"] == 200
        assert request_params["method"].upper() == "GET"

    def test_response_to_data_source_extracts_return_value(self) -> None:
        """
        Assert that the ``response_to_data_source_extracts`` method returns
        the expected value.
        """
        data_source = FakeDataSourceFactory()
        response_content = {"results": []}

        self.assertDictEqual(
            self._api_dialect.response_to_data_source_extracts(
                json.dumps(response_content).encode("ascii"),
                data_source=data_source,
            ),
            {},
        )

    def test_fetch_data_sources_return_value(self) -> None:
        """
        Assert that the ``fetch_data_sources()`` method returns the expected
        value.
        """
        data_source_type = FakeDataSourceTypeFactory()
        request_params = self._api_dialect.fetch_data_sources(
            data_source_type=data_source_type
        )

        assert request_params  # Should not be None or empty.
        assert request_params["expected_http_status_code"] == 200
        assert request_params["method"].upper() == "GET"

    def test_response_to_data_sources_return_value(self) -> None:
        """
        Assert that the ``response_to_data_sources`` method returns the
        expected value.
        """
        data_source_type = FakeDataSourceTypeFactory()
        response_content = {"results": []}

        self.assertDictEqual(
            self._api_dialect.response_to_data_sources(
                json.dumps(response_content).encode("ascii"),
                data_source_type=data_source_type,
            ),
            {},
        )
