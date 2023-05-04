from abc import ABCMeta
from typing import Any, Generic, TypeVar

from attrs import define, field

from ..interfaces import (
    CleanedData,
    Data,
    DataSink,
    DataSinkStream,
    DataSource,
    DataSourceMetadata,
    DataSourceStream,
    ExtractMetadata,
    RawData,
    UploadContentMetadata,
    UploadMetadata,
)
from .base import BaseNamedDomainObject

# =============================================================================
# TYPES
# =============================================================================

_CD = TypeVar("_CD", bound=CleanedData)
_DM = TypeVar("_DM", bound=DataSourceMetadata)
_EM = TypeVar("_EM", bound=ExtractMetadata)
_RD = TypeVar("_RD", bound=RawData)
_T = TypeVar("_T")
_UC = TypeVar("_UC", bound=UploadContentMetadata)
_UM = TypeVar("_UM", bound=UploadMetadata)


# =============================================================================
# OPERATION BASE CLASSES
# =============================================================================


@define(slots=False)
class BaseData(Generic[_T], Data[_T], metaclass=ABCMeta):
    """
    The base skeletal implementation for most :class:`<Data>` implementations.
    """

    _content: _T = field()

    @property
    def content(self) -> _T:
        return self._content


@define(slots=False)
class BaseDataSink(
    BaseNamedDomainObject,
    DataSink[_UM, _UC, _CD],
    Generic[_UM, _UC, _CD],
    metaclass=ABCMeta,
):
    """
    Base skeletal implementation for most :class:`DataSink` implementations.
    """

    _is_disposed: bool = field(default=False, init=False)

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed


@define(slots=False)
class BaseDataSinkStream(
    DataSinkStream[_UM, _UC, _CD],
    Generic[_UM, _UC, _CD],
    metaclass=ABCMeta,
):
    """
    Base skeletal implementation for most :class:`DataSinkStream`
    implementations.
    """

    _data_sink: DataSink[_UM, _UC, _CD] = field()
    _upload_metadata: _UM = field()
    _is_disposed: bool = field(default=False, init=False)

    @property
    def data_sink(self) -> DataSink[_UM, _UC, _CD]:
        return self._data_sink

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed

    @property
    def upload_metadata(self) -> _UM:
        return self._upload_metadata


@define(slots=False)
class BaseDataSource(
    BaseNamedDomainObject,
    DataSource[_DM, _EM, _RD],
    Generic[_DM, _EM, _RD],
    metaclass=ABCMeta,
):
    """
    Base skeletal implementation for most :class:`DataSource` implementations.
    """

    _is_disposed: bool = field(default=False, init=False)

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed


@define(slots=False)
class BaseDataSourceStream(
    DataSourceStream[_EM, _RD],
    Generic[_EM, _RD],
    metaclass=ABCMeta,
):
    """
    Base skeletal implementation for most :class:`DataSourceStream`
    implementations.
    """

    _data_source: DataSource[Any, _EM, _RD] = field()
    _extract_metadata: _EM = field()
    _is_disposed: bool = field(default=False, init=False)

    @property
    def data_source(self) -> DataSource[Any, _EM, _RD]:
        return self._data_source

    @property
    def extract_metadata(self) -> _EM:
        return self._extract_metadata

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed
