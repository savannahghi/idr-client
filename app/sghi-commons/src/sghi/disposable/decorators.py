from collections.abc import Callable
from functools import wraps
from typing import Concatenate, ParamSpec, TypeVar

from ..utils import ensure_not_none
from .disposable import Disposable
from .exceptions import ResourceDisposedError

# =============================================================================
# TYPES
# =============================================================================

_D = TypeVar("_D", bound=Disposable)
_DE = TypeVar("_DE", bound=ResourceDisposedError)
_P = ParamSpec("_P")
_R = TypeVar("_R")


# =============================================================================
# DECORATORS
# =============================================================================

class not_disposed:  # noqa :N801
    """
    Decorator that checks if a :class:`~.disposable.Disposable` item has
    already been disposed.

    If the item is disposed, i.e.
    the :attr:`~.disposable.Disposable.is_disposed` property returns ``True``,
    then an instance of :exc:`~.exceptions.ResourceDisposedError`
    is raised.

    .. important::

        This decorator *should* be used on methods bound to an instance of
        the ``Disposable`` interface. It requires that the first parameter of
        the decorated method, i.e. ``self``, be an instance of ``Disposable``.
    """

    __slots__ = ("_exc_factory",)

    def __init__(self, exc_factory: Callable[[], _DE] | None = None):
        """
        Initialize a new instance of ``not_disposed`` decorator.

        :param exc_factory: An optional callable that creates instances of
            ``ResourceDisposedError`` or its subclasses. This is only called
            if the resource is disposed. If not provided, a default factory
            that creates ``ResourceDisposedError`` instances will be used.
        """
        super().__init__()
        self._exc_factory = exc_factory or ResourceDisposedError

    def __call__(
        self, f: Callable[Concatenate[_D, _P], _R],
    ) -> Callable[Concatenate[_D, _P], _R]:
        """Decorate a function with the resource disposal check.

        :param f: The function to be decorated. The first argument of the
            function should be a ``Disposable`` instance.

        :return: The decorated function.
        """
        ensure_not_none(f, "'f' MUST not be None.")

        @wraps(f)
        def wrapper(disposable: _D, *args: _P.args, **kwargs: _P.kwargs) -> _R:
            if disposable.is_disposed:
                raise self._exc_factory()
            return f(disposable, *args, **kwargs)

        return wrapper
