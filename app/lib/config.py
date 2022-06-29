from typing import Any, Dict, Mapping, Optional

from app.core import Task

# =============================================================================
# TYPES
# =============================================================================

SettingInitializer = Task[Any, Any]


# =============================================================================
# CONFIG
# =============================================================================

class Config:
    """An object that holds the app settings."""

    def __init__(
            self,
            settings: Mapping[str, Any],
            settings_initializers: Optional[Mapping[str, SettingInitializer]] = None  # noqa
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
        self._initializers: Mapping[str, Task] = settings_initializers or dict()  # noqa
        self._run_initializers()

    def __getattr__(self, setting: str) -> Any:
        """Make settings available using the dot operator."""
        return self._settings[setting]

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
            setting_val: Any = initializer(self._settings.get(setting))
            self._settings[setting] = setting_val
