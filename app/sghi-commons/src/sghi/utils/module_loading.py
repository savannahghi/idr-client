import inspect
from importlib.metadata import EntryPoint
from typing import Any, Final, TypeVar, cast

# =============================================================================
# TYPES
# =============================================================================

_T = TypeVar("_T")


# =============================================================================
# CONSTANTS
# =============================================================================

_UNKNOWN_STR: Final[str] = "UNKNOWN"


# =============================================================================
# IMPORT UTILITIES
# =============================================================================


def import_string(dotted_path: str) -> Any:  # noqa: ANN401
    """
    Import a dotted module path and return the Python object designated by
    the last name in the path.

    The `dotted path` can refer to any "importable" Python object
    including modules. It should also conform to the format defined by the
    Python packaging conventions. See :doc:`the packaging docs on entry points
    <pypackage:specifications/entry-points>` for more information.

    Raise :exc:`ImportError` if the import failed.

    :param dotted_path: A dotted path to a Python object.

    :return: The Python object designated by the last name in the path.

    :raise ImportError: If the import fails for some reason.
    """
    entry_point = EntryPoint(
        name=_UNKNOWN_STR,
        group=_UNKNOWN_STR,
        value=dotted_path,
    )
    try:
        return entry_point.load()
    except AttributeError as exp:
        _err_msg: str = str(exp)
        raise ImportError(_err_msg) from exp


def import_string_as_klass(
    dotted_path: str,
    target_klass: type[_T],
) -> type[_T]:
    """
    Import a dotted module path as the given class type.

    Raise :exc:`ImportError` if the import failed or a :exc:`TypeError` if the
    imported Python object is not of the given class type or derived from it.

    :param dotted_path: A dotted path to a class.
    :param target_klass: The class type that the imported module should have or
        be derived from.

    :return: The class designated by the last name in the path.

    :raise ImportError: If the import fails for some reason.
    :raise TypeError: If the imported object is not of the given class type or
        derived from the given class.
    """
    _module = import_string(dotted_path)
    if not inspect.isclass(_module) or not issubclass(_module, target_klass):
        err_msg: str = (
            'Invalid value, "{}" is either not a class or a subclass of '
            '"{}".'.format(dotted_path, target_klass.__qualname__)
        )
        raise TypeError(err_msg)

    return cast(type[target_klass], _module)
