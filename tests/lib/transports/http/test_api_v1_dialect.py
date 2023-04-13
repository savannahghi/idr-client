import json
from typing import TYPE_CHECKING, Any
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
    FakeExtractMetadataFactory,
    FakeUploadChunkFactory,
    FakeUploadMetadataFactory,
    UploadMetadata,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


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
        },
    }
    with patch("app.settings", config):
        api_dialect = idr_server_api_v1_dialect_factory()
        assert api_dialect is not None


def test_idr_server_api_v1_dialect_factor_fails_with_invalid_config() -> None:
    """
    Assert that the ``idr_server_api_dialect_factory()`` raises the expected
    errors when the app has missing settings or is incorrectly configured.
    """

    with patch("app.settings", {}), pytest.raises(ImproperlyConfiguredError):
        idr_server_api_v1_dialect_factory()

    with (
        patch("app.settings", {"REMOTE_SERVER": []}),
        pytest.raises(ImproperlyConfiguredError),
    ):
        idr_server_api_v1_dialect_factory()

    with (
        patch("app.settings", {"REMOTE_SERVER": {}}),
        pytest.raises(ImproperlyConfiguredError),
    ):
        idr_server_api_v1_dialect_factory()

    with (
        patch("app.settings", {"REMOTE_SERVER": {"host": "http://test.com"}}),
        pytest.raises(ImproperlyConfiguredError),
    ):
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

        assert self._api_dialect.response_to_auth(
            json.dumps({"token": token}).encode("ascii"),
        ) == {"Authorization": "Token %s" % token}

    def test_fetch_data_source_extracts_return_value(self) -> None:
        """
        Assert that the ``fetch_data_source_extracts()`` method returns the
        expected value.
        """
        data_source = FakeDataSourceFactory()
        data_source_type = FakeDataSourceTypeFactory()
        request_params = self._api_dialect.fetch_data_source_extracts(
            data_source_type=data_source_type,
            data_source=data_source,
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
        data_source_type = FakeDataSourceTypeFactory()
        response_content = {"results": []}

        assert (
            list(
                self._api_dialect.response_to_data_source_extracts(
                    json.dumps(response_content).encode("ascii"),
                    data_source_type=data_source_type,
                    data_source=data_source,
                ),
            )
            == []
        )

    def test_fetch_data_sources_return_value(self) -> None:
        """
        Assert that the ``fetch_data_sources()`` method returns the expected
        value.
        """
        data_source_type = FakeDataSourceTypeFactory()
        request_params = self._api_dialect.fetch_data_sources(
            data_source_type=data_source_type,
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

        assert (
            list(
                self._api_dialect.response_to_data_sources(
                    json.dumps(response_content).encode("ascii"),
                    data_source_type=data_source_type,
                ),
            )
            == []
        )

    def test_mark_upload_as_complete_return_value(self) -> None:
        """
        Assert that the ``mark_upload_as_complete`` method returns the expected
        value.
        """
        upload_meta = FakeUploadMetadataFactory()
        request_params = self._api_dialect.mark_upload_as_complete(
            upload_metadata=upload_meta,
        )

        assert request_params  # Should not be None or empty.
        assert request_params["expected_http_status_code"] == 200
        assert request_params["method"].upper() == "PATCH"

    def test_post_upload_chunk_return_value(self) -> None:
        """
        Assert that the ``post_upload_chunk`` method returns the expected
        value.
        """
        upload_meta = FakeUploadMetadataFactory()
        chunk_index = 0
        chunk_content = b"Bla bla bla ..."
        request_params = self._api_dialect.post_upload_chunk(
            upload_metadata=upload_meta,
            chunk_index=chunk_index,
            chunk_content=chunk_content,
        )

        assert request_params  # Should not be None or empty.
        assert request_params.get("data")  # Should not be None or empty.
        assert request_params["expected_http_status_code"] == 201
        assert request_params["method"].upper() == "POST"

    def test_response_to_upload_chunk_return_value(self) -> None:
        """
        Assert that the ``response_to_upload_chunk`` method returns the
        expected value.
        """
        source_upload_chunk = FakeUploadChunkFactory(chunk_content="")
        upload_meta = FakeUploadMetadataFactory()
        response_content = {
            "id": source_upload_chunk.id,
            "chunk_index": source_upload_chunk.chunk_index,
            "chunk_content": source_upload_chunk.chunk_content,
        }
        upload_chunk = self._api_dialect.response_to_upload_chunk(
            json.dumps(response_content).encode("ascii"),
            upload_metadata=upload_meta,
        )

        assert upload_chunk is not None
        assert upload_chunk.id == source_upload_chunk.id
        assert upload_chunk.chunk_index == source_upload_chunk.chunk_index

    def test_post_upload_metadata_return_value(self) -> None:
        """
        Assert that the ``post_upload_metadata`` method returns the expected
        value.
        """
        content_type = "application/json"
        extract_meta = FakeExtractMetadataFactory()
        org_unit_code = "12345"
        org_unit_name = "Test Facility"
        request_params = self._api_dialect.post_upload_metadata(
            extract_metadata=extract_meta,
            content_type=content_type,
            org_unit_code=org_unit_code,
            org_unit_name=org_unit_name,
        )

        assert request_params  # Should not be None or empty.
        assert request_params.get("data")  # Should not be None or empty.
        assert request_params["expected_http_status_code"] == 201
        assert request_params["method"].upper() == "POST"

    def test_response_to_upload_metadata_return_value(self) -> None:
        """
        Assert that the ``response_to_upload_metadata`` method returns the
        expected value.
        """
        source_upload_meta: UploadMetadata = FakeUploadMetadataFactory()
        response_content = {
            "id": source_upload_meta.id,
            "extract_metadata": source_upload_meta.extract_metadata.id,
            "org_unit_code": source_upload_meta.org_unit_code,
            "org_unit_name": source_upload_meta.org_unit_name,
            "content_type": source_upload_meta.content_type,
        }

        upload_meta = self._api_dialect.response_to_upload_metadata(
            json.dumps(response_content).encode("ascii"),
            extract_metadata=source_upload_meta.extract_metadata,
        )

        assert upload_meta is not None
        assert upload_meta.id == source_upload_meta.id
        assert (
            upload_meta.extract_metadata == source_upload_meta.extract_metadata
        )
        assert upload_meta.org_unit_code == source_upload_meta.org_unit_code
        assert upload_meta.org_unit_name == source_upload_meta.org_unit_name
        assert upload_meta.content_type == source_upload_meta.content_type
