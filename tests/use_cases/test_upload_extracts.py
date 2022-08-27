from typing import Any, Dict, Sequence, Tuple
from unittest import TestCase
from unittest.mock import patch

from app.core import ExtractMetadata, Transport, UploadMetadata
from app.lib import Config
from app.use_cases.upload_extracts import (
    DoMarkUploadAsComplete,
    DoPostChunk,
    DoPostUpload,
    MarkUploadsAsComplete,
    PostUploadChunks,
    PostUploads,
    PrepareUploadChunks,
    RunExtractionResult,
    UploadExtractResult,
)
from tests.core.factories import (
    FakeExtractMetadataFactory,
    FakeTransportFactory,
    FakeUploadMetadataFactory,
)


class TestDoMarkUploadAsComplete(TestCase):
    """Tests for the :class:`DoMarkUploadAsComplete` class."""

    def setUp(self) -> None:
        super().setUp()
        self._upload_meta: UploadMetadata = FakeUploadMetadataFactory()
        self._instance: DoMarkUploadAsComplete = DoMarkUploadAsComplete(
            upload=self._upload_meta
        )
        self._transport: Transport = FakeTransportFactory()

    def test_execute_return_value(self) -> None:
        """Assert that the ``execute()`` method returns the expected value."""
        result = self._instance.execute(self._transport)

        assert result  # Should not be None or empty.
        assert result == self._upload_meta


class TestDoPostChunk(TestCase):
    """Tests for the :class:`DoPostChunk` class."""

    def setUp(self) -> None:
        super().setUp()
        self._chunk_content: bytes = b"Bla bla bla ..."
        self._chunk_index: int = 0
        self._transport: Transport = FakeTransportFactory()
        self._upload_meta: UploadMetadata = FakeUploadMetadataFactory()
        self._instance: DoPostChunk = DoPostChunk(
            upload=self._upload_meta,
            chunk_index=self._chunk_index,
            chunk_content=self._chunk_content,
        )

    def test_execute_return_value(self) -> None:
        """Assert that the ``execute()`` method returns the expected value."""
        result = self._instance.execute(self._transport)

        assert result  # Should not be None or empty.
        assert result.chunk_content == self._chunk_content
        assert result.chunk_index == self._chunk_index


class TestDoPostUpload(TestCase):
    """Tests for the :class:`DoPostUpload` class."""

    def setUp(self) -> None:
        super().setUp()
        self._data: bytes = b"Bla bla bla ..."
        self._extract_meta: ExtractMetadata = FakeExtractMetadataFactory()
        self._org_unit_code: str = "12345"
        self._org_unit_name: str = "Test Facility"
        self._transport: Transport = FakeTransportFactory()
        self._instance: DoPostUpload = DoPostUpload(
            extract=(self._extract_meta, self._data)
        )

    def test_execute_return_value(self) -> None:
        """Assert that the ``execute()`` method returns the expected value."""
        config: Dict[str, Any] = {
            "ORG_UNIT_CODE": self._org_unit_code,
            "ORG_UNIT_NAME": self._org_unit_name,
        }
        with patch("app.settings", Config(settings=config)):
            result = self._instance.execute(self._transport)

        assert len(result) == 2
        assert result[0].extract_metadata == self._extract_meta
        assert result[0].org_unit_code == self._org_unit_code
        assert result[0].org_unit_name == self._org_unit_name


class TestPostUploads(TestCase):
    """Tests for the :class:`PostUploads` class."""

    def setUp(self) -> None:
        super().setUp()
        self._max_items: int = 7
        self._extract_data: Sequence[bytes] = tuple(
            f"Bla bla bla {_index} ...".encode()
            for _index in range(self._max_items)
        )
        self._extract_metas: Sequence[ExtractMetadata]
        self._extract_metas = FakeExtractMetadataFactory.create_batch(
            size=self._max_items
        )
        self._extraction_result: Sequence[RunExtractionResult] = tuple(
            (_extract, _data)
            for _extract, _data in zip(self._extract_metas, self._extract_data)
        )
        self._org_unit_code: str = "12345"
        self._org_unit_name: str = "Test Facility"
        self._transport: Transport = FakeTransportFactory()
        self._instance: PostUploads = PostUploads(transport=self._transport)

    def test_execute_return_value(self) -> None:
        """Assert that the ``execute()`` method returns the expected value."""
        config: Dict[str, Any] = {
            "ORG_UNIT_CODE": self._org_unit_code,
            "ORG_UNIT_NAME": self._org_unit_name,
        }
        with patch("app.settings", Config(settings=config)):
            results = self._instance.execute(self._extraction_result)

        assert len(results) == self._max_items
        assert len(results[0]) == 2
        assert results[0][0].org_unit_code == self._org_unit_code
        assert results[0][0].org_unit_name == self._org_unit_name


class TestPrepareUploadChunks(TestCase):
    """Tests for the :class:`PrepareUploadChunks` class."""

    def setUp(self) -> None:
        super().setUp()
        self._chunk_count: int = 10
        self._max_items: int = 7
        self._extract_data: Sequence[bytes] = tuple(
            f"Bla bla bla {_index} ...".encode()
            for _index in range(self._max_items)
        )
        self._instance: PrepareUploadChunks = PrepareUploadChunks()
        self._transport: Transport = FakeTransportFactory()
        self._upload_metas: Sequence[UploadMetadata]
        self._upload_metas = FakeUploadMetadataFactory.create_batch(
            size=self._max_items,
            chunk_count=self._chunk_count,
        )
        self._posted_uploads: Sequence[Tuple[UploadMetadata, Any]] = tuple(
            (_upload, _data)
            for _upload, _data in zip(self._upload_metas, self._extract_data)
        )

    def test_execute_return_value(self) -> None:
        """Assert that the ``execute()`` method returns the expected value."""
        results = self._instance.execute(self._posted_uploads)

        assert len(results) == self._max_items
        assert len(results[0]) == 2
        assert len(results[0][1]) == self._chunk_count


class TestPostUploadChunks(TestPrepareUploadChunks):
    """Tests for the :class:`PostUploadChunks` class."""

    def setUp(self) -> None:
        super().setUp()
        self._prepared_chunks: Sequence[Tuple[UploadMetadata, Sequence[bytes]]]
        self._prepared_chunks = PrepareUploadChunks().execute(
            self._posted_uploads
        )
        self._instance: PostUploadChunks = PostUploadChunks(self._transport)

    def test_execute_return_value(self) -> None:
        """Assert that the ``execute()`` method returns the expected value."""
        results = self._instance.execute(self._prepared_chunks)

        assert len(results) == self._max_items
        assert len(results[0]) == 2
        assert len(results[0][1]) == self._chunk_count


class TestMarkUploadAsComplete(TestPostUploadChunks):
    """Tests for the :class:`MarkUploadsAsComplete` class."""

    def setUp(self) -> None:
        super().setUp()
        self._instance: MarkUploadsAsComplete = MarkUploadsAsComplete(
            transport=self._transport
        )
        self._upload_results: Sequence[UploadExtractResult]
        self._upload_results = PostUploadChunks(self._transport).execute(
            self._prepared_chunks
        )

    def test_execute_return_value(self) -> None:
        """Assert that the ``execute()`` method returns the expected value."""
        results = self._instance.execute(self._upload_results)

        assert len(results) == self._max_items
        assert len(results[0]) == 2
        assert len(results[0][1]) == self._chunk_count
