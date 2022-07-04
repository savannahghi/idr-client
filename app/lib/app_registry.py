from typing import Dict, Mapping

from app.core import DataSourceType


class AppRegistry:
    """
    This class provides lookup functionality to important resources and
    services needed within the app. At runtime, an instance of this class can
    be accessed at `app.registry`.
    """

    def __init__(self):
        self._data_source_types: Dict[str, DataSourceType] = dict()

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
