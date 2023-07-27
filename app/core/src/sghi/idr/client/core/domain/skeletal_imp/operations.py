from abc import ABCMeta
from typing import Any, Generic, TypeVar

from attrs import define, field

from ..interfaces import (
    CleanedData,
    Data,
    DataProcessor,
    DataSink,
    DataSinkMetadata,
    DataSinkStream,
    DataSource,
    DataSourceMetadata,
    DataSourceStream,
    DrainMetadata,
    DrawMetadata,
    RawData,
)
from .base import BaseNamedDomainObject

# =============================================================================
# TYPES
# =============================================================================

_CD = TypeVar("_CD", bound=CleanedData)
_DM = TypeVar("_DM", bound=DataSourceMetadata)
_DS = TypeVar("_DS", bound=DataSinkMetadata)
_EM = TypeVar("_EM", bound=DrawMetadata)
_RD = TypeVar("_RD", bound=RawData)
_T = TypeVar("_T")
_UM = TypeVar("_UM", bound=DrainMetadata)


# =============================================================================
# OPERATION BASE CLASSES
# =============================================================================


@define(slots=False)
class BaseData(Data[_T], Generic[_T], metaclass=ABCMeta):
    """
    The base skeletal implementation for most :class:`<Data>` implementations.
    """

    _content: _T = field()
    _index: int = field()

    @property
    def content(self) -> _T:
        return self._content

    @property
    def index(self) -> int:
        return self._index


@define(slots=False)
class BaseDataProcessor(
    DataProcessor[_EM, _RD, _CD],
    Generic[_EM, _RD, _CD],
    metaclass=ABCMeta,
):
    """
    Base skeletal implementation for most :class:`DataProcessor` derivatives.
    """

    _is_disposed: bool = field(default=False, init=False)

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed


@define(slots=False)
class BaseDataSink(
    BaseNamedDomainObject,
    DataSink[_DS, _UM, _CD],
    Generic[_DS, _UM, _CD],
    metaclass=ABCMeta,
):
    """
    Base skeletal implementation for most :class:`DataSink` implementations.
    """

    _data_sink_meta: _DS = field()
    _is_disposed: bool = field(default=False, init=False)

    @property
    def data_sink_meta(self) -> _DS:
        return self._data_sink_meta

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed


@define(slots=False)
class BaseDataSinkStream(
    DataSinkStream[_UM, _CD],
    Generic[_UM, _CD],
    metaclass=ABCMeta,
):
    """
    Base skeletal implementation for most :class:`DataSinkStream`
    implementations.
    """

    _data_sink: DataSink[Any, _UM, _CD] = field()
    _drain_metadata: _UM = field()
    _is_disposed: bool = field(default=False, init=False)

    @property
    def data_sink(self) -> DataSink[Any, _UM, _CD]:
        return self._data_sink

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed

    @property
    def drain_metadata(self) -> _UM:
        return self._drain_metadata


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

    _data_source_meta: _DM = field()
    _is_disposed: bool = field(default=False, init=False)

    @property
    def data_source_meta(self) -> _DM:
        return self._data_source_meta

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
    _draw_metadata: _EM = field()
    _is_disposed: bool = field(default=False, init=False)

    @property
    def data_source(self) -> DataSource[Any, _EM, _RD]:
        return self._data_source

    @property
    def draw_metadata(self) -> _EM:
        return self._draw_metadata

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed
