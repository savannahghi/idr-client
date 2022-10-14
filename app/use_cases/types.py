from collections.abc import Sequence
from typing import Any

from app.core import ExtractMetadata, UploadChunk, UploadMetadata

RunExtractionResult = tuple[ExtractMetadata, Any]

UploadExtractResult = tuple[UploadMetadata, Sequence[UploadChunk]]
