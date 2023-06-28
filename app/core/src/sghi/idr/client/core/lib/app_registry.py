import logging
from collections.abc import Mapping
from typing import Any

from sghi.idr.client.core.domain import ETLProtocol

from .checkers import ensure_not_none

# =============================================================================
# TYPES
# =============================================================================

_LogLevel = int | str


# =============================================================================
# APP REGISTRY
# =============================================================================


class AppRegistry:
    """Application registry.

    This class provides lookup functionality for important resources and
    services at runtime as well as a means to change the values for these
    resources at runtime.

    At runtime, an instance of this class can be accessed using the
    :attr:`app.registry` property.
    """

    def __init__(self):
        super().__init__()
        self._etl_protocols: dict[str, ETLProtocol] = {}
        self._log_level: _LogLevel = logging.NOTSET
        self._items: dict[str, Any] = {}

    @property
    def etl_protocols(self) -> Mapping[str, ETLProtocol]:
        return self._etl_protocols

    @etl_protocols.setter
    def etl_protocols(
        self,
        etl_protocols: Mapping[str, ETLProtocol],
    ) -> None:
        self._etl_protocols = dict(
            ensure_not_none(
                etl_protocols,
                message='"etl_protocols" must not be None.',
            ),
        )

    @property
    def log_level(self) -> _LogLevel:
        return self._log_level

    @log_level.setter
    def log_level(self, log_level: _LogLevel) -> None:
        self._log_level = ensure_not_none(
            log_level,
            message='"log_level" must not be None.',
        )
        logging.getLogger("sghi.idr.client").setLevel(self._log_level)

    def get(self, key: str, default: Any = None) -> Any:  # noqa: ANN401
        return self._items.get(key, default)

    def set(self, key: str, value: Any) -> None:  # noqa: A003, ANN401
        self._items[key] = value
