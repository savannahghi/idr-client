from abc import ABCMeta, abstractmethod
from collections.abc import Mapping
from types import TracebackType
from typing import Any, ContextManager, Generic, TypeVar

from .task import Task

# =============================================================================
# TYPES
# =============================================================================

_IN = TypeVar("_IN")
_RT = TypeVar("_RT")


# =============================================================================
# MIXINS
# =============================================================================


class Disposable(ContextManager, metaclass=ABCMeta):
    """Represents an entity that uses resources that need to be cleaned up."""

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        self.dispose()
        return False

    @property
    @abstractmethod
    def is_disposed(self) -> bool:
        """
        Return ``True`` if this object has already been disposed, ``False``
        otherwise.

        :return: ``True`` if this object has been disposed, ``False``
            otherwise.
        """
        ...

    @abstractmethod
    def dispose(self) -> None:
        """
        Dispose this object releasing any underlying resources that it may
        have.

        .. note::
            Unless otherwise specified, trying to use other methods of this
            class on an instance after this method returns should generally be
            considered a programming error and should result in an exception
            being raised. This method which should be idempotent allowing it
            to be called more that once; only the first call, however, should
            have an effect.

        :return: None.
        """
        ...


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

        .. note::
            This method is defined as a class method to allow implementing
            classes to self initialize using this method.

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
