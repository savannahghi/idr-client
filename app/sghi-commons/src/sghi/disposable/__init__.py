from __future__ import annotations

from abc import ABCMeta, abstractmethod
from contextlib import AbstractContextManager
from functools import wraps
from typing import TYPE_CHECKING, Concatenate, ParamSpec, TypeVar, overload

from ..exceptions import SGHIError

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import TracebackType


# =============================================================================
# TYPES
# =============================================================================


_DE = TypeVar("_DE", bound="ResourceDisposedError")
_DT = TypeVar("_DT", bound="Disposable")
_P = ParamSpec("_P")
_RT = TypeVar("_RT")


# =============================================================================
# EXCEPTIONS
# =============================================================================


class ResourceDisposedError(SGHIError):
    """Indicates that a :class:`Disposable` item has already been disposed."""

    def __init__(self, message: str | None = "Resource already disposed."):
        """
        Initialize a new instance of `ResourceDisposedError`.

        :param message: Optional custom error message. If not provided, a
            default message indicating that the resource is already disposed
            will be used.
        """
        super().__init__(message=message)


# =============================================================================
# DISPOSABLE MIXIN
# =============================================================================


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
        """Exit the context manager and call the :meth:`dispose` method.

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
            and should result in a :exc:`ResourceDisposedError` being raised.

            This method should be idempotent allowing it to be called more
            than once; only the first call, however, should have an effect.

        :return: None.
        """
        ...


# =============================================================================
# DECORATORS
# =============================================================================


@overload
def not_disposed(
    f: Callable[Concatenate[_DT, _P], _RT],
    *,
    exc_factory: Callable[[], _DE] = ResourceDisposedError,
) -> Callable[Concatenate[_DT, _P], _RT]:
    ...


@overload
def not_disposed(
    f: None = None,
    *,
    exc_factory: Callable[[], _DE] = ResourceDisposedError,
) -> Callable[
    [Callable[Concatenate[_DT, _P], _RT]],
    Callable[Concatenate[_DT, _P], _RT],
]:
    ...


def not_disposed(
    f: Callable[Concatenate[_DT, _P], _RT] | None = None,
    *,
    exc_factory: Callable[[], _DE] = ResourceDisposedError,
) -> Callable[Concatenate[_DT, _P], _RT] | Callable[
    [Callable[Concatenate[_DT, _P], _RT]],
    Callable[Concatenate[_DT, _P], _RT],
]:
    """Decorate a function with the resource disposal check.

    This decorator ensures a :class:`Disposable` item has not been disposed. If
    the item is disposed, i.e. the :attr:`~Disposable.is_disposed` property
    returns ``True``, then an instance of :exc:`ResourceDisposedError` or it's
    derivatives is raised.

    .. important::

        This decorator *MUST* be used on methods bound to an instance of the
        ``Disposable`` interface. It requires that the first parameter of the
        decorated method, i.e. ``self``, be an instance of ``Disposable``.

    :param f: The function to be decorated. The first argument of the
        function should be a ``Disposable`` instance.
    :param exc_factory: An optional callable that creates instances of
        ``ResourceDisposedError`` or its subclasses. This is only called
        if the resource is disposed. If not provided, a default factory
        that creates ``ResourceDisposedError`` instances will be used.

    :return: The decorated function.
    """
    def wrap(
        _f: Callable[Concatenate[_DT, _P], _RT],
    ) -> Callable[Concatenate[_DT, _P], _RT]:

        @wraps(_f)
        def wrapper(
            disposable: _DT,
            *args: _P.args,
            **kwargs: _P.kwargs,
        ) -> _RT:
            if disposable.is_disposed:
                raise exc_factory()
            return _f(disposable, *args, **kwargs)

        return wrapper

    # Whether `f` is None or not depends on the usage of the decorator. It's a
    # method when used as `@not_disposed` and None when used as
    # `@not_disposed()` or `@not_disposed(exc_factory=...)`.
    if f is None:
        return wrap

    return wrap(f)


# =============================================================================
# MODULE EXPORTS
# =============================================================================


__all__ = [
    "Disposable",
    "ResourceDisposedError",
    "not_disposed",
]
