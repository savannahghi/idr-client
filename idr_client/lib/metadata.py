from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import Any, Generic, Optional, Sequence, Type, TypeVar, Mapping

from idr_client.core import AbstractMetadata

from .tasks import SQLTask


# =============================================================================
# TYPES
# =============================================================================

_IN = TypeVar("_IN")
_RT = TypeVar("_RT")
_SE = TypeVar("_SE", bound="AbstractMetadata")


# =============================================================================
# METADATA
# =============================================================================

class SQLMetadataTypes(Enum):
    """The different types of sql metadata types."""
    EXTRACTOR = "Extractor"
    PREDICATE = "Predicate"


class SQLMetadata(AbstractMetadata[Any, object]):
    sql: str
    metadata_type: SQLMetadataTypes
    extract_name: Optional[str]

    def as_task(self) -> SQLTask:
        return SQLTask(self.sql)

    @classmethod
    def of_mapping(cls, mapping: Mapping[str, Any]) -> object:
        # TODO: Add implementation
        ...
