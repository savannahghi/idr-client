from concurrent.futures import Future, as_completed
from logging import getLogger
from typing import Any, Iterable, Sequence, Tuple, Type

import app
from app.core import (
    DataSource,
    DataSourceType,
    ExtractMetadata,
    Task,
    Transport,
    TransportError,
    UploadChunk,
    UploadMetadata,
)
from app.lib import (
    ConcurrentExecutor,
    Consumer,
    Retry,
    completed_successfully,
    if_exception_type_factory,
)

from .types import RunExtractionResult, UploadExtractResult

# =============================================================================
# CONSTANTS
# =============================================================================

_LOGGER = getLogger(__name__)


# =============================================================================
# TYPES
# =============================================================================

_PostedUpload = Tuple[UploadMetadata, Any]

_PreparedChunks = Tuple[UploadMetadata, Sequence[bytes]]


# =============================================================================
# HELPER TASKS
# =============================================================================


class DoPostUpload(Task[Transport, _PostedUpload]):
    def __init__(self, extract: RunExtractionResult):
        self._extract: RunExtractionResult = extract

    @Retry(predicate=if_exception_type_factory(TransportError))
    def execute(self, an_input: Transport) -> _PostedUpload:
        _LOGGER.info(
            'Posting upload metadata for extract metadata="%s".',
            str(self._extract[0]),
        )
        extract_meta: ExtractMetadata = self._extract[0]
        parent_ds: DataSource = extract_meta.data_source
        parent_dst: DataSourceType = parent_ds.data_source_type
        upload_meta_klass: Type[
            UploadMetadata
        ] = parent_dst.imp_upload_metadata_klass()
        content_type: str = upload_meta_klass.get_content_type()

        upload_meta: UploadMetadata = an_input.post_upload_metadata(
            extract_metadata=extract_meta,
            content_type=content_type,
            org_unit_code=app.settings.ORG_UNIT_CODE,
            org_unit_name=app.settings.ORG_UNIT_NAME,
            extra_init_kwargs=extract_meta.get_upload_meta_extra_init_kwargs(),
        )
        return upload_meta, self._extract[1]


class DoPostChunk(Task[Transport, UploadChunk]):
    def __init__(
        self, upload: UploadMetadata, chunk_index: int, chunk_content: bytes
    ):
        self._upload: UploadMetadata = upload
        self._chunk_index: int = chunk_index
        self._chunk_content: bytes = chunk_content

    @Retry(predicate=if_exception_type_factory(TransportError))
    def execute(self, an_input: Transport) -> UploadChunk:
        _LOGGER.info(
            'Posting upload chunks for upload metadata="%s".',
            str(self._upload),
        )
        extra_init_kwargs = self._upload.get_upload_chunk_extra_init_kwargs()
        chunk: UploadChunk = an_input.post_upload_chunk(
            upload_metadata=self._upload,
            chunk_index=self._chunk_index,
            chunk_content=self._chunk_content,
            extra_init_kwargs=extra_init_kwargs,
        )
        return chunk


class DoMarkUploadAsComplete(Task[Transport, UploadMetadata]):
    def __init__(self, upload: UploadMetadata):
        self._upload: UploadMetadata = upload

    @Retry(predicate=if_exception_type_factory(TransportError))
    def execute(self, an_input: Transport) -> UploadMetadata:
        _LOGGER.info('Marking upload="%s" as complete.', str(self._upload))
        an_input.mark_upload_as_complete(self._upload)
        return self._upload


# =============================================================================
# MAIN TASKS
# =============================================================================


