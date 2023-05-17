from app.core import IDRClientException


class ConfigurationError(IDRClientException):
    """Indicates a generic configuration error occurred."""

    def __init__(self, message: str | None = None):
        self._message: str = message or (
            "An unknown error occurred while configuring the app."
        )
        super().__init__(message=self._message)


class ImproperlyConfiguredError(ConfigurationError):
    """Indicates that a configuration was found, but it is invalid."""


class MissingSettingError(ConfigurationError, LookupError):
    """Non-existing setting access error."""

    def __init__(self, setting: str, message: str | None = None):
        """Initialize a ``MissingSettingError`` with the given properties.

        :param setting: The missing setting.
        :param message: An optional message for the resulting exception. If
            none is provided, then a generic one is automatically generated.
        """
        self._setting: str = setting
        self._message: str = (
            message or 'Setting "%s" does not exist.' % self._setting
        )
        ConfigurationError.__init__(self, message=self._message)

    @property
    def setting(self) -> str:
        """Return the missing setting whose attempted access resulted in this
        exception being raised.

        :return: The missing setting.
        """
        return self._setting
