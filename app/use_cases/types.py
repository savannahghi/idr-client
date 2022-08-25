from typing import Any, Sequence, Tuple

from app.core import ExtractMetadata, UploadChunk, UploadMetadata

RunExtractionResult = Tuple[ExtractMetadata, Any]

UploadExtractResult = Tuple[UploadMetadata, Sequence[UploadChunk]]
