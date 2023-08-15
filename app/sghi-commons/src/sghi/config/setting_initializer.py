from abc import ABCMeta, abstractmethod
from typing import Any

from ..task import Task


class SettingInitializer(Task[Any, Any], metaclass=ABCMeta):
    """
    This interface represents a task used to perform some initialization
    action based on the value of a setting. This can include *(but is not
    limited to)* validating a given config value, setting up additional
    components, set default values for settings, etc.

    Setting initializers allow an application/tool to bootstrap/setup itself at
    startup. The only limitation is that they are only executed once, as part
    of the application's config instantiation.
    """

    __slots__ = ()

    @property
    def has_secrets(self) -> bool:
        """Indicates whether the value of this setting contains secrets.

        This is important, and it indicates the value should be handled with
        special care to prevent accidental exposure of sensitive/private
        information.

        :return: ``True`` if the value of this setting contains secretes or
            ``False`` otherwise.
        """
        return False

    @property
    @abstractmethod
    def setting(self) -> str:
        """Return the setting to be initialized using this initializer.

        :return: The setting to be initialized using this initializer.
        """
