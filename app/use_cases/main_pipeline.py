from typing import Any, Sequence

from app.core import DataSourceType, ExtractMetadata, Transport
from app.lib import Pipeline

from .fetch_metadata import FetchDataSources, FetchExtractMetadata
from .run_extraction import GroupSiblingExtracts, RunDataSourceExtracts
from .types import RunExtractionResult
from .upload_extracts import PostUploadChunks, PostUploads, PrepareUploads


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
    """Upload the extracted metadata to the remote server."""

    def __init__(self, transport: Transport):
        super().__init__(
            PostUploads(transport=transport),
            PrepareUploads(),
            PostUploadChunks(transport=transport),
        )

    # def execute(self, an_input: Sequence[RunExtractionResult]) -> Any:
    #     PostUploads(transport=self._transport).execute(an_input)
    #     # TODO: Add proper implementation.
    #     for _extract in an_input:
    #         print("==========================================================")
    #         print(_extract[0].name)
    #         print("==========================================================")
    #         print("\n", _extract[1], "\n")
    #         print("----------------------------------------------------------")
    #         print("\n")
    #
    #     return an_input
