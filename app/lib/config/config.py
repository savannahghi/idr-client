import logging
from typing import Any, Dict, Mapping, Optional

from app.core import Task

from .exceptions import MissingSettingError

# =============================================================================
# TYPES
# =============================================================================

SettingInitializer = Task[Any, Any]


# =============================================================================
# CONSTANTS
# =============================================================================

_LOGGER = logging.getLogger(__name__)


# =============================================================================
# CONFIG
# =============================================================================


class Config:
    """An object that holds the app settings.

    Only read only access to the settings is available post initialization. Any
    required modifications to the settings should be done at initialization
    time by passing a mapping of setting names and ``SettingInitializer``
    instances to this class's constructor. Setting names are encouraged to be
    uppercase to convey that they are read only. Setting names that are also
    valid python identifiers can also be accessed using the dot notation.
    """

    def __init__(
        self,
        settings: Mapping[str, Any],
        settings_initializers: Optional[
            Mapping[str, SettingInitializer]
        ] = None,  # noqa
    ):
        """
        Initialize a new :class:`Config` instance. The settings to use are
        passed as a mapping with the setting names as the keys and the setting
        values as the values of the mapping.

        Optional initializers can also be passed to the constructor to perform
        additional initialization tasks such as set up of addition components
        or validating that required settings were provided, etc. Initializers
        can also be used to remap settings values to more appropriate runtime
        values by taking a raw setting value and return the desired or
        appropriate value. The value is then set as the new value of the
        setting and will remain that way for the duration of the runtime of the
        app.

        :param settings: The configurations/settings to use as a mapping.
        :param settings_initializers: Optional initializers to perform post
            initialization tasks.
        """
        self._settings: Dict[str, Any] = dict(settings or {})
        self._initializers: Mapping[str, Task] = (
            settings_initializers or dict()
        )  # noqa
        self._run_initializers()

    def __getattr__(self, setting: str) -> Any:
        """Make settings available using the dot operator."""
        try:
            return self._settings[setting]
        except KeyError:
            raise MissingSettingError(setting=setting)

    def get(self, setting: str, default: Any = None) -> Any:
        """
        Retrieve the value of the given setting or return the given default if
        no such setting exists in this ``Config`` instance. This method can
        also be used for retrieval of settings with invalid python identifier
        names.

        :param setting: The name of the setting value to retrieve.
        :param default: A value to return when no setting with the given name
            exists in this config.

        :return: The value of the given setting if it is present in this config
            or the given default otherwise.
        """
        return self._settings.get(setting, default)

    def _run_initializers(self) -> None:
        """
        Run each setting initializer passing it the current raw value of the
        setting or ``None`` if the setting is not present. Whatever the
        initializer returns is set as the new value if the setting. This way,
        initializers can also be used to set default settings if they aren't
        already present.

        :return: None.
        """
        for setting, initializer in self._initializers.items():
            raw_setting_val: Any = self._settings.get(setting)
            setting_val: Any = initializer(raw_setting_val)
            _LOGGER.debug(
                'Ran initializer for the setting "%s" with raw value "%s".',
                str(setting),
                str(raw_setting_val),
            )
            self._settings[setting] = setting_val
