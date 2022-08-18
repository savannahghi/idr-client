from typing import Any, Mapping, Tuple

from app.core import DataSource, DataSourceType, ExtractMetadata

AppData = Mapping[str, DataSourceType]

RunExtractionResult = Tuple[DataSourceType, DataSource, ExtractMetadata, Any]
