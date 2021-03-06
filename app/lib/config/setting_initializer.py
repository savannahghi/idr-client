from abc import ABCMeta, abstractmethod
from typing import Any

from app.core import Task


class SettingInitializer(Task[Any, Any], metaclass=ABCMeta):
    """
    This interface represents a task used to perform some initialization
    action based on the value of a setting. This can include *(but is not
    limited to)* validating a valid value for a config was given, setting up
    additional components, set default values for settings, etc.

    Setting initializers allow the app to bootstrap/setup itself just before
    the main pipeline begins. There only limitation is that they are only
    executed once, as part of the app's config instantiation.
    """

    @property
    @abstractmethod
    def setting(self) -> str:
        """Return the setting to be initialized using this initializer.

        :return: the setting to be initialized using this initializer.
        """
