from collections.abc import Callable

from app.core.domain import ETLProtocol

ETLProtocol_Factory = Callable[[], ETLProtocol]
