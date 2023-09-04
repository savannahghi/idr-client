"""
``Config`` interface definition, implementing classes and helpers.
"""
from __future__ import annotations

import logging
from abc import ABCMeta, abstractmethod
from logging import Logger
from typing import TYPE_CHECKING, Any, Never, final

from ..exceptions import SGHIError
from ..tasks import Pipe, Task
from ..utils import type_fqn

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


# =============================================================================
# EXCEPTIONS
# =============================================================================


class ConfigurationError(SGHIError):
    """Indicates a generic configuration error occurred."""

    def __init__(self, message: str | None = None):
        _message: str = message or (
            "An unknown error occurred while configuring the app."
        )
        super().__init__(message=_message)


class ImproperlyConfiguredError(ConfigurationError):
    """Indicates that a configuration was found, but it is invalid."""


class NoSuchSettingError(ConfigurationError, LookupError):
    """Non-existent setting access error."""

    def __init__(self, setting: str, message: str | None = None) -> None:
        """Initialize a ``NoSuchSettingError`` with the given properties.

        :param setting: The missing setting.
        :param message: An optional message for the resulting exception. If
            none is provided, then a generic one is automatically generated.
        """
        self._setting: str = setting
        _message: str = (
            message or "Setting '%s' does not exist." % self._setting
        )
        ConfigurationError.__init__(self, message=_message)

    @property
    def setting(self) -> str:
        """
        Return the missing setting whose attempted access resulted in this
        exception being raised.

        :return: The missing setting.
        """
        return self._setting


class NotSetupError(ConfigurationError):
    """
    Indicates that the application/tool is yet to be setup/initialized.

    Applications can be setup by calling the :meth:`sghi.app.setup` function or
    equivalent. Check the application documentation for more details.
    """

    def __init__(self, message: str | None = None):
        _message: str = message or (
            "Application/tool not set up. Please call the 'sghi.app.setup()' "
            "function(or equivalent) of the application before proceeding."
        )
        super().__init__(message=_message)


# =============================================================================
# SETTING INITIALIZER INTERFACE
# =============================================================================


