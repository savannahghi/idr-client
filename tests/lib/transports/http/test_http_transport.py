from unittest.mock import patch

import pytest
from requests.exceptions import ChunkedEncodingError, ConnectionError

from app.core import TransportClosedError, TransportError
from app.lib.transports.http import HTTPAPIDialect, HTTPTransport
from tests import TestCase
from tests.core.factories import (
    FakeDataSourceFactory,
    FakeDataSourceTypeFactory,
    FakeExtractMetadataFactory,
    FakeUploadMetadataFactory,
)
from tests.lib.transports.http.factories import FakeHTTPAPIDialectFactory

# =============================================================================
# MOCKS
# =============================================================================


class _FakeResponse:
    """A fake ``requests.models.Response`` for testing."""

    status_code: int = 200
    content: bytes = b""
    text: str = ""


# =============================================================================
# TESTS
# =============================================================================


class TestHTTPTransport(TestCase):
    """Tests for the :class:`HTTPTransport` class."""

    def setUp(self) -> None:
        super().setUp()
        self._api_dialect: HTTPAPIDialect = FakeHTTPAPIDialectFactory()
        self._transport: HTTPTransport = HTTPTransport(
            api_dialect=self._api_dialect,
            connect_timeout=10,
            read_timeout=10,
        )

    def tearDown(self) -> None:
        self._transport.dispose()

    def test_an_api_dialect_is_required_at_instantiation(self) -> None:
        """
        Assert that the `api_dialect` parameter is a required parameter
        during the ``HTTPTransport`` class instantiation.
        """
        with pytest.raises(ValueError, match='"api_dialect" MUST be'):
            HTTPTransport(api_dialect=None)  # type: ignore

    def test_dispose_returns_cleanly(self) -> None:
        """Assert that the ``dispose()`` method returns cleanly."""
        self._transport.dispose()

        assert self._transport.is_disposed

    def test_a_disposed_transport_raises_expected_errors(self) -> None:
        """
        Assert that a disposed Transport instance raises
        ``TransportClosedError`` on attempted usage.
        """
        data_source = FakeDataSourceFactory()
        data_source_type = FakeDataSourceTypeFactory()
        extract_meta = FakeExtractMetadataFactory()
        upload_meta = FakeUploadMetadataFactory()
        self._transport.dispose()
        with patch("requests.sessions.Session.request", autospec=True) as s:
            s.return_value = self._mock_response_factory()
            with pytest.raises(TransportClosedError):
                self._transport.fetch_data_sources(
                    data_source_type=data_source_type,
                )
            with pytest.raises(TransportClosedError):
                self._transport.fetch_data_source_extracts(
                    data_source_type=data_source_type,
                    data_source=data_source,
                )
            with pytest.raises(TransportClosedError):
                self._transport.mark_upload_as_complete(
                    upload_metadata=upload_meta,
                )

            s.return_value = self._mock_response_factory(status_code=201)
            with pytest.raises(TransportClosedError):
                self._transport.post_upload_chunk(
                    upload_metadata=upload_meta,
                    chunk_content=b"Bla bla bla ...",
                    chunk_index=0,
                )
            with pytest.raises(TransportClosedError):
                self._transport.post_upload_metadata(
                    extract_metadata=extract_meta,
                    content_type="application/json",
                    org_unit_code="12345",
                    org_unit_name="Test Facility",
                )

    def test_fetch_data_source_extracts_returns_expected_value(self) -> None:
        """
        Assert that the ``fetch_data_source_extracts()`` method returns the
        expected value.
        """
        data_source = FakeDataSourceFactory()
        data_source_type = FakeDataSourceTypeFactory()
        with patch("requests.sessions.Session.request", autospec=True) as s:
            s.return_value = self._mock_response_factory()
            results = self._transport.fetch_data_source_extracts(
                data_source_type=data_source_type,
                data_source=data_source,
            )
            assert list(results) == []

    def test_fetch_data_sources_returns_expected_value(self) -> None:
        """
        Assert that the ``fetch_data_sources()`` method returns the expected
        value.
        """
        data_source_type = FakeDataSourceTypeFactory()
        with patch("requests.sessions.Session.request", autospec=True) as s:
            s.return_value = self._mock_response_factory()
            results = self._transport.fetch_data_sources(data_source_type)
            assert list(results) == []

    def test_mark_upload_as_complete_exits_cleanly_on_valid_data(self) -> None:
        """
        Assert that the ``mark_upload_as_complete()`` method returns without
        raising any errors when given the correct data.
        """
        upload_meta = FakeUploadMetadataFactory()
        with patch("requests.sessions.Session.request", autospec=True) as s:
            s.return_value = self._mock_response_factory()
            self._transport.mark_upload_as_complete(
                upload_metadata=upload_meta,
            )

    def test_post_upload_chunk_returns_expected_value(self) -> None:
        """
        Assert that the ``post_upload_chunk`` method returns the expected
        value.
        """
        upload_meta = FakeUploadMetadataFactory()
        with patch("requests.sessions.Session.request", autospec=True) as s:
            s.return_value = self._mock_response_factory(status_code=201)
            result = self._transport.post_upload_chunk(
                upload_metadata=upload_meta,
                chunk_index=0,
                chunk_content=b"Bla bla bla ...",
            )

            assert result  # Should not be None or empty.

    def test_post_upload_metadata_returns_expected_value(self) -> None:
        """
        Assert that the ``post_upload_metadata`` method returns the expected
        value.
        """
        extract_meta = FakeExtractMetadataFactory()
        with patch("requests.sessions.Session.request", autospec=True) as s:
            s.return_value = self._mock_response_factory(status_code=201)
            result = self._transport.post_upload_metadata(
                extract_metadata=extract_meta,
                content_type="application/json",
                org_unit_code="12345",
                org_unit_name="Test Facility",
            )

            assert result  # Should not be None or empty.

    def test_transport_authentication_errors(self) -> None:
        """
        Assert that when an authenticates error occurs, the error is handled
        correctly and wrapped inside a TransportError.
        """
        data_source = FakeDataSourceFactory()
        data_source_type = FakeDataSourceTypeFactory()
        with patch("requests.sessions.Session.request", autospec=True) as s:
            s.side_effect = [
                # The first response should trigger the client to
                # re-authenticate.
                self._mock_response_factory(status_code=401),
                ConnectionError,
            ]
            with pytest.raises(
                TransportError,
                match="Error authenticating the client",
            ) as exc_info:
                self._transport.fetch_data_source_extracts(
                    data_source_type=data_source_type,
                    data_source=data_source,
                )

            assert isinstance(exc_info.value.__cause__, ConnectionError)

    def test_transport_re_authentication_failure(self) -> None:
        """
        Assert that if transport re-authenticates fails, the expected error is
        raised.
        """
        data_source = FakeDataSourceFactory()
        data_source_type = FakeDataSourceTypeFactory()
        with patch("requests.sessions.Session.request", autospec=True) as s:
            s.side_effect = [
                self._mock_response_factory(status_code=401),
                # The second response should return 200 not 401.
                self._mock_response_factory(status_code=401),
            ]
            with pytest.raises(
                TransportError,
                match="Unable to authenticate the client on IDR Server",
            ):
                self._transport.fetch_data_source_extracts(
                    data_source_type=data_source_type,
                    data_source=data_source,
                )

    def test_transport_re_authentication_works(self) -> None:
        """
        Test that the transport re-authenticates it-self once it encounters
        a re-authentication-trigger-status.
        """
        data_source = FakeDataSourceFactory()
        data_source_type = FakeDataSourceTypeFactory()
        with patch("requests.sessions.Session.request", autospec=True) as s:
            s.side_effect = [
                # The first response returns a re-authentication trigger status
                self._mock_response_factory(status_code=401),
                # The second response is the result of a call to the
                # authentication end-point.
                self._mock_response_factory(),
                # The final response is the result of the original response
                # after it was retried with the new credentials.
                self._mock_response_factory(),
            ]
            results = self._transport.fetch_data_source_extracts(
                data_source_type=data_source_type,
                data_source=data_source,
            )
            assert list(results) == []

    def test_request_errors(self) -> None:
        """
        Assert that when an request error occurs, the error is handled
        correctly and wrapped inside a TransportError.
        """
        data_source = FakeDataSourceFactory()
        data_source_type = FakeDataSourceTypeFactory()
        with patch("requests.sessions.Session.request", autospec=True) as s:
            s.side_effect = ChunkedEncodingError
            with pytest.raises(
                TransportError,
                match="Unable to make a request to the remote server",
            ) as exc_info:
                self._transport.fetch_data_source_extracts(
                    data_source_type=data_source_type,
                    data_source=data_source,
                )

            assert isinstance(exc_info.value.__cause__, ChunkedEncodingError)

    def test_request_failure(self) -> None:
        """Assert that a request failure raises the expected errors."""
        data_source = FakeDataSourceFactory()
        data_source_type = FakeDataSourceTypeFactory()
        with patch("requests.sessions.Session.request", autospec=True) as s:
            s.return_value = self._mock_response_factory(status_code=500)
            with pytest.raises(
                TransportError,
                match="Expected response status 200, but got 500",
            ):
                self._transport.fetch_data_source_extracts(
                    data_source_type=data_source_type,
                    data_source=data_source,
                )

    @staticmethod
    def _mock_response_factory(
        response_content: bytes = b"",
        status_code: int = 200,
    ) -> _FakeResponse:
        """
        Create and return a new ``_FakeResponse`` instance with the given
        properties.
        """
        response = _FakeResponse()
        response.content = response_content
        response.status_code = status_code
        return response
