from abc import ABCMeta
from typing import Generic, TypeVar

from attrs import define, field

from ..interfaces import (
    DataSinkMetadata,
    DataSourceMetadata,
    ExtractMetadata,
    MetadataSink,
    MetadataSource,
    UploadMetadata,
    UploadMetadataFactory,
)
from .base import BaseNamedDomainObject

# =============================================================================
# TYPES
# =============================================================================


_DM = TypeVar("_DM", bound=DataSourceMetadata)
_DS = TypeVar("_DS", bound=DataSinkMetadata)
_EM = TypeVar("_EM", bound=ExtractMetadata)
_UM = TypeVar("_UM", bound=UploadMetadata)


# =============================================================================
# BASE SKELETAL IMPLEMENTATIONS
# =============================================================================


@define(slots=False)
class BaseMetadataSink(
    BaseNamedDomainObject,
    MetadataSink[_UM],
    Generic[_UM],
    metaclass=ABCMeta,
):
    """
    Base skeletal implementation for most :class:`MetadataSink`
    implementations.
    """

    _is_disposed: bool = field(default=False, init=False)

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed


@define(slots=False)
class BaseMetadataSource(
    BaseNamedDomainObject,
    MetadataSource[_DS, _DM, _EM],
    Generic[_DS, _DM, _EM],
    metaclass=ABCMeta,
):
    """
    Base skeletal implementation for most :class:`MetadataSource`
    implementations.
    """

    _is_disposed: bool = field(default=False, init=False)

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed


@define(slots=False)
class BaseUploadMetadataFactory(
    UploadMetadataFactory[_UM, _EM],
    Generic[_UM, _EM],
    metaclass=ABCMeta,
):
    """
    Base skeletal implementation for most :class:`UploadMetadataFactory`
    implementations.
    """

    _is_disposed: bool = field(default=False, init=False)

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed
