from typing import Any


def config_factory() -> dict[str, Any]:
    """
    A factory that returns a configuration object that can be used for testing.

    :return: A configuration dictionary that can be used for testing.
    """
    return {
        "DEFAULT_TRANSPORT_FACTORY": (
            "tests.core.factories.FakeTransportFactory"
        ),
        "RETRY": {
            "enable_retries": False,
            "default_maximum_delay": 10.0,  # 10 seconds
        },
        "SETTINGS_INITIALIZERS": [
            "tests.test_app.FakeDataSourceTypesConfigInitializer",
        ],
        "SUPPORTED_DATA_SOURCE_TYPES": ["app.imp.sql_data.SQLDataSourceType"],
    }
