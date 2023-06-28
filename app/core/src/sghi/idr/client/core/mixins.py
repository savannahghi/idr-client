from abc import ABCMeta, abstractmethod
from collections.abc import Mapping
from contextlib import AbstractContextManager
from types import TracebackType
from typing import Any, Generic, TypeVar

from .task import Task

# =============================================================================
# TYPES
# =============================================================================

_IN = TypeVar("_IN")
_RT = TypeVar("_RT")


# =============================================================================
# MIXINS
# =============================================================================


class Disposable(AbstractContextManager, metaclass=ABCMeta):
    """An entity that uses resources that need to be cleaned up.

    As such, this interface supports the
    `context manager protocol <https://docs.python.org/3.11/library/stdtypes.html#typecontextmanager>`_
    making its derivatives usable with Python's ``with`` statement.
    Implementors should override the :meth:`dispose` method and define the
    resource clean up logic. The :attr:`is_disposed` property can be used to
    check whether an instance has been disposed.
    """

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        super().__exit__(exc_type, exc_val, exc_tb)
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
        """Release any underlying resources contained by this object.

        After this method returns successfully, the :attr:`is_disposed`
        property should return ``True``.

        .. note::
            Unless otherwise specified, trying to use other methods of this
            class on an instance after this method returns should generally be
            considered a programming error and should result in an exception
            being raised. This method should be idempotent allowing it to be
            called more that once; only the first call, however, should have an
            effect.

        :return: None.
        """
        ...


class InitFromMapping(metaclass=ABCMeta):
    """A type that can instantiate itself from a `Mapping` of it's state.

    Derivatives of this interface can instantiate themselves from a serialized
    mapping of their state. This can be achieved by calling the
    :meth:`of_method` class method and passing a `Mapping` of the object's
    state.
    """

    @classmethod
    @abstractmethod
    def of_mapping(cls, mapping: Mapping[str, Any]) -> "InitFromMapping":
        """Initialize an object given a `Mapping` of its state.

        .. note::
            This method is defined as a class method to allow implementing
            classes to self initialize using this method.

        :param mapping: A `Mapping` containing/representing an object's state.

        :return: the initialized object.
        """
        ...


class ToMapping(metaclass=ABCMeta):
    """A type whose instances' state be serialized into a `Mapping`.

    Instances of this interface can call the :meth:`to_mapping` method to get a
    `Mapping` of their states.
    """

    @abstractmethod
    def to_mapping(self) -> Mapping[str, Any]:
        """Serialize this object's state into a `Mapping` and return it.

        :return: a Mapping containing the object's state.
        """
        ...


class ToTask(Generic[_IN, _RT], metaclass=ABCMeta):
    """A type whose instances can create or be converted to a :class:`Task`.

    Instances of this interface can call the :meth:`to_task` method to get a
    `Task` representation of the instance.
    """

    @abstractmethod
    def to_task(self) -> Task[_IN, _RT]:
        """Create and return a `Task` instance from this object.

        :return: a `Task` created from this object.
        """
        ...
