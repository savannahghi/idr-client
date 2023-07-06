import logging
from collections.abc import Mapping
from logging.config import dictConfig
from typing import Any

import sghi.idr.client.core as app
from sghi.idr.client.core.lib import SettingInitializer

from .constants import DEFAULT_CONFIG, LOGGING_CONFIG_KEY


class LoggingInitializer(SettingInitializer):
    """:class:`SettingInitializer` that configures logging for the app."""

    @property
    def setting(self) -> str:
        return LOGGING_CONFIG_KEY

    def execute(self, an_input: Mapping[str, Any] | None) -> Mapping[str, Any]:
        logging_config: dict[str, Any] = dict(
            an_input or DEFAULT_CONFIG[self.setting],
        )
        dictConfig(logging_config)
        logging.getLogger("sghi.idr.client").setLevel(app.registry.log_level)
        return logging_config
