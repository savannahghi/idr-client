from abc import ABCMeta, abstractmethod
from typing import Any, Generic, Mapping, TypeVar

from .task import Task

# =============================================================================
# TYPES
# =============================================================================

_IN = TypeVar("_IN")
_RT = TypeVar("_RT")


# =============================================================================
# MIXINS
# =============================================================================


class InitFromMapping(metaclass=ABCMeta):
    """
    Represents objects that can initialize themselves from a serialized
    mapping of their state.
    """

    @classmethod
    @abstractmethod
    def of_mapping(cls, mapping: Mapping[str, Any]) -> object:
        """
        Initialize an object given a mapping representing the object's state.

        *Note: This method is defined as a class method to allow implementors
        to initialize themselves using this method.*

        :param mapping: A mapping containing/representing an object's state.

        :return: the initialized object.
        """
        ...


class ToMapping(metaclass=ABCMeta):
    """Represents objects that can serialize their state into a mapping.

    This mapping can then be used to initialize the object later.
    """

    @abstractmethod
    def to_mapping(self) -> Mapping[str, Any]:
        """
        Serialize an object's state into a mapping and return that mapping.

        :return: a mapping containing the object's state.
        """
        ...


class ToTask(Generic[_IN, _RT], metaclass=ABCMeta):
    """Represents an object that can create or be converted to a `Task`."""

    @abstractmethod
    def to_task(self) -> Task[_IN, _RT]:
        """Create and return a `Task` instance from this object.

        :return: a task created from this object.
        """
        ...
