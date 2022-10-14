from collections.abc import Mapping
from typing import Callable, Optional

from app.core import DataSourceType, Transport

from .config import ImproperlyConfiguredError

# =============================================================================
# TYPES
# =============================================================================

DefaultTransportFactory = Callable[[], Transport]


# =============================================================================
# APP REGISTRY
# =============================================================================


class AppRegistry:
    """
    This class provides lookup functionality to important resources and
    services needed within the app. At runtime, an instance of this class can
    be accessed at `app.registry`.
    """

    def __init__(self):
        self._data_source_types: dict[str, DataSourceType] = dict()
        self._default_transport_factory: Optional[
            DefaultTransportFactory
        ] = None

    @property
    def data_source_types(self) -> Mapping[str, DataSourceType]:
        """
        Return a readonly mapping of the data source types supported by the
        app.

        :return: A readonly mapping of the data source types supported by the
            app.
        """
        return self._data_source_types

    @data_source_types.setter
    def data_source_types(
        self, data_source_types: Mapping[str, DataSourceType]
    ) -> None:
        """Set the data sources supported by the app.

        :param data_source_types: A readonly mapping of the data source types
            supported by the app.

        :return: None.
        """
        self._data_source_types = dict(**data_source_types)

    @property
    def default_transport_factory(self) -> Optional[DefaultTransportFactory]:
        """Return the default transport factory for the app if set.

        :return: The default transport factory for the app if set or ``None``
            otherwise.
        """
        return self._default_transport_factory

    @default_transport_factory.setter
    def default_transport_factory(
        self, transport_factory: DefaultTransportFactory
    ) -> None:
        """Set the default transport factory for the app.

        :param transport_factory: The transport factory to set as the default
            for the app.

        :return: None.
        """
        self._default_transport_factory = transport_factory

    def get_default_transport_factory_or_raise(
        self, error_message: Optional[str] = None
    ) -> DefaultTransportFactory:
        """
        Returns the default transport factory if set or raise an
        :class:`ImproperlyConfiguredError` otherwise. An optional error message
        can be provided to be used as the exception message.

        :param error_message: An optional error message to be used as the
            exception message.

        :return: The default transport factory for the app.

        :raise ImproperlyConfiguredError: If the default transport factory for
            the app has not been set.
        """
        if not self.default_transport_factory:
            raise ImproperlyConfiguredError(
                message=error_message
                or ("The default transport factor has not been set.")
            )
        return self.default_transport_factory