class SettingInitializer(Task[Any, Any], metaclass=ABCMeta):
    """
    This interface represents a tasks used to perform some initialization
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


# =============================================================================
# CONFIG INTERFACE
# =============================================================================


class Config(metaclass=ABCMeta):
    """An object that holds the application settings.

    Only read-only access to the settings is available post initialization. Any
    required modifications to the settings should be done at initialization
    time by passing a sequence of
    :class:`initializers<.setting_initializer.SettingInitializer>` to this
    class's :func:`of` factory method. Uppercase names for settings should be
    preferred to convey that they are read-only.

    Setting names that are also valid python identifiers can be accessed using
    the dot notation on an instance of this class. The :meth:`get` method can
    also be used to access settings after initialization and is especially
    useful for access to settings with names that are invalid python
    identifies.

    .. tip::

        Unless otherwise indicated, at runtime, there should be an instance of
        this class at :attr:`sghi.app.conf` ment to hold the main
        configuration settings for the executing application/tool.

    .. admonition:: Info: Regarding ``Config`` immutability

        This interface was intentionally designed with immutability in mind.
        The rationale behind this choice stems from the fact that, once loaded,
        configuration should rarely change if ever. This has a couple of
        benefits, chief among them being:

            - It makes it easy to reason about the application .i.e. you don't
              have to worry about the "current" configuration in use going
              stale.
            - It makes accessing and using the configuration safe in concurrent
              contexts.

        Nonetheless, making the configuration immutable also comes with some
        challenges. In most cases, configuration comes from the user inputs or
        external sources linked to the application. This necessitates a
        "loading" process from an origin, such as a disk. This typically
        happens during application setup or initiation phase. As such, there
        exists a (short) period between when the application starts and when
        the setup is concluded. During this phase, the application may not yet
        have a "valid" configuration.

        To account for such scenarios, there exists an implementation of this
        interface whose instances raises a :exc:`~.exceptions.NotSetupError`
        whenever an attempt to access their settings is made. These instances
        function as the default placeholders for applications that have not
        undergone or are yet to complete the setup process. They can be created
        using the :func:`of_awaiting_setup` factory.
    """

    __slots__ = ()

    @abstractmethod
    def __getattr__(self, setting: str) -> Any:  # noqa: ANN401
        """Make settings available using the dot operator.

        :param setting: The name of the setting value to retrieve.

        :raises NoSuchSettingError: If the setting is not present.

        :return: The value of the given setting if it is present in this
            config.
        """
        raise NotImplementedError

    @abstractmethod
    def get(self, setting: str, default: Any = None) -> Any:  # noqa: ANN401
        """
        Retrieve the value of the given setting or return the given default if
        no such setting exists in this ``Config`` instance.

        This method can
        also be used for retrieval of settings with invalid python identifier
        names.

        :param setting: The name of the setting value to retrieve.
        :param default: A value to return when no setting with the given name
            exists in this config.

        :return: The value of the given setting if it is present in this config
            or the given default otherwise.
        """
        raise NotImplementedError

    @staticmethod
    def of(
        settings: Mapping[str, Any],
        settings_initializers: Sequence[SettingInitializer] | None = None,
    ) -> Config:
        """Create a new :class:`Config` instance.

        The settings to use are passed as a mapping with the setting names as
        the keys and the setting values as the values of the mapping.

        Optional initializers can also be passed to the factory to perform
        additional initialization tasks such as set up of addition components
        or validating that required settings were provided, etc. Initializers
        can also be used to remap settings values to more appropriate runtime
        values by taking a raw setting value and returning the desired or
        appropriate value. The value is then set as the new value of the
        setting and will remain that way for the duration of the runtime of the
        app. If multiple initializers are given for the same setting, they are
        executed in the encounter order with the output of the previous
        initializer becoming the input of the next initializer. The output of
        the last initializer is then set as the final value of the setting.

        :param settings: The configurations/settings to use as a mapping.
        :param settings_initializers: Optional initializers to perform
            post-initialization tasks.

        :return: A `Config` instance.
        """
        return _ConfigImp(settings, settings_initializers)

    @staticmethod
    def of_awaiting_setup(err_msg: str | None = None) -> Config:
        """
        Create a new :class:`Config` instance to represent an application that
        is not yet set up.

        Any attempt to access settings from the returned
        instance will result in a ``NotSetupError`` being raised indicating to
        the user/caller that the application is yet to be setup.

        .. tip::

            Applications can be setup by calling the :func:`sghi.app.setup`
            function or equivalent. Check the application documentation for
            more details.

        :param err_msg: Optional custom error message to be displayed when
            accessing settings from the returned instance.

        :return: A new `Config` instance.
        """
        return _NotSetup(err_msg=err_msg)


# =============================================================================
# CONFIG IMPLEMENTATIONS
# =============================================================================


@final
class _ConfigImp(Config):
    """A simple concrete implementation of the :class:`Config` interface."""

    __slots__ = ("_settings", "_initializers", "_logger")

    def __init__(
            self,
            settings: Mapping[str, Any],
            settings_initializers: Sequence[SettingInitializer] | None = None,
    ):
        """Initialize a new :class:`Config` instance.

        The settings to use are passed as a mapping with the setting names as
        the keys and the setting values as the values of the mapping.

        Optional initializers can also be passed to the constructor to perform
        additional initialization tasks such as set up of addition components
        or validating that required settings were provided, etc. Initializers
        can also be used to remap settings values to more appropriate runtime
        values by taking a raw setting value and return the desired or
        appropriate value. The value is then set as the new value of the
        setting and will remain that way for the duration of the runtime of the
        app. If multiple initializers are given for the same setting, they are
        executed in the encounter order with the output of the previous
        initializer becoming the input of the next initializer. The output of
        the last initializer is then set as the final value of the setting.

        :param settings: The configurations/settings to use as a mapping.
        :param settings_initializers: Optional initializers to perform
            post-initialization tasks.
        """
        self._settings: dict[str, Any] = dict(settings or {})
        self._initializers: Mapping[
            str,
            Sequence[SettingInitializer],
        ] = self._group_related_initializers(settings_initializers or ())
        self._logger: Logger = logging.getLogger(type_fqn(self.__class__))
        self._run_initializers()

    def __getattr__(self, setting: str) -> Any:  # noqa: ANN401
        """Make settings available using the dot operator."""
        try:
            return self._settings[setting]
        except KeyError:
            raise NoSuchSettingError(setting=setting) from None

    def get(self, setting: str, default: Any = None) -> Any:  # noqa: ANN401
        """
        Retrieve the value of the given setting or return the given default
        if no such setting exists in this ``Config`` instance.

        This method can also be used for retrieval of settings with invalid
        Python identifier names.

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
        setting or ``None`` if the setting is not present.

        The return value of the initializer is set as the new value if the
        setting.
        This way, initializers can also be used to set default settings if
        they aren't already present.

        :return: None.
        """
        for _setting, _initializers in self._initializers.items():
            raw_setting_val: Any = self._settings.get(_setting)
            initializer_pipeline: Pipe = Pipe(*_initializers)
            setting_val: Any = initializer_pipeline(raw_setting_val)
            if self._logger.isEnabledFor(logging.DEBUG):
                self._logger.debug(
                    "Ran initializer for the setting '%s' with raw value '%s'.",  # noqa  :E502
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
        """Group the given initializers based on the setting they belong to.

        :param initializers: The list of initializers to group.
        :return: A dictionary containing the grouped initializers, where the
            keys are setting names, and the values are sequences of
            corresponding initializers.
        """
        grouped_initializers: dict[str, list[SettingInitializer]] = {}
        for _initializer in initializers:
            grouped_initializers.setdefault(_initializer.setting, []).append(
                _initializer,
            )
        return grouped_initializers


@final
class _NotSetup(Config):
    """A representation of an application that is not yet set up."""

    __slots__ = ("_err_msg",)

    def __init__(self, err_msg: str | None = None):
        """Initialize a new `_NotSetup` instance.

        :param err_msg: Optional custom error message to be displayed when
            accessing any setting.

        :return: None.
        """
        self._err_msg: str | None = err_msg

    def __getattr__(self, setting: str) -> Any:  # noqa: ANN401
        """Raise a `NotSetupError` when trying to access any setting.

        :param setting: The name of the setting value to retrieve.

        :raises NotSetupError: Always raises the `NotSetupError`.

        :return: This method does not return a value; it raises an exception.
        """
        self._raise(err_msg=self._err_msg)

    def get(self, setting: str, default: Any = None) -> Any:  # noqa: ANN401
        """Raise a `NotSetupError` when trying to access any setting.

        :param setting: The name of the setting value to retrieve.
        :param default: A value to return when no setting with the given name
            exists in this config.

        :raises NotSetupError: Always raises the `NotSetupError`.

        :return: This method does not return a value; it raises an exception.
        """
        self._raise(err_msg=self._err_msg)

    @staticmethod
    def _raise(err_msg: str | None) -> Never:
        """Raise a `NotSetupError` with the specified error message.

        :param err_msg: An optional error message to be displayed in the
            exception.

        :raises NotSetupError: Always raises the `NotSetupError` with the
            specified error message.

        :return: This method does not return a value; it raises an exception.
        """
        raise NotSetupError(message=err_msg)


# =============================================================================
# MODULE EXPORTS
# =============================================================================


__all__ = [
    "Config",
    "ConfigurationError",
    "ImproperlyConfiguredError",
    "NoSuchSettingError",
    "NotSetupError",
    "SettingInitializer",
]
