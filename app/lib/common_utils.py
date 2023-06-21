from collections.abc import Callable
from typing import Any, TypeVar

_T = TypeVar("_T")


def type_fqn(klass: type[_T] | Callable[..., Any]) -> str:
    """Return the fully qualified name of a type or callable.

    :param klass: A type or callable whose fully qualified name is to be
        determined.

    :return: The fully qualified name of the given type/callable.
    """
    return ".".join((klass.__module__, klass.__qualname__))
