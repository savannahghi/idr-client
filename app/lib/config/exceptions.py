from typing import Optional

from app.core import IDRClientException


class MissingSettingError(IDRClientException, LookupError):
    """Non existing setting access error."""

    def __init__(self, setting: str, message: Optional[str] = None):
        """Initialize a ``MissingSettingError`` with the given properties.

        :param setting: The missing setting.
        :param message: An optional message for the resulting exception. If
            none is provided, then a generic one is automatically generated.
        """
        self._setting: str = setting
        self._message: str = (
            message or 'Setting "%s" does not exist.' % self._setting
        )
        IDRClientException.__init__(self, message=self._message)

    @property
    def setting(self) -> str:
        """
        Return the missing setting that resulted in this exception being
        raised.

        :return: The missing setting.
        """
        return self._setting
