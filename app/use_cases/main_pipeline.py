from collections.abc import Sequence
from typing import Any

from app.core import DataSourceType, ExtractMetadata, Transport
from app.lib import Pipeline

from .fetch_metadata import FetchDataSources, FetchExtractMetadata
from .run_extraction import GroupSiblingExtracts, RunDataSourceExtracts
from .types import RunExtractionResult
from .upload_extracts import (
    MarkUploadsAsComplete,
    PostUploadChunks,
    PostUploads,
    PrepareUploadChunks,
)


class FetchMetadata(
    Pipeline[Sequence[DataSourceType], Sequence[ExtractMetadata]]
):
    """Connect to the remote server and fetch metadata."""

    def __init__(self, transport: Transport):
        super().__init__(
            FetchDataSources(transport=transport),
            FetchExtractMetadata(transport=transport),
        )


class RunExtraction(
    Pipeline[Sequence[ExtractMetadata], Sequence[RunExtractionResult]]
):
    """
    Run each extracts against their parent data source and return the results.
    """

    def __init__(self):
        super().__init__(GroupSiblingExtracts(), RunDataSourceExtracts())


class UploadExtracts(Pipeline[Sequence[RunExtractionResult], Any]):
    """Upload the extracted metadata to their final destination."""

    def __init__(self, transport: Transport):
        super().__init__(
            PostUploads(transport=transport),
            PrepareUploadChunks(),
            PostUploadChunks(transport=transport),
            MarkUploadsAsComplete(transport=transport),
        )
