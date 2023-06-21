import logging
from collections.abc import Mapping, Sequence
from logging.config import dictConfig
from typing import Any

import app
from app.lib import (
    ImproperlyConfiguredError,
    SettingInitializer,
    import_string,
)

from .constants import (
    DEFAULT_CONFIG,
    ETL_PROTOCOLS_CONFIG_KEY,
    LOGGING_CONFIG_KEY,
)
from .typings import ETLProtocol_Factory


class ETLProtocolInitializer(SettingInitializer):
    """
    :class:`SettingInitializer` that loads :class:`ETLProtocol` factories for
    later instantiation.
    """

    @property
    def setting(self) -> str:
        return ETL_PROTOCOLS_CONFIG_KEY

    def execute(
        self,
        an_input: Sequence[str],
    ) -> Sequence[ETLProtocol_Factory]:
        etl_protocols: Sequence[ETLProtocol_Factory] = list(
            map(self._dotted_path_to_etl_protocol_factory, an_input),
        )
        return etl_protocols

    @staticmethod
    def _dotted_path_to_etl_protocol_factory(
        etl_protocol_dotted_path: str,
    ) -> ETLProtocol_Factory:
        try:
            etl_protocol_factory: ETLProtocol_Factory
            etl_protocol_factory = import_string(  # type: ignore
                etl_protocol_dotted_path,
            )
            return etl_protocol_factory
        except ImportError as exp:
            _err_msg: str = '"{}" does not seem to be a valid path.'.format(
                etl_protocol_dotted_path,
            )
            raise ImproperlyConfiguredError(message=_err_msg) from exp


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
        logging.getLogger("app").setLevel(app.registry.log_level)
        return logging_config
