from abc import ABCMeta

from attrs import define, field

from ..interfaces import MetadataSink, MetadataSource
from .base import BaseNamedDomainObject


@define(slots=False)
class BaseMetadataSink(BaseNamedDomainObject, MetadataSink, metaclass=ABCMeta):
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
    BaseNamedDomainObject, MetadataSource, metaclass=ABCMeta,
):
    """
    Base skeletal implementation for most :class:`MetadataSource`
    implementations.
    """

    _is_disposed: bool = field(default=False, init=False)

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed
