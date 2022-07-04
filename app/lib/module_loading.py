# The contents of this module are copied from Django sources.
import sys
from importlib import import_module
from types import ModuleType


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


def import_string(dotted_path: str) -> ModuleType:
    """
    Import a dotted module path and return the attribute/class designated by
    the last name in the path. Raise ImportError if the import failed.

    :param dotted_path: A dotted path to an attribute or class.

    :return: The attribute/class designated by the last name in the path.

    :raise ImportError: If the import fails for some reason.
    """
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError as err:
        raise ImportError(
            "%s doesn't look like a module path" % dotted_path
        ) from err

    try:
        return _cached_import(module_path, class_name)
    except AttributeError as err:
        raise ImportError(
            'Module "%s" does not define a "%s" attribute/class'
            % (module_path, class_name)
        ) from err
