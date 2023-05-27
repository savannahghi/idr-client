import logging
from collections.abc import Mapping, Sequence
from typing import Any, final

from .exceptions import MissingSettingError
from .setting_initializer import SettingInitializer

# =============================================================================
# CONSTANTS
# =============================================================================

_LOGGER = logging.getLogger(__name__)


# =============================================================================
# CONFIG
# =============================================================================


@final
class Config:
    """An object that holds the app settings.

    At runtime, an instance of this class is accessible using the
    :attr:`app.config` attribute.

    Only read-only access to the settings is available post initialization. Any
    required modifications to the settings should be done at initialization
    time by passing a sequence of :class:`initializers <SettingInitializer>`
    to this class's constructor. Uppercase names for settings should be
    preferred to convey that they are read only.

    Setting names that are also valid python identifiers can be accessed using
    the dot notation on an instance of this class. The :meth:`get` method can
    also be used to access settings after initialization and is especially
    useful for access to settings with names that are invalid python
    identifies.
    """

    def __init__(
        self,
        settings: Mapping[str, Any],
        settings_initializers: Sequence[SettingInitializer] | None = None,
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
        app. If multiple initializers are given for the same setting, they are
        executed in the given order with the output of the previous initializer
        becoming the input of the next initializer. The output of the last
        initializer is then set as the final value of the setting.

        :param settings: The configurations/settings to use as a mapping.
        :param settings_initializers: Optional initializers to perform post
            initialization tasks.
        """
        self._settings: dict[str, Any] = dict(settings or {})
        self._initializers: Mapping[
            str,
            Sequence[SettingInitializer],
        ] = self._group_related_initializers(settings_initializers or ())
        self._run_initializers()

    def __getattr__(self, setting: str) -> Any:  # noqa: ANN401
        """Make settings available using the dot operator."""
        try:
            return self._settings[setting]
        except KeyError:
            raise MissingSettingError(setting=setting) from None

    def get(self, setting: str, default: Any = None) -> Any:  # noqa: ANN401
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
        from app.lib import Pipeline

        for _setting, _initializers in self._initializers.items():
            raw_setting_val: Any = self._settings.get(_setting)
            initializer_pipeline: Pipeline = Pipeline(*_initializers)
            setting_val: Any = initializer_pipeline(raw_setting_val)
            _LOGGER.debug(
                'Ran initializer for the setting "%s" with raw value "%s".',
                str(_setting),
                "******"
                if any(_i.has_secrets for _i in _initializers)
                else str(raw_setting_val),
            )
            self._settings[_setting] = setting_val

    @staticmethod
    def _group_related_initializers(
        initializers: Sequence[SettingInitializer],
    ) -> Mapping[str, Sequence[SettingInitializer]]:
        grouped_initializers: dict[str, list[SettingInitializer]] = {}
        for _initializer in initializers:
            grouped_initializers.setdefault(_initializer.setting, []).append(
                _initializer,
            )
        return grouped_initializers
