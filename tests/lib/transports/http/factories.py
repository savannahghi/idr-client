from typing import Mapping, Sequence

import factory

from app.core import (
    DataSource,
    DataSourceType,
    ExtractMetadata,
    TransportOptions,
)
from app.lib.transports.http.http_api_dialect import (
    HTTPAPIDialect,
    HTTPRequestParams,
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
            "method": "POST",
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
            "method": "POST",
            "url": "%s/data_sources" % self._host,
        }

    def response_to_data_sources(
        self,
        response_content: bytes,
        data_source_type: DataSourceType,
        **options: TransportOptions,
    ) -> Sequence[DataSource]:
        return tuple()


# =============================================================================
# FACTORIES
# =============================================================================


class FakeHTTPAPIDialectFactory(factory.Factory):
    """
    A factory for creating fake instances of http api dialects for testing.
    """

    class Meta:
        model = _FakeHTTPAPIDialect
