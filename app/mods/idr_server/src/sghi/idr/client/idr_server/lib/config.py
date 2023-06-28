from typing import Final, TypedDict

from sghi.idr.client.core.lib.config import (
    ImproperlyConfiguredError,
    SettingInitializer,
)

# =============================================================================
# TYPES
# =============================================================================


class _IDRServerSettingsMapping(TypedDict, total=True):
    host: str
    username: str
    password: str


# =============================================================================
# CONSTANTS
# =============================================================================

_IDR_SERVER_SETTINGS_CONFIG_KEY: Final[str] = "IDR_SERVER_SETTINGS"


# =============================================================================
# SETTINGS INITIALIZERS
# =============================================================================


class IDRServerSettingsInitializer(SettingInitializer):
    """:class:`SettingInitializer` to load IDR Server settings."""

    @property
    def has_secrets(self) -> bool:
        return True

    @property
    def setting(self) -> str:
        return _IDR_SERVER_SETTINGS_CONFIG_KEY

    def execute(
        self,
        an_input: _IDRServerSettingsMapping | None,
    ) -> _IDRServerSettingsMapping:
        match an_input:
            case None:
                _err_message: str = (
                    'Required setting "{}" not provided. This setting is '
                    "needed to work with the IDR Server.".format(
                        _IDR_SERVER_SETTINGS_CONFIG_KEY,
                    )
                )
                raise ImproperlyConfiguredError(message=_err_message)
            case {"host": host, "password": _, "username": _} if not host:
                _err_message: str = 'IDR Server "host" cannot be empty.'
                raise ImproperlyConfiguredError(message=_err_message)
            case {"host": _, "password": _, "username": _}:
                return an_input
            case _:
                _err_message: str = (
                    "The setting is not a valid IDR Server setting. Ensure "
                    "the setting is a mapping with the host, password and "
                    "username entries."
                )
                raise ImproperlyConfiguredError(message=_err_message)
