# The contents of this module are copied from Django sources.
import inspect
import sys
from importlib import import_module
from types import ModuleType
from typing import TypeVar, cast

# =============================================================================
# TYPES
# =============================================================================

_T = TypeVar("_T")


# =============================================================================
# HELPERS
# =============================================================================


def _cached_import(module_path: str, class_name: str) -> ModuleType:
    modules = sys.modules
    if module_path not in modules or (
        # Module is not fully initialized.
        getattr(modules[module_path], "__spec__", None) is not None
        and getattr(modules[module_path].__spec__, "_initializing", False)
        is True
    ):  # pragma: no branch
        import_module(module_path)
    return getattr(modules[module_path], class_name)


# =============================================================================
# IMPORT UTILITIES
# =============================================================================


def import_string(dotted_path: str) -> ModuleType:
    """
    Import a dotted module path and return the attribute/class designated by
    the last name in the path. Raise ``ImportError`` if the import failed.

    :param dotted_path: A dotted path to an attribute or class.

    :return: The attribute/class designated by the last name in the path.

    :raise ImportError: If the import fails for some reason.
    """
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError as err:
        err_msg: str = "%s doesn't look like a module path" % dotted_path
        raise ImportError(err_msg, path=dotted_path) from err

    try:
        return _cached_import(module_path, class_name)
    except AttributeError as err:
        err_msg: str = (
            'Module "{}" does not define a "{}" attribute/class'.format(
                module_path,
                class_name,
            )
        )
        raise ImportError(err_msg, name=class_name, path=module_path) from err


def import_string_as_klass(
    dotted_path: str,
    target_klass: type[_T],
) -> type[_T]:
    """
    Import a dotted module as the given class type. Raise ``ImportError`` if
    the import failed and a ``TypeError`` if the imported module is not of the
    given class type or derived from it.

    :param dotted_path: A dotted path to a class.
    :param target_klass: The class type that the imported module should have or
        be derived from.

    :return: The class designated by the last name in the path.

    :raise ImportError: If the import fails for some reason.
    :raise TypeError: If the imported module is not of the given class type or
        derived from the given class.
    """
    _module = import_string(dotted_path)
    if not inspect.isclass(_module) or not issubclass(_module, target_klass):
        err_msg: str = (
            'Invalid value, "%s" is either not a class or a subclass of "%s".'
            % (dotted_path, target_klass.__qualname__)
        )
        raise TypeError(err_msg)

    return cast(type[target_klass], _module)
