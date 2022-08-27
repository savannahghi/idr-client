from typing import Any, Mapping, Optional, Sequence

import factory

from app.core import (
    DataSource,
    DataSourceType,
    ExtractMetadata,
    TransportOptions,
    UploadChunk,
    UploadMetadata,
)
from app.lib.transports.http.http_api_dialect import (
    HTTPAPIDialect,
    HTTPRequestParams,
)
from tests.core.factories import (
    FakeUploadChunkFactory,
    FakeUploadMetadataFactory,
)

# =============================================================================
# MOCK CLASSES
# =============================================================================


class _FakeHTTPAPIDialect(HTTPAPIDialect):
    def __init__(self):
        self._host: str = "http://test.example.com"

    @property
    def auth_trigger_statuses(self) -> Sequence[int]:
        return [401]

    def authenticate(self, **options: TransportOptions) -> HTTPRequestParams:
        return {
            "headers": {"Accept": "application/json"},
            "expected_http_status_code": 200,
            "method": "POST",
            "url": "%s/auth/login" % self._host,
        }

    def response_to_auth(
        self, response_content: bytes, **options: TransportOptions
    ) -> Mapping[str, str]:
        return {"Authorization": "Bearer some_secure_token"}

    def fetch_data_source_extracts(
        self,
        data_source_type: DataSourceType,
        data_source: DataSource,
        **options: TransportOptions,
    ) -> HTTPRequestParams:
        return {
            "headers": {"Accept": "application/json"},
            "expected_http_status_code": 200,
            "method": "GET",
            "url": "%s/data_sources_extracts" % self._host,
        }

    def response_to_data_source_extracts(
        self,
        response_content: bytes,
        data_source: DataSource,
        **options: TransportOptions,
    ) -> Sequence[ExtractMetadata]:
        return tuple()

    def fetch_data_sources(
        self, data_source_type: DataSourceType, **options: TransportOptions
    ) -> HTTPRequestParams:
        return {
            "headers": {"Accept": "application/json"},
            "expected_http_status_code": 200,
            "method": "GET",
            "url": "%s/data_sources" % self._host,
        }

    def response_to_data_sources(
        self,
        response_content: bytes,
        data_source_type: DataSourceType,
        **options: TransportOptions,
    ) -> Sequence[DataSource]:
        return tuple()

    def mark_upload_as_complete(
        self, upload_metadata: UploadMetadata, **options: TransportOptions
    ) -> HTTPRequestParams:
        return {
            "headers": {"Accept": "application/json"},
            "expected_http_status_code": 200,
            "method": "PATCH",
            "url": "%s/mark_upload_as_complete" % self._host,
        }

    def post_upload_chunk(
        self,
        upload_metadata: UploadMetadata,
        chunk_index: int,
        chunk_content: Any,
        extra_init_kwargs: Optional[Mapping[str, Any]] = None,
        **options: TransportOptions,
    ) -> HTTPRequestParams:
        return {
            "headers": {"Accept": "application/json"},
            "expected_http_status_code": 201,
            "method": "POST",
            "url": "%s/create_upload_chunk" % self._host,
        }

    def response_to_upload_chunk(
        self,
        response_content: bytes,
        upload_metadata: UploadMetadata,
        **options: TransportOptions,
    ) -> UploadChunk:
        return FakeUploadChunkFactory()

    def post_upload_metadata(
        self,
        extract_metadata: ExtractMetadata,
        content_type: str,
        org_unit_code: str,
        org_unit_name: str,
        extra_init_kwargs: Optional[Mapping[str, Any]] = None,
        **options: TransportOptions,
    ) -> HTTPRequestParams:
        return {
            "headers": {"Accept": "application/json"},
            "expected_http_status_code": 201,
            "method": "POST",
            "url": "%s/create_upload_metadata" % self._host,
        }

    def response_to_upload_metadata(
        self,
        response_content: bytes,
        extract_metadata: ExtractMetadata,
        **options: TransportOptions,
    ) -> UploadMetadata:
        return FakeUploadMetadataFactory(extract_metadata=extract_metadata)


# =============================================================================
# FACTORIES
# =============================================================================


class FakeHTTPAPIDialectFactory(factory.Factory):
    """
    A factory for creating fake instances of http api dialects for testing.
    """

    class Meta:
        model = _FakeHTTPAPIDialect
