from typing import Any, Dict


def config_factory() -> Dict[str, Any]:
    """
    A factory that returns a configuration object that can be used for testing.

    :return: A configuration dictionary that can be used for testing.
    """
    return {
        "DEFAULT_TRANSPORT_FACTORY": (
            "tests.core.factories.FakeTransportFactory"
        ),
        "SETTINGS_INITIALIZERS": [
            "tests.test_app.FakeDataSourceTypesConfigInitializer"
        ],
        "SUPPORTED_DATA_SOURCE_TYPES": ["app.imp.sql_data.SQLDataSourceType"],
    }
