from typing import Final

from app.lib.config import ImproperlyConfiguredError, SettingInitializer

# =============================================================================
# CONSTANTS
# =============================================================================

_LOCATION_ID_CONFIG_KEY: Final[str] = "LOCATION_ID"

_LOCATION_NAME_CONFIG_KEY: Final[str] = "LOCATION_NAME"


# =============================================================================
# SETTINGS INITIALIZERS
# =============================================================================


class LocationIDInitializer(SettingInitializer):
    @property
    def has_secrets(self) -> bool:
        return False

    @property
    def setting(self) -> str:
        return _LOCATION_ID_CONFIG_KEY

    def execute(self, an_input: str | None) -> str:
        if not an_input:
            _err_message: str = (
                'The setting "{}" is required and must not be empty.'.format(
                    _LOCATION_ID_CONFIG_KEY,
                )
            )
            raise ImproperlyConfiguredError(message=_err_message)

        return an_input


class LocationNameInitializer(SettingInitializer):
    @property
    def has_secrets(self) -> bool:
        return False

    @property
    def setting(self) -> str:
        return _LOCATION_NAME_CONFIG_KEY

    def execute(self, an_input: str | None) -> str:
        if not an_input:
            _err_message: str = (
                'The setting "{}" is required and must not be empty.'.format(
                    _LOCATION_NAME_CONFIG_KEY,
                )
            )
            raise ImproperlyConfiguredError(message=_err_message)

        return an_input
