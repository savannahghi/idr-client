from collections.abc import Callable

from sghi.idr.client.core.domain import ETLProtocol

ETLProtocol_Factory = Callable[[], ETLProtocol]
