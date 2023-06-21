from typing import Any, Final

APP_DISPATCHER_REG_KEY: Final[str] = "runtime.app_dispatcher"

APP_VERBOSITY_REG_KEY: Final[str] = "runtime.verbosity"

ETL_PROTOCOLS_CONFIG_KEY: Final[str] = "ETL_PROTOCOLS"

LOGGING_CONFIG_KEY: Final[str] = "LOGGING"

SETTINGS_INITIALIZERS_CONFIG_KEY: Final[str] = "SETTINGS_INITIALIZERS"

DEFAULT_CONFIG: Final[dict[str, Any]] = {
    ETL_PROTOCOLS_CONFIG_KEY: [],
    LOGGING_CONFIG_KEY: {
        "version": 1,
        "formatters": {
            "simple": {
                "format": "%(asctime)s %(levelname)s %(name)s - %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
                "level": "DEBUG",
            },
        },
        "loggers": {
            "app": {"level": "INFO", "handlers": ["console"]},
        },
    },
    SETTINGS_INITIALIZERS_CONFIG_KEY: [],
}
