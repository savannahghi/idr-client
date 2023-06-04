from collections.abc import Callable

from app.core_v1.domain import ETLProtocol

ETLProtocol_Factory = Callable[[], ETLProtocol]