class PostUploads(
    Task[Sequence[RunExtractionResult], Sequence[_PostedUpload]]
):
    def __init__(self, transport: Transport):
        self._transport: Transport = transport

    def execute(
        self, an_input: Sequence[RunExtractionResult]
    ) -> Sequence[_PostedUpload]:
        _LOGGER.info("Posting uploads.")
        executor: ConcurrentExecutor[Transport, _PostedUpload]
        executor = ConcurrentExecutor(
            *self._extraction_results_to_tasks(an_input)
        )
        with executor:
            futures: Sequence[Future[_PostedUpload]]
            futures = executor(self._transport)  # noqa
            # Focus on completed tasks and ignore the ones that failed.
            completed_futures = as_completed(futures)
        return tuple(
            map(
                lambda _f: _f.result(),
                filter(
                    lambda _f: completed_successfully(_f), completed_futures
                ),
            )
        )

    @staticmethod
    def _extraction_results_to_tasks(
        extraction_results: Iterable[RunExtractionResult],
    ) -> Sequence[DoPostUpload]:
        return tuple(DoPostUpload(_extract) for _extract in extraction_results)


class PrepareUploadChunks(
    Task[Sequence[_PostedUpload], Sequence[_PreparedChunks]]
):
    def execute(
        self, an_input: Sequence[_PostedUpload]
    ) -> Sequence[_PreparedChunks]:
        _LOGGER.info("Preparing chunks.")
        return tuple(
            self._prepare_chunks_for_upload(_posted_upload)
            for _posted_upload in an_input
        )

    @staticmethod
    def _prepare_chunks_for_upload(
        posted_upload: _PostedUpload,
    ) -> _PreparedChunks:
        _LOGGER.info(
            'Preparing chunks for upload metadata="%s".', str(posted_upload[0])
        )
        upload: UploadMetadata = posted_upload[0]
        extract_data: Any = posted_upload[1]
        chunks: Sequence[bytes] = upload.to_task().execute(extract_data)
        return upload, chunks


class PostUploadChunks(
    Task[Sequence[_PreparedChunks], Sequence[UploadExtractResult]]
):
    def __init__(self, transport: Transport):
        self._transport: Transport = transport

    def execute(
        self, an_input: Sequence[_PreparedChunks]
    ) -> Sequence[UploadExtractResult]:
        _LOGGER.info("Posting upload chunks.")
        return tuple(
            self._post_upload_chunks(
                upload=_prepared_upload[0],
                chunks=_prepared_upload[1],
                transport=self._transport,
            )
            for _prepared_upload in an_input
        )

    @staticmethod
    def _post_upload_chunks(
        upload: UploadMetadata, chunks: Sequence[bytes], transport: Transport
    ) -> UploadExtractResult:
        executor: ConcurrentExecutor[Transport, UploadChunk]
        executor = ConcurrentExecutor(
            *(
                DoPostChunk(
                    upload=upload, chunk_index=_index, chunk_content=_chunk
                )
                for _index, _chunk in enumerate(chunks)
            )
        )
        with executor:
            futures: Sequence[Future[UploadChunk]]
            futures = executor(transport)  # noqa
            # Focus on completed tasks and ignore the ones that failed.
            completed_futures = as_completed(futures)
        uploaded_chunks: Sequence[UploadChunk] = tuple(
            map(
                lambda _f: _f.result(),
                filter(
                    lambda _f: completed_successfully(_f), completed_futures
                ),
            )
        )
        return upload, uploaded_chunks


class MarkUploadsAsComplete(Consumer[Sequence[UploadExtractResult]]):
    def __init__(self, transport: Transport):
        super().__init__(consume=self._mark_uploads_as_complete)
        self._transport: Transport = transport

    def _mark_uploads_as_complete(
        self, posted_uploads: Sequence[UploadExtractResult]
    ) -> None:
        _LOGGER.info("Marking completed upload as so.")
        executor: ConcurrentExecutor[Transport, Any]
        executor = ConcurrentExecutor(
            *(
                DoMarkUploadAsComplete(upload=_posted_upload[0])
                for _posted_upload in posted_uploads
            )
        )
        with executor:
            futures: Sequence[Future[Any]]
            futures = executor(an_input=self._transport)  # noqa
            as_completed(futures)
