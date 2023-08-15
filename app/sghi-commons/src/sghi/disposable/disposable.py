from __future__ import annotations

from abc import ABCMeta, abstractmethod
from contextlib import AbstractContextManager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import TracebackType


class Disposable(AbstractContextManager, metaclass=ABCMeta):
    """An entity that uses resources that need to be cleaned up.

    As such, this interface supports the
    :doc:`context manager protocol<python:library/contextlib>` making its
    derivatives usable with Python's ``with`` statement. Implementors should
    override the :meth:`dispose` method and define the resource clean up logic.
    The :attr:`is_disposed` property can be used to check whether an instance
    has been disposed.
    """

    __slots__ = ()

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
    ) -> bool | None:
        """
        Exit the context manager and call the :meth:`dispose` method.

        :param exc_type: The type of the exception being handled. If an
            exception was raised and is being propagated, this will be the
            exception type. Otherwise, it will be ``None``.
        :param exc_val: The exception instance. If no exception was raised,
            this will be ``None``.
        :param exc_tb: The traceback for the exception. If no exception was
            raised, this will be ``None``.

        :return: `False`.
        """
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
            Unless otherwise specified, trying to use methods of a
            ``Disposable`` instance decorated with the
            :class:`~.decorators.not_disposed` decorator after this
            method returns should generally be considered a programming error
            and should result in a :exc:`~.exceptions.ResourceDisposedError`
            being raised.

            This method should be idempotent allowing it to be called more
            than once; only the first call, however, should have an effect.

        :return: None.
        """
        ...
